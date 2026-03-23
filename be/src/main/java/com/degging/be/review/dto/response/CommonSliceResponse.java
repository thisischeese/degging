package com.degging.be.review.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.data.domain.Slice;

import java.util.List;

/**
 * 리뷰 무한 스크롤용 Slice 객체를 담아 보낼 Response DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CommonSliceResponse<T> {
    private List<T> content;
    private boolean hasNext;    // 다음 페이지 존재 여부
    private int page;           // 현재 페이지 번호

    // Slice 객체를 받아서 바로 변환해주는 정적 팩토리 메서드
    public static <T> CommonSliceResponse<T> from(Slice<T> slice) {
        return CommonSliceResponse.<T>builder()
                .content(slice.getContent())
                .hasNext(slice.hasNext())
                .page(slice.getNumber())
                .build();
    }
}