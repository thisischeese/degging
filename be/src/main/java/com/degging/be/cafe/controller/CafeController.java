package com.degging.be.cafe.controller;

import com.degging.be.cafe.dto.request.CafeMapRequest;
import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.service.CafeService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
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
}