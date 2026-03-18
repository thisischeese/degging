package com.degging.be.cafe.client;

import com.degging.be.cafe.dto.response.external.SeoulFoodResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * 서울시 휴게음식점 인허가 정보 API 클라이언트
 *
 * 서울시 열린데이터 광장에서 제공하는 API를 통해 카페의 영업 상태(영업/폐업) 정보 확인
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SeoulFoodApiClient {

    // Builder가 아니라 이미 build된 WebClient를 직접 주입
    private final WebClient webClient;

    @Value("${public-data.seoul-food.service-key}")
    private String serviceKey;

    private static final String BASE_URL = "http://openapi.seoul.go.kr:8088";

    /**
     * 서울시 휴게음식점 인허가 정보 조회
     *
     * @param start 인덱스 시작 번호
     * @param end 인덱스 종료 번호
     * @return 서울시 API 응답 데이터 DTO
     */
    public SeoulFoodResponse fetchCafeStatus(int start, int end) {
        // 서울시 API 구조: BASE_URL/인증키/json/localdata_072405/시작/종료
        String url = String.format("%s/%s/json/localdata_072405/%d/%d", BASE_URL, serviceKey, start, end);

        return webClient.get()
                .uri(url)
                .retrieve()
                .bodyToMono(SeoulFoodResponse.class)
                .block();
    }
}