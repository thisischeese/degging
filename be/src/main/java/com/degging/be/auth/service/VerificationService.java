package com.degging.be.auth.service;

import com.degging.be.auth.util.GmailUtil;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.util.concurrent.TimeUnit;

/**
 * 이메일 인증 코드 발송 및 검증을 담당하는 서비스 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class VerificationService {

    private final UserRepository userRepository;
    private final GmailUtil gmailUtil;
    private final StringRedisTemplate redisTemplate;

    @Value("${spring.gmail.admin-mail}")
    private String adminMail;

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    private static final String VERIFY_PREFIX = "verify:";
    private static final String VERIFIED_FLAG = "verified:";

    /**
     * 이메일 인증 코드 발송
     *
     * @param userEmail 인증코드를 발송할 이메일
     */
    @Transactional
    public void sendVerificationCode(String userEmail) {
        // 이메일 중복 확인 (MemberService에서 호출해도 되지만, 발송 전 최종 검증)
        if (userRepository.existsByEmail(userEmail)) {
            throw new BaseException(AuthErrorCode.EMAIL_DUPLICATE);
        }

        // 6자리 랜덤 숫자 생성
        String code = String.format("%06d", SECURE_RANDOM.nextInt(1000000));

        // Redis에 인증 코드 저장 (유효시간 3분)
        redisTemplate.opsForValue().set(VERIFY_PREFIX + userEmail, code, 3, TimeUnit.MINUTES);

        String subject = "[Degging] 회원가입 인증 번호 안내";
        String content = "[Degging] 회원가입 인증 번호 안내\n\n" +
                "안녕하세요, Degging 서비스를 이용해 주셔서 감사합니다.\n" +
                "회원가입을 위한 인증 번호를 아래와 같이 발급해 드립니다.\n\n" +
                "🔢 인증 번호: " + code + "\n\n" +
                "🚨주의 사항\n" +
                "* 인증 번호는 3분간 유효합니다.\n" +
                "* 본인이 요청하지 않은 경우, 고객센터로 문의해 주시기 바랍니다.\n\n" +
                "스위트 걸 드림\n";

        // 메일 발송
        gmailUtil.sendEmail(adminMail, userEmail, subject, content);
    }

    /**
     * 사용자가 입력한 인증 코드 확인
     *
     * @param userEmail 인증코드 수신 이메일
     * @param code      사용자가 입력한 인증 코드
     */
    public void confirmVerificationCode(String userEmail, String code) {
        String savedCode = redisTemplate.opsForValue().get(VERIFY_PREFIX + userEmail);

        if (savedCode == null) {
            throw new BaseException(AuthErrorCode.VERIFICATION_CODE_EXPIRED);
        }

        if (!savedCode.equals(code)) {
            throw new BaseException(AuthErrorCode.VERIFICATION_CODE_MISMATCH);
        }

        // 인증 성공 시 기존 코드 삭제 및 인증 완료 플래그 저장 (10분간 유효)
        redisTemplate.delete(VERIFY_PREFIX + userEmail);
        redisTemplate.opsForValue().set(VERIFIED_FLAG + userEmail, "true", 10, TimeUnit.MINUTES);
    }

    /**
     * 최종 가입/비밀번호 변경 전 인증 완료 여부 확인
     *
     * @param userEmail 확인할 이메일
     * @return 인증 완료 여부 (키가 존재하면 true)
     */
    public boolean isVerified(String userEmail) {
        return redisTemplate.hasKey(VERIFIED_FLAG + userEmail);
    }

    /**
     * 가입 완료 후 인증 플래그 삭제
     *
     * @param userEmail 삭제할 이메일
     */
    public void removeVerifiedFlag(String userEmail) {
        redisTemplate.delete(VERIFIED_FLAG + userEmail);
    }

    /**
     * 임시 비밀번호 메일 발송
     *
     * @param userEmail    수신자 이메일
     * @param tempPassword 생성된 임시 비밀번호
     */
    public void sendTempPassword(String userEmail, String tempPassword) {
        String subject = "[Degging] 임시 비밀번호 발송 안내";
        String content = "[Degging] 임시 비밀번호 발송 안내\n\n" +
                "안녕하세요, Degging 서비스를 이용해 주셔서 감사합니다.\n" +
                "요청하신 임시 비밀번호를 아래와 같이 발급해 드립니다.\n\n" +
                "🔑 임시 비밀번호: " + tempPassword + "\n\n" +
                "🚨주의 사항\n" +
                "* 로그인 후 마이페이지에서 꼭 비밀번호를 변경해 주세요!\n" +
                "* 본인이 요청하지 않은 경우, 고객센터로 문의해 주시기 바랍니다.\n\n" +
                "스위트 걸 드림\n";

        gmailUtil.sendEmail(adminMail, userEmail, subject, content);
    }
}
