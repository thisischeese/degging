package com.degging.be.cafe.controller;

import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.cafe.service.CafeSearchService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.checkerframework.common.reflection.qual.GetClass;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
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
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @param user 인증된 사용자 정보
     * @return 200, AI 분석 결과 (카페 리스트)
     */
    @PostMapping
    public BaseResponse<Map<String, List<UUID>>> processSearch(
                                                 @RequestBody CafeSearchRequest request,
                                                 @AuthenticationPrincipal UserDetails user) {
        log.info("검색 요청 수신됨! 키워드: {}, 좌표: ({}, {})",
                request.getKeyword(), request.getLatitude(), request.getLongitude());

        UUID userId = getUserId(user);
        Map<String, List<UUID>> result = cafeSearchService.processSearch(userId, request);
        return BaseResponse.success(result);
    }
}
