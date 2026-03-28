package com.degging.be.cafe.controller;

import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.cafe.dto.response.internal.CafeSearchResponse;
import com.degging.be.cafe.service.CafeSearchService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * 검색용 컨트롤러
 */
@Slf4j
@RestController
@RequestMapping("/api/cafes/search")
@RequiredArgsConstructor
public class CafeSearchController {
    private final CafeSearchService cafeSearchService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 검색 메서드
     * @param request 프론트엔드가 보낸 원본 검색어, 태그 및 좌표
     * @param user 인증된 사용자 정보
     * @return 200, AI 분석 결과 (추천 카페 리스트)
     */
    @PostMapping
    public BaseResponse<CafeSearchResponse> processSearch(
                                                 @RequestBody CafeSearchRequest request,
                                                 @AuthenticationPrincipal UserDetails user) {
        UUID userId = getUserId(user);
        CafeSearchResponse result = cafeSearchService.processSearch(userId, request);
        return BaseResponse.success(result);
    }

    // 정렬 API GET /api/cafes/search/results?sort
}
