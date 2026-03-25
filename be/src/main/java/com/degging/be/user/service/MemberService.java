package com.degging.be.user.service;

import com.degging.be.auth.dto.request.ResetPasswordRequest;
import com.degging.be.auth.dto.request.SignupRequest;
import com.degging.be.auth.service.VerificationService;
import com.degging.be.cafe.repository.VibeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.user.dto.request.UserUpdateRequest;
import com.degging.be.user.dto.response.UserDetailResponse;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserProfileEntity;
import com.degging.be.user.entity.mongodb.UserOnboarding;
import com.degging.be.user.repository.UserProfileRepository;
import com.degging.be.user.repository.UserRepository;
import com.degging.be.user.repository.mongodb.UserOnboardingRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 회원가입, 닉네임 중복 검사, 비밀번호 찾기 및 재설정 관리 클래스
 */
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

        // 회원 취향 태그 조회 (MongoDB + PostgreSQL 조회)
        List<String> tags = getUserPreferred(userId);

        // password 를 제외하고 dto 로 변환하여 응답
        return UserDetailResponse.of(entity, tags);
    }

    /**
     * 취향 태그 매핑 후 반환하는 메서드

     * MongoDB 에서 회원 취향 태그 UUID 를 조회하여 Top3 를 뽑아
     * 해당 UUID 에 맞는 tagName 을 조회해 반환함
     */
    public List<String> getUserPreferred(UUID userId){
        // 회원 취향 태그 조회 (없을 경우 온보딩 미실행을 고려하여 null 값으로 초기화)
        UserOnboarding onboardingData = userOnboardingRepository.findByUserId(userId)
                .orElse(null);

        // 온보딩 데이터 자체가 없거나, 있더라도 태그 Map이 비어있으면 빈 리스트 반환
        if (onboardingData == null || onboardingData.getPreferredTags() == null || onboardingData.getPreferredTags().isEmpty()) {
            return Collections.emptyList(); // [] 반환
        }

        // 취향 태그들 가져와서
        Map<UUID, Integer> tags = onboardingData.getPreferredTags();

        // 상위 3개의 태그 조회
        List<UUID> top3 = tags.entrySet().stream()
                .sorted(Map.Entry.<UUID, Integer>comparingByValue().reversed()) // 내림차
                .limit(3) // 3개만
                .map(Map.Entry::getKey) // 상위 3개의 UUID 를 가져옴
                .toList();

        // top3가 비어있을 경우 빈 리스트 반환
        if (top3.isEmpty()) {
            return Collections.emptyList();
        }

        // 해당 태그 UUID 를 이용해 태그명을 조회 (조회 결과가 없으면 자동으로 빈 리스트 처리)
        List<String> tagNames = vibeRepository.findTagNameByTagIds(top3);

        return (tagNames != null && !tagNames.isEmpty()) ? tagNames : Collections.emptyList();
    }

    /**
     * 회원 정보를 수정하는 메서드
     */
    @Transactional
    public void updateUser(UUID userId, UserUpdateRequest request) {
        // 닉네임 유효성 검증
        checkNicknameDuplication(request.getNickname());
        // dto -> entity
        UserEntity entity = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 회원 정보 업데이트, 더티체킹
        entity.getProfile().updateUser(request.getNickname(), request.getProfileImageUrl());
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
