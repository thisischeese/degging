package com.degging.be.infra.storage.s3;

import org.springframework.web.multipart.MultipartFile;

/**
 * 이미지 연동을 다루는 인터페이스
 */
public interface ImageService {
    // 이미지 업로드
    ImageUploadResult uploadImage(MultipartFile file, String folderName);

    // 이미지 삭제
    void deleteImage(String imageUrl);
}
