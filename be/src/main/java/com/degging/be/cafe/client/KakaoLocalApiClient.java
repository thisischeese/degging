package com.degging.be.cafe.client;

import com.degging.be.cafe.dto.response.external.KakaoPlaceResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * 카카오 로컬 API 호출 클라이언트
 *
 * 카페 이름 기반으로 카카오 장소 검색 API를 호출
 */
@Component
@RequiredArgsConstructor
public class KakaoLocalApiClient {

    // Builder가 아니라 이미 build된 WebClient를 직접 주입
    private final WebClient webClient;

    @Value("${kakao.rest-api-key}")
    private String kakaoRestApiKey;

    /**
     * 카카오 장소 검색 API 호출
     *
     * @param keyword 검색 키워드 (카페 이름)
     * @param page 페이지 번호
     * @param size 페이지 크기
     * @return 카카오 장소 검색 응답 DTO
     */
    public KakaoPlaceResponse searchPlaces(String keyword, int page, int size) {

        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .scheme("https")
                        .host("dapi.kakao.com")
                        .path("/v2/local/search/keyword.json")
                        .queryParam("query", keyword)
                        .queryParam("page", page)
                        .queryParam("size", size)
                        .build())
                .header(HttpHeaders.AUTHORIZATION, "KakaoAK " + kakaoRestApiKey)
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .bodyToMono(KakaoPlaceResponse.class)
                .block();
    }
}