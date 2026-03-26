package com.degging.be.user.service;

import com.degging.be.auth.dto.request.ResetPasswordRequest;
import com.degging.be.auth.dto.request.SignupRequest;
import com.degging.be.auth.service.VerificationService;
import com.degging.be.cafe.repository.VibeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.global.util.ImageUtils;
import com.degging.be.infra.storage.s3.ImageService;
import com.degging.be.infra.storage.s3.ImageUploadResult;
import com.degging.be.user.dto.request.UserUpdateRequest;
import com.degging.be.user.dto.response.UserDetailResponse;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserProfileEntity;
import com.degging.be.user.entity.mongodb.UserOnboarding;
import com.degging.be.user.repository.UserProfileRepository;
import com.degging.be.user.repository.UserRepository;
import com.degging.be.user.repository.mongodb.UserOnboardingRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import com.degging.be.infra.cache.redis.RedisService;

import java.io.IOException;
import java.security.SecureRandom;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * 회원가입, 닉네임 중복 검사, 비밀번호 찾기 및 재설정 관리 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MemberService {

    private final UserRepository userRepository;
    private final VerificationService verificationService;
    private final PasswordEncoder passwordEncoder;
    private final UserOnboardingRepository userOnboardingRepository;
    private final VibeRepository vibeRepository;
    private final UserProfileRepository userProfileRepository;
    private final ImageService imageService;
    private final RedisService redisService;

    // 랜덤 생성기
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    // 임시 비밀번호 생성용 문자셋
    private static final String CHAR_SET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

    /**
     * 회원가입
     *
     * 이메일 인증 여부를 확인, 이메일 및 닉네임 중복 시 예외를 발생
     *
     * @param request 회원가입 요청 DTO
     * @throws BaseException 이메일 미인증, 이메일 중복, 닉네임 중복 시 발생
     */
    @Transactional
    public UUID register(SignupRequest request) {

        // 회원가입 데이터 유효성 검증
        validateSignupRequest(request);

        // A/B 테스트 그룹 배정
        Character group = getLesserGroup();

        // 비밀번호 암호화 후 엔티티 생성
        UserEntity user = UserEntity.builder()
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .abGroup(group)
                .build();

        // 닉네임, 성별, 생년월일 정보를 UserProfileEntity로 생성하여 UserEntity에 매핑
        UserProfileEntity userProfile = UserProfileEntity.builder()
                .nickname(request.getNickname())
                .gender(request.getGender())
                .birthDate(request.getBirthDate())
                .build();
        user.setProfile(userProfile);

        userRepository.save(user);

        // 가입 완료 후 Redis의 인증 성공 플래그 제거
        verificationService.removeVerifiedFlag(request.getEmail());

        return user.getUserId();
    }

    /**
     * A/B 중 더 적은 그룹을 반환하는 메서드
     */
    public Character getLesserGroup(){
        // 현재 회원의 비율을 조회하여 1:1 에 가깝도록 A/B 테스트 그룹 랜덤 배정
        long countA = userRepository.countByAbGroup('A');
        long countB = userRepository.countByAbGroup('B');
        long total = countA + countB;

        if (total == 0) return Math.random() < 0.5 ? 'A' : 'B';

        // A의 비율이 높을수록 B가 선택될 확률이 커짐
        // 예: A가 60명, B가 40명이면 B가 선택될 확률은 60%
        double probabilityA = 1.0 - ((double) countA / total);

        return Math.random() < probabilityA ? 'A' : 'B';
    }

    /**
     * 특정 회원 정보를 조회하는 메서드
     */
    // 이 메서드에서는 기존 트랜잭션을 잠시 중단하고 실행함 (MongoDB 에러 방지)
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public UserDetailResponse getUserDetail(UUID userId){
        // 유효성 검사
        UserEntity entity = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 프로필 조회
        UserProfileEntity profileEntity = userProfileRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 회원 취향 태그 조회 (MongoDB + PostgreSQL 조회)
        List<String> tags = getUserPreferred(userId);

        // password 를 제외하고 dto 로 변환하여 응답
        return UserDetailResponse.of(entity, profileEntity, tags);
    }

    /**
     * 취향 태그 매핑 후 반환하는 메서드
     *
     * MongoDB 에서 회원 취향 태그 UUID 를 조회하여 Top3 를 뽑아
     * 해당 UUID 에 맞는 tagName 을 조회해 반환함
     */
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public List<String> getUserPreferred(UUID userId){
        // 1. MongoDB에서 영구 취향 태그 조회 (Top 3)
        List<String> permanentTags = getPermanentPreferredTags(userId);

        // 2. Redis에서 일회성(임시) 취향 태그 조회
        List<String> temporaryTags = redisService.getListValues("user:preference:temp:" + userId);

        // 3. 두 리스트 병합 (중복 제거 및 순서 유지)
        Set<String> mergedTags = new LinkedHashSet<>(permanentTags);
        if (temporaryTags != null) {
            mergedTags.addAll(temporaryTags);
        }

        return new ArrayList<>(mergedTags);
    }

    /**
     * MongoDB에서 상위 3개의 영구 취향 태그를 조회합니다.
     */
    private List<String> getPermanentPreferredTags(UUID userId) {
        UserOnboarding onboardingData = userOnboardingRepository.findByUserId(userId.toString())
                .orElse(null);
        log.info("회원 취향 태그 DB 로드 결과: {}", onboardingData);

        if (onboardingData == null || onboardingData.getPreferredTags() == null || onboardingData.getPreferredTags().isEmpty()) {
            return Collections.emptyList();
        }

        // 취향 태그들 가져와서 (Map<String, Integer> 형식)
        Map<String, Integer> tags = onboardingData.getPreferredTags();
        log.info("취향 태그 내용: {}", tags);

        // 상위 3개의 태그 조회 (가중치 순)
        List<UUID> top3 = tags.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(3)
                .map(entry -> UUID.fromString(entry.getKey()))
                .toList();

        if (top3.isEmpty()) {
            return Collections.emptyList();
        }

        List<String> tagNames = vibeRepository.findTagNameByTagIds(top3);
        return (tagNames != null) ? tagNames : Collections.emptyList();
    }

    /**
     * 임시 취향 태그를 Redis에 저장하는 메서드
     * @param userId 유저 식별자
     * @param tags 추가로 선택한 태그 리스트
     */
    public void saveTemporaryTags(UUID userId, List<String> tags) {
        // Redis에 24시간 동안 저장
        redisService.setValues("user:preference:temp:" + userId, tags, 24, TimeUnit.HOURS);
        log.info("[Redis] 임시 취향 태그 저장 완료 - UserId: {}, Tags: {}", userId, tags);
    }

    /**
     * 회원 정보를 수정하는 메서드
     */
    @Transactional
    public void updateUser(UUID userId, UserUpdateRequest request){
        UserEntity entity = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 현재 닉네임과 요청받은 닉네임이 다를 때만 중복 검사 실행
        if (!entity.getProfile().getNickname().equals(request.getNickname())) {
            checkNicknameDuplication(request.getNickname());
        }

        String originalUrl = entity.getProfile().getProfileImageUrl();
        String newProfileImageUrl = originalUrl;

        // 이미지 처리 분기
        // 기본 이미지로 지정하기로 한 경우
        if (request.isDefaultImage()) {
            // [CASE 1] 기본 이미지로 변경 -> 무조건 null
            newProfileImageUrl = null;
            if (originalUrl != null && !originalUrl.isBlank()) {
                imageService.deleteImage(originalUrl);
                log.info("[S3] 기존 이미지 삭제 성공: {}", originalUrl);
            }
        } else if (request.getProfileImage() != null && !request.getProfileImage().isEmpty()) {
            // [CASE 2] 새 이미지 업로드
            if (originalUrl != null && !originalUrl.isBlank()) {
                imageService.deleteImage(originalUrl);
                log.info("[S3] 교체 전 기존 이미지 삭제: {}", originalUrl);
            }
            newProfileImageUrl = uploadReviewImages(request.getProfileImage());
        } else {
            // [CASE 3] 변경 없음 -> 만약 기존 데이터가 ""라면 여기서 null로 정제
            if (originalUrl != null && originalUrl.isBlank()) {
                newProfileImageUrl = null;
            }
        }

        // 3. 더티 체킹으로 업데이트
        entity.getProfile().updateUser(request.getNickname(), newProfileImageUrl);
    }

    // 회원 이미지 업로드 후 링크 반환 메서드
    public String uploadReviewImages(MultipartFile image){
        if (image == null) return null;

        try {
            // 리사이징한 이미지를 S3 업로드 후 KeyPath 반환 받아 DB에 저장
            // 유저 프로필 이미지 생성 (200px) 및 업로드
            log.info("이미지 리사이징 시작: {}", image.getOriginalFilename());
            MultipartFile thumbnail = ImageUtils.resizeImage(image, 200);

            // S3 업로드
            ImageUploadResult thumbResult = imageService.uploadImage(thumbnail, "user/profile");
            log.info("이미지 업로드 성공: {}", thumbResult.storedName());

            return thumbResult.storedName();
        } catch (IOException e){
            // 파일 읽기/쓰기 실패 시 처리
            log.error("이미지 리사이징 중 입출력 오류 발생: {}", e.getMessage(), e);
            throw new BaseException(UserErrorCode.PROFILE_IMAGE_UPLOAD_FAILED);
        }
    }


    /**
     * 특정 회원을 삭제하는 메서드
     */
    @Transactional
    public void removeUser(UUID userId){
        // 유효성 검사
        UserEntity user = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 유저 삭제
        userRepository.delete(user);
    }

    /**
     * 회원가입 데이터 통합 검증
     *
     * @param request 가입 요청 정보
     */
    private void validateSignupRequest(SignupRequest request) {
        checkEmailVerification(request.getEmail());
        checkEmailDuplication(request.getEmail());
        checkNicknameDuplication(request.getNickname());
    }

    /**
     * 이메일 인증 완료 상태 확인
     *
     * @param email 검증할 이메일
     * @throws BaseException 이메일 인증이 완료되지 않았을 경우 발생
     */
    public void checkEmailVerification(String email) {
        if (!verificationService.isVerified(email)) {
            throw new BaseException(AuthErrorCode.EMAIL_NOT_VERIFIED);
        }
    }

    /**
     * 이메일 중복 여부 확인
     *
     * @param email 검사할 이메일
     * @throws BaseException 이미 존재하는 이메일일 경우 발생
     */
    public void checkEmailDuplication(String email) {
        if (userRepository.existsByEmail(email)) {
            throw new BaseException(AuthErrorCode.EMAIL_DUPLICATE);
        }
    }

    /**
     * 닉네임 중복 여부 확인
     *
     * @param nickname 검사할 닉네임
     * @throws BaseException 이미 존재하는 닉네임일 경우 발생
     */
    public void checkNicknameDuplication(String nickname) {
        if (userProfileRepository.existsByNickname(nickname)) {
            throw new BaseException(UserErrorCode.NICKNAME_DUPLICATE);
        }
    }

    /**
     * 임시 비밀번호 발급하고 이메일 전송
     *
     * @param email 비밀번호를 찾고자 하는 사용자의 이메일
     * @throws BaseException 존재하지 않는 사용자일 경우 발생
     */
    @Transactional
    public void findPassword(String email) {
        // 사용자 정보 조회
        UserEntity user = userRepository.findByEmail(email)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 임시 비밀번호 생성 및 암호화 반영
        String tempPassword = generateTempPassword();
        user.updatePassword(passwordEncoder.encode(tempPassword));

        // 메일 발송
        verificationService.sendTempPassword(email, tempPassword);
    }

    /**
     * 사용자 비밀번호 변경
     *
     * @param userId 사용자 UUID
     * @param request 비밀번호 재설정 요청 DTO
     * @throws BaseException 기존 비밀번호 불일치, 새 비밀번호 불일치, 이전과 동일한 비밀번호일 경우 발생
     */
    @Transactional
    public void resetPassword(UUID userId, ResetPasswordRequest request) {
        // 사용자 정보 조회
        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 현재 비밀번호 일치 확인
        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BaseException(UserErrorCode.PASSWORD_WRONG);
        }

        // 새 비밀번호와 확인용 비밀번호 일치 확인
        if (!request.getNewPassword().equals(request.getConfirmPassword())) {
            throw new BaseException(UserErrorCode.PASSWORD_MISMATCH);
        }

        // 기존 비밀번호와 새 비밀번호 동일 여부 확인
        if (request.getOldPassword().equals(request.getNewPassword())) {
            throw new BaseException(UserErrorCode.SAME_AS_OLD_PASSWORD);
        }

        user.updatePassword(passwordEncoder.encode(request.getNewPassword()));
    }

    /**
     * 임시 비밀번호용 랜덤 문자열 생성
     *
     * @return 10자리의 영문 대소문자 및 숫자 조합
     */
    private String generateTempPassword() {
        StringBuilder sb = new StringBuilder(10);
        for (int i = 0; i < 10; i++) {
            sb.append(CHAR_SET.charAt(SECURE_RANDOM.nextInt(CHAR_SET.length())));
        }
        return sb.toString();
    }
}
