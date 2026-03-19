package com.degging.be.global.util;

import lombok.extern.slf4j.Slf4j;
import net.coobird.thumbnailator.Thumbnails;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import org.springframework.mock.web.MockMultipartFile;

/**
 * 요청 속 이미지 크기 조정을 위한 Util 클래스
 */
@Slf4j
public class ImageUtils {
    /**
     * 원본 이미지 크기를 줄이는 메서드 (CafeImageEntity 의 필드 저장용)
     */
    public static MultipartFile resizeImage(MultipartFile file, int targetWidth) throws IOException {
        // 원본이 이미 작다면 (예: 100KB 미만) 리사이징 건너뛰기
        if (file.getSize() < 100 * 1024) {
            log.info("[리사이징 스킵] 이미 충분히 작은 파일입니다. 크기: {}KB", file.getSize() / 1024);
            return file;
        }

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        // 비율 맞춰서 너비(width) 기준으로 리사이징
        // 비율 유지 옵션으로 가로, 세로 중 하나만 맞아도 되게 설정
        Thumbnails.of(file.getInputStream())
                .size(targetWidth, targetWidth) // 가로 세로 중 큰 쪽을 targetWidth 에 맞춤
                .keepAspectRatio(true)          // 비율 유지
                .outputFormat("jpg")            // 용량 최적화를 위해 jpg 지정
                .outputQuality(0.9f)            // 용량 대비 화질 좋게
                .toOutputStream(outputStream);

        return new MockMultipartFile(
                file.getOriginalFilename(),
                file.getOriginalFilename(),
                "image/jpeg",
                outputStream.toByteArray()
        );
    }

    /**
     * 썸네일 이미지 생성 시 사용하는 메서드 (빠른 조회를 위해 경량화, cafeEntity 의 필드 저장용)
     * 카페 데이터 적재 시 사용
     */
    public static MultipartFile createCafeThumbnail(MultipartFile file) throws IOException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        Thumbnails.of(file.getInputStream())
                .size(300, 300)
                .keepAspectRatio(true)   
                .outputFormat("jpg")          
                .outputQuality(0.7f)    // 리스트 로딩 속도 향상 및 네트워크 트래픽 절감을 위한 압축
                .toOutputStream(outputStream);

        return new MockMultipartFile(
                file.getOriginalFilename(),
                file.getOriginalFilename(),
                "image/jpeg",
                outputStream.toByteArray()
        );
    }
}
