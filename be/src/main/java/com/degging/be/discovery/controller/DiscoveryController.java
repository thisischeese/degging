package com.degging.be.discovery.controller;

import com.degging.be.discovery.dto.response.DiscoveryResponse;
import com.degging.be.discovery.service.DiscoveryService;
import com.degging.be.global.dto.BaseResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.data.domain.Slice;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import java.util.List;
import java.util.UUID;

/**
 * 탐색(Discovery) 탭 전용 컨트롤러
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/discovery")
public class DiscoveryController {

    private final DiscoveryService discoveryService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 탐색 탭 메인 화면 진입 및 무한 스크롤용 - 일일 랜덤 카페 리스트 조회
     *
     * @param page 조회할 페이지 번호 (0번부터 시작)
     * @param size 페이지 당 썸네일 수 (기본 15개 추천)
     * @return 일일 랜덤 카페 썸네일 무한스크롤 데이터(Slice)
     */
    @GetMapping
    public BaseResponse<Slice<DiscoveryResponse>> getDiscoveryCafes(
            @AuthenticationPrincipal UserDetails user,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "15") int size) {

        UUID userId = null;
        if (userDetails != null) {
            try {
                userId = UUID.fromString(userDetails.getUsername());
            } catch (IllegalArgumentException e) {
                log.warn("유효하지 않은 사용자 UUID 형식: {}", userDetails.getUsername());
            }
        }
        
        Slice<DiscoveryResponse> responses = discoveryService.getDailyDiscoveryCafes(page, size, userId);
        return BaseResponse.success(responses);
    }
}
