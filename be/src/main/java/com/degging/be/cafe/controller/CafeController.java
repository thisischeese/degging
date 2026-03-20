package com.degging.be.cafe.controller;

import com.degging.be.cafe.dto.request.CafeBottomSheetRequest;
import com.degging.be.cafe.dto.request.CafeMapRequest;
import com.degging.be.cafe.dto.response.internal.CafeBottomSheetResponse;
import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.dto.response.internal.CafeOnboardingResponse;
import com.degging.be.cafe.service.CafeService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Slice;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * 카페 서비스 전용 컨트롤러
 */
@RestController
@RequestMapping("/api/cafes")
@RequiredArgsConstructor
public class CafeController {

    private final int DEFAULT_ONBOARDING_COUNT = 8;

    private final CafeService cafeService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 카페 상세 정보 조회 API
     *
     * @param user 유효한 사용자
     * @param cafeId 조회할 카페의 UUID
     * @return 카페 상세 정보를 담은 BaseResponse
     */
    @GetMapping("/{cafeId}")
    public BaseResponse<CafeDetailResponse> getCafeDetail(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable UUID cafeId) {

        UUID userId = getUserId(user);

        CafeDetailResponse response = cafeService.getCafeDetail(userId, cafeId);

        return BaseResponse.success(response);
    }

    /**
     * 지도 내 카페 마커(핀) 목록 조회 API
     * 사용자의 현재 위치를 기준으로 반경 2km 이내의 카페 위치 정보를 반환합니다.
     *
     * @param user 유효한 사용자
     * @param request 사용자 현재 위치(위도, 경도)를 담은 요청 객체
     * @return 반경 내 카페 마커 리스트를 담은 공통 응답 객체
     */
    @GetMapping("/map/markers")
    public BaseResponse<List<CafeMapResponse>> getCafeMarkers(
            @AuthenticationPrincipal UserDetails user,
            @ModelAttribute CafeMapRequest request) {

        List<CafeMapResponse> response = cafeService.getCafeMarkers(request);

        return BaseResponse.success(response);
    }

    /**
     * 지도 바텀시트 카페 리스트 조회 API
     * 반경 2km 내 카페를 프랜차이즈 포함여부와 정렬 기준에 따라 페이징 처리하여 반환합니다.
     * 
     * @param user 유효한 사용자
     * @param request 위치, 프랜차이즈 필터, 정렬 기준 정보
     * @param page 조회할 페이지 번호 (0번부터 시작, 무한 스크롤 용)
     * @param size 페이지 당 항목 수 (기본 10)
     * @return 무한 스크롤 가능한 바텀시트 정보 Slice
     */
    @GetMapping("/map/bottom-sheet")
    public BaseResponse<Slice<CafeBottomSheetResponse>> getBottomSheetCafes(
            @AuthenticationPrincipal UserDetails user,
            @ModelAttribute CafeBottomSheetRequest request,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        
        getUserId(user); // 인증 체크 용도

        Slice<CafeBottomSheetResponse> responses = cafeService.getBottomSheetCafes(request, page, size);

        return BaseResponse.success(responses);
    }

    /**
     * 온보딩 화면에서 사용할 랜덤 카페 아이템 리스트를 조회합니다.
     * 상호명 없이 썸네일 이미지만 포함된 8개의 카페 정보를 반환합니다.
     *
     * @return 8개의 랜덤 카페 온보딩 정보 리스트
     */
    @GetMapping("/onboarding")
    public BaseResponse<List<CafeOnboardingResponse>> getOnboardingItems() {

        // DEFAULT_ONBOARDING_COUNT(8)개의 카페 추출 요청
        List<CafeOnboardingResponse> responses = cafeService.getRandomOnboardingItems(DEFAULT_ONBOARDING_COUNT);

        return BaseResponse.success(responses);
    }

}