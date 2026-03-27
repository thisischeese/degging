package com.degging.be.curation.controller;

import com.degging.be.curation.dto.request.CurationMinimapRequest;
import com.degging.be.curation.dto.response.CurationMapResponse;
import com.degging.be.curation.service.CurationService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/curation")
public class CurationController {

    private final CurationService curationService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 특정 큐레이션 요소(카페)의 미니맵 데이터 조회
     *
     * @param user     유효한 사용자
     * @param request  큐레이션 요소(카페)의 미니맵 요청 DTO
     * @return 개별 카페의 미니맵 정보 (좌표 및 전용 소개글 포함)
     */
    @GetMapping("/minimap")
    public BaseResponse<CurationMapResponse> getCurationMinimap(
            @AuthenticationPrincipal UserDetails user,
            @ModelAttribute CurationMinimapRequest request) {

        UUID userId = getUserId(user);
        String category = request.getCategory();
        String cafeName = request.getCafeName();
        
        log.info("Request for curation minimap - category: {}, cafeName: {}, userId: {}", 
                category, cafeName, userId);

        CurationMapResponse response = curationService.getCurationMinimap(userId, category, cafeName);
        return BaseResponse.success(response);
    }
}
