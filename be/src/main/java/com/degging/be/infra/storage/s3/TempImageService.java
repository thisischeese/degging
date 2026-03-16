package com.degging.be.infra.storage.s3;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

/**
 * 사진 유료 저장소 연결 전 사용할 임시 클래스
 */
@Service
@Primary // 인터페이스 주입 시 우선 순위로 설정
@Slf4j
public class TempImageService implements ImageService{

    /**
     * Google Cloud Service 에 이미지를 업로드하는 메서드
     * @return fakeUrl, 반환 받은 퍼블릭 URL 
     */
    @Override
    public String uploadImage(MultipartFile file, String folderName) {
        log.info("[임시] 사진 업로드 - 폴더: {}, 파일명: {}", folderName, file.getOriginalFilename());

        // 실제 Cloudflare 도메인이 들어올 자리 시뮬레이션
        String fakeUrl = "https://temp-cdn.degging.com/" + folderName + "/" + UUID.randomUUID() + "_" + file.getOriginalFilename();
        log.info("[임시] 생성된 가짜 URL : {}", fakeUrl);
        return fakeUrl;
    }

    /**
     * Google Cloud Service 에서 이미지를 삭제하는 메서드
     */
    @Override
    public void deleteImage(String imageUrl) {
        log.info("[임시] 삭제된 가짜 URL : {}", imageUrl);
    }
}
