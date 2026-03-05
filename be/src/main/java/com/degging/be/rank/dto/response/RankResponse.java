package com.degging.be.rank.dto.response;

import lombok.*;

import java.util.List;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class RankResponse {
    private List<Items> rankings; // 랭킹 리스트

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Items {
        private int rank; // 순위
        private String keyword; // 디저트명 (ex 두쫀쿠, 강남역 크로플)
    }
}
