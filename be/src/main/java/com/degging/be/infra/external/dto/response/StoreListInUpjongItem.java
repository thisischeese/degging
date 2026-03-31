package com.degging.be.infra.external.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

/**
 * 업종별 상가업소 조회 API의 개별 업소 DTO
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class StoreListInUpjongItem {

    // 상가업소번호
    private String bizesId;

    // 상호명
    private String bizesNm;

    // 지점명
    private String brchNm;

    // 상권업종 대분류 코드
    private String indsLclsCd;

    // 상권업종 대분류명
    private String indsLclsNm;

    // 상권업종 중분류 코드
    private String indsMclsCd;

    // 상권업종 중분류명
    private String indsMclsNm;

    // 상권업종 소분류 코드
    private String indsSclsCd;

    // 상권업종 소분류명
    private String indsSclsNm;

    // 표준산업분류 코드
    private String ksicCd;

    // 표준산업분류명
    private String ksicNm;

    // 시도 코드
    private String ctprvnCd;

    // 시도명
    private String ctprvnNm;

    // 시군구 코드
    private String signguCd;

    // 시군구명
    private String signguNm;

    // 행정동 코드
    private String adongCd;

    // 행정동명
    private String adongNm;

    // 법정동 코드
    private String ldongCd;

    // 법정동명
    private String ldongNm;

    // 지번 주소
    private String lnoAdr;

    // 도로명 주소
    private String rdnmAdr;

    // 건물명
    private String bldNm;

    // 층 정보
    private String flrNo;

    // 호 정보
    private String hoNo;

    // 경도
    private Double lon;

    // 위도
    private Double lat;
}