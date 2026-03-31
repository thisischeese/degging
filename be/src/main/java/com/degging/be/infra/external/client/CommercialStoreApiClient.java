package com.degging.be.infra.external.client;

import com.degging.be.infra.external.dto.response.StoreListInUpjongResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * 소상공인시장진흥공단 상가(상권)정보 API 호출 클라이언트
 *
 * 업종별 상가업소 조회(/storeListInUpjong) 기능 담당
 */
@Component
@RequiredArgsConstructor
public class CommercialStoreApiClient {

    // Builder가 아니라 이미 build된 WebClient를 직접 주입
    private final WebClient webClient;

    @Value("${public-data.commercial-store.service-key}")
    private String serviceKey;

    /**
     * 특정 업종 코드에 해당하는 상가업소 목록 조회
     *
     * @param upjongCode 상권업종소분류코드 (ex. I21201)
     * @param pageNo 현재 페이지 번호
     * @param rows 페이지당 조회 건수
     * @return 업종별 상가업소 조회 응답 DTO
     */
    public StoreListInUpjongResponse fetchCafeStores(String upjongCode, int pageNo, int rows) {
        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .scheme("https")
                        .host("apis.data.go.kr")
                        .path("/B553077/api/open/sdsc2/storeListInUpjong")
                        .queryParam("ServiceKey", serviceKey)
                        .queryParam("pageNo", pageNo)
                        .queryParam("numOfRows", rows)
                        .queryParam("divId", "indsSclsCd")
                        .queryParam("key", upjongCode)
                        .queryParam("type", "json")
                        .build())
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .bodyToMono(StoreListInUpjongResponse.class)
                .block();
    }
}