package com.degging.be.infra.storage.s3;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.google.cloud.storage.BlobInfo;
import com.google.cloud.storage.Storage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.UUID;

/**
 * Google Cloud Service 로 이미지를 관리하는 클래스
 */ 
//@Service
@Slf4j
@RequiredArgsConstructor
public class GcsImageService implements ImageService{

    private final Storage storage;

    @Value("${spring.cloud.gcp.storage.bucket}")
    private String bucketName;

    // Cloudflare 도메인
    @Value("${app.image.domain}")
    private String imageDomain;

    /**
     * Google Cloud Service 에 이미지를 업로드하는 메서드
     * @return fakeUrl, 반환 받은 퍼블릭 URL
     */
    @Override
    public String uploadImage(MultipartFile file, String folderName) {
        String fileName = folderName + "/" + UUID.randomUUID() + "_" + file.getOriginalFilename();

        try {
            BlobInfo blobInfo = BlobInfo.newBuilder(bucketName, fileName)
                    .setContentType(file.getContentType())
                    .build();

            // 버킷에 해당 파일 업로드
            storage.create(blobInfo, file.getBytes());

            // Cloudflare 결합
            return imageDomain + (imageDomain.endsWith("/") ? "" : "/") + fileName;

        } catch (IOException e) {
            log.error("GCS 업로드 중 IOException 발생: ", e);
            throw new BaseException(CommonErrorCode.FILE_PROCESSING_ERROR);
        }
    }


    /**
     * Google Cloud Service 에서 이미지를 삭제하는 메서드
     */
    @Override
    public void deleteImage(String imageUrl) {
        try {
            String fileName = imageUrl.replace(imageDomain, "");
            // '/'를 포함하고 있다면 제거해줌
            if (fileName.startsWith("/")) fileName = fileName.substring(1);

            // 버킷에서 해당 파일 제거
            boolean deleted = storage.delete(bucketName, fileName);

            if (deleted){
                log.info("[GCS] 파일 삭제 성공: {}", fileName);
            } else {
                log.warn("[GCS] 파일 삭제 실패: {}", fileName);
            }
        } catch (Exception e){
            // 메인 로직이 롤백되지 않도록 로그만 기록
            log.error("[GCS] 이미지 삭제 중 네트워크 오류 또는 권한 문제 발생. URL: {}, Error: {}", imageUrl, e.getMessage());
        }
    }
}
