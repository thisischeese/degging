package com.degging.be.user.service;

import com.degging.be.auth.dto.request.ResetPasswordRequest;
import com.degging.be.auth.dto.request.SignupRequest;
import com.degging.be.auth.service.VerificationService;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.user.dto.response.UserDetailResponse;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
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
        User user = User.builder()
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .nickname(request.getNickname())
                .gender(request.getGender())
                .birthDate(request.getBirthDate())
                .abGroup(group)
                .build();

        userRepository.save(user);

        // 가입 완료 후 Redis의 인증 성공 플래그 제거
        verificationService.removeVerifiedFlag(request.getEmail());

        return user.getUserId();
    }

    /**
     * 특정 회원 정보를 조회하는 메서드
     */
    public UserDetailResponse getUserDetail(UUID userId){
        // 유효성 검사
        User entity = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // password 를 제외하고 dto 로 변환하여 응답
        return UserDetailResponse.from(entity);
    }

    /**
     * A/B 중 더 적은 그룹을 반환하는 메서드
     */
    public Character getLesserGroup(){
        // 현재 회원의 비율을 조회하여 1:1 에 가깝도록 A/B 테스트 그룹 배정
        long countA = userRepository.countByAbGroup('A');
        long countB = userRepository.countByAbGroup('B');
        
        // 같은 수면 A를 우선으로 배정, 기본은 더 적은 그룹으로 배정
        return countA > countB ? 'B' : 'A'; 
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
        if (userRepository.existsByNickname(nickname)) {
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
        User user = userRepository.findByEmail(email)
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
        User user = userRepository.findById(userId)
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
