package com.degging.be.global.util;

import net.coobird.thumbnailator.Thumbnails;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import org.springframework.mock.web.MockMultipartFile;

/**
 * 요청 속 이미지 크기 조정을 위한 Util 클래스
 */
public class ImageUtils {
    public static MultipartFile resizeImage(MultipartFile file, int targetWidth) throws IOException {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        // 비율 맞춰서 너비(width) 기준으로 리사이징
        // .size(가로, 세로) 지만 하나만 맞추고 싶으면 비율 유지 옵션을 씁니다.
        Thumbnails.of(file.getInputStream())
                .size(targetWidth, targetWidth) // 가로 세로 중 큰 쪽을 targetWidth에 맞춤
                .keepAspectRatio(true)          // 비율 유지 (이미지 안 찌그러짐)
                .outputFormat("jpg")            // 용량 최적화를 위해 jpg 권장
                .outputQuality(0.9f)            // 용량 대비 화질 좋게
                .toOutputStream(outputStream);

        return new MockMultipartFile(
                file.getOriginalFilename(),
                file.getOriginalFilename(),
                "image/jpeg",
                outputStream.toByteArray()
        );
    }
}
