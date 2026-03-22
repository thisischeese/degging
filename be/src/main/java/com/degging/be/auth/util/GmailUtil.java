package com.degging.be.auth.util;

import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.global.repository.SystemEntityRepository;
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import com.google.api.services.gmail.Gmail;
import com.degging.be.global.exception.BaseException;
import jakarta.mail.Session;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.util.Properties;

@Slf4j
@RequiredArgsConstructor
@Component
public class GmailUtil {

    private final SystemEntityRepository systemEntityRepository;

    @Value("${spring.gmail.client-id}")
    private String clientId;

    @Value("${spring.gmail.secret-key}")
    private String clientSecret;

    private Gmail gmailService;

    public synchronized Gmail getGmailService() throws Exception {
        // 이미 생성된 객체가 있다면 즉시 반환
        if (gmailService != null) {
            return gmailService;
        }

        // DB에서 Refresh Token 조회
        String refreshToken = systemEntityRepository.findById("GOOGLE_REFRESH_TOKEN")
                .map(config -> config.getConfigValue())
                .orElseThrow(() -> {
                    log.error("Google API Refresh Token이 DB에 설정되지 않았습니다. system_entity 테이블을 확인하세요.");
                    return new BaseException(CommonErrorCode.INTERNAL_SERVER_ERROR);
                });

        final var httpTransport = GoogleNetHttpTransport.newTrustedTransport();
        final var jsonFactory = GsonFactory.getDefaultInstance();

        // 파일 시스템(FileDataStoreFactory)을 사용하지 않고 직접 토큰 주입하여 인메모리 생성
        GoogleCredential credential = new GoogleCredential.Builder()
                .setTransport(httpTransport)
                .setJsonFactory(jsonFactory)
                .setClientSecrets(clientId, clientSecret)
                .build()
                .setRefreshToken(refreshToken);

        // 생성된 객체를 필드에 할당
        gmailService = new Gmail.Builder(httpTransport, jsonFactory, credential)
                .setApplicationName("Degging")
                .build();

        return gmailService;
    }

    /**
     * 공통 메일 발송 메서드
     *
     * @param adminMail 발신자 주소
     * @param userEmail 수신자 주소
     * @param subject 메일 제목
     * @param content 메일 내용
     */
    public void sendEmail(String adminMail, String userEmail, String subject, String content) {
        try {
            // 인증된 Gmail 서비스 객체 가져옴
            Gmail service = getGmailService();

            // 세션, 속성을 기반으로 MimeMessage 객체를 생성
            MimeMessage email = new MimeMessage(Session.getDefaultInstance(new Properties()));

            // 메일 내용
            email.setFrom(new InternetAddress(adminMail, "스위트 걸", "UTF-8"));
            email.addRecipient(jakarta.mail.Message.RecipientType.TO, new InternetAddress(userEmail));
            email.setSubject(subject);
            email.setText(content, "UTF-8");

            // 생성한 메일 데이터를 구글 API로 전달하기 위해 바이트 배열 형태로 추출
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            email.writeTo(buffer);
            byte[] rawMessageBytes = buffer.toByteArray();
            // Gmail API 규격에 따라 데이터를 URL 통신에 안전한 Base64 형식의 문자열로 변환
            String encodedEmail = java.util.Base64.getUrlEncoder().encodeToString(rawMessageBytes);

            // 구글 API 전용 메시지 객체에 인코딩된 데이터 주입
            Message message = new Message();
            message.setRaw(encodedEmail);

            // 현재 인증된 사용자 본인(me)의 계정 권한으로 실제 메일 전송 명령 수행
            Message sentMessage = service.users().messages().send("me", message).execute();

            // 전송 성공 시 로그 확인용
            log.info("메일 전송 성공! Message ID: {}", sentMessage.getId());
        } catch (Exception e) {
            // 전송 실패 시 로그 확인용
            log.error("메일 전송 실패: {}", e.getMessage());
            // 예외를 던져줘야 응답에서 실패로 나오게 됨
            throw new BaseException(CommonErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

}