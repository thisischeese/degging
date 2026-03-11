package com.degging.be.scrap.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.service.ScrapService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * 카페 스크랩 관련 API 컨트롤러
 */
@RestController
@RequestMapping("/api/scraps")
@RequiredArgsConstructor
public class ScrapController {
    private final ScrapService scrapService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 스크랩 폴더를 생성하는 메서드
     * @param scrapRequest 스크랩 폴더를 생성하기 위한 입력값 (스크랩명, 색상)
     * @param user  JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200
     */
    @PostMapping
    public BaseResponse<?> createScrap(
            @RequestBody @Valid ScrapRequest scrapRequest,
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        scrapService.createScrap(scrapRequest, userId);
        return BaseResponse.success();
    }
}
