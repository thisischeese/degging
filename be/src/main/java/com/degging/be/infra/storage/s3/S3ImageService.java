package com.degging.be.infra.storage.s3;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.util.UUID;

/**
 * Google Cloud Service 로 이미지를 관리하는 클래스
 */ 
//@Service
@Slf4j
@Service
@Primary
@RequiredArgsConstructor
public class S3ImageService implements ImageService{

    private final S3Client s3Client;

    @Value("${spring.cloud.aws.s3.bucket}")
    private String bucketName;

    // Cloudflare 도메인
    @Value("${app.image.domain}")
    private String imageDomain;

    /**
     * S3에 이미지를 업로드하는 메서드
     * @return CloudFront가 적용된 퍼블릭 URL
     */
    @Override
    public ImageUploadResult uploadImage(MultipartFile file, String folderName) {
        // 확장자 조회
        String extension = StringUtils.getFilenameExtension(file.getOriginalFilename());
        // 원본명 저장
        String originalName = file.getOriginalFilename();
        // S3 에 저장될 고유키 생성
        String storedName = folderName + "/" + UUID.randomUUID() + "." + extension;

        try {
            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(storedName)
                    .contentType(file.getContentType())
                    .build();

            // 버킷에 해당 파일 업로드
            s3Client.putObject(putObjectRequest,
                    RequestBody.fromInputStream(file.getInputStream(), file.getSize()));

            String url = imageDomain + (imageDomain.endsWith("/") ? "" : "/") + storedName;
            // CloudFront 결합 후 DTO 에 정보 담아 반환
            return new ImageUploadResult(url, storedName, originalName);

        } catch (IOException e) {
            log.error("S3 업로드 중 IOException 발생: ", e);
            throw new BaseException(CommonErrorCode.FILE_PROCESSING_ERROR);
        }
    }


    /**
     * S3에서 이미지를 삭제하는 메서드
     */
    @Override
    public void deleteImage(String imageUrl) {
        try {
            String fileName = imageUrl.replace(imageDomain, "");
            // '/'를 포함하고 있다면 제거해줌
            if (fileName.startsWith("/")) fileName = fileName.substring(1);

            // 삭제 요청 객체 생성
            DeleteObjectRequest deleteRequest = DeleteObjectRequest.builder()
                    .bucket(bucketName)
                    .key(fileName)
                    .build();

            // 버킷에서 해당 파일 제거
            s3Client.deleteObject(deleteRequest);
            log.info("[S3] 파일 삭제 성공: {}", fileName);

        } catch (Exception e){
            // 메인 로직이 롤백되지 않도록 로그만 기록
            log.error("[S3] 이미지 삭제 중 오류 발생. URL: {}, Error: {}", imageUrl, e.getMessage());        }
    }
}
