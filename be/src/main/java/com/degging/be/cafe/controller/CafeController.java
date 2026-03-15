package com.degging.be.cafe.controller;

import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.service.CafeService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
}