package com.degging.be.scrap.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequset;
import com.degging.be.scrap.service.ScrapService;
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

    // 스크랩 폴더 생성
    @PostMapping
    public BaseResponse<?> createScrap(
            @RequestBody ScrapRequset scrapRequset,
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        scrapService.createScrap(scrapRequset, userId);
        return BaseResponse.success();
    }
}
