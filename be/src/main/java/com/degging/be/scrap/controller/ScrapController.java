package com.degging.be.scrap.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.dto.response.ScrapDetailResponse;
import com.degging.be.scrap.dto.response.ScrapResponse;
import com.degging.be.scrap.dto.response.ScrapShareResponse;
import com.degging.be.scrap.service.ScrapService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
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

    /**
     * 모든 스크랩을 조회하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200, List<ScrapResponse> 유저의 스크랩 정보 리스트
     */
    @GetMapping
    public BaseResponse<List<ScrapResponse>> getScraps(
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        List<ScrapResponse> scraps = scrapService.getScrapsByUserId(userId);
        return BaseResponse.success(scraps);
    }

    /**
     * 스크랩 전체 모아보기 조회
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200, 전체 스크랩 조회
     */
    @GetMapping("/all")
    public BaseResponse<ScrapDetailResponse> getAllScraps(
            @AuthenticationPrincipal UserDetails user) {
        UUID userId = getUserId(user);
        return BaseResponse.success(scrapService.getAllScrapDetail(userId));
    }
    
    /**
     * 특정 스크랩을 상세 조회하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 조회하려는 스크랩 ID
     * @return 200, ScrapDetailResponse 스크랩 상세 정보 (스크랩 정보, 카페 정보)
     */
    @GetMapping("/{scrapId}")
    public BaseResponse<ScrapDetailResponse> getScrapDetail(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId){
        UUID userId = getUserId(user);

        ScrapDetailResponse detail = scrapService.getScrapDetail(scrapId, userId);
        return BaseResponse.success(detail);
    }

    /**
     * 스크랩 정보를 수정하는 메서드
     * @param scrapRequest 수정하려는 스크랩 정보 (제목, 색상)
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 수정하려는 스크랩 ID
     * @return 200
     */
    @PatchMapping("/{scrapId}")
    public BaseResponse<?> updateScrap(
            @RequestBody @Valid ScrapRequest scrapRequest,
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId){
        UUID userId = getUserId(user);
        scrapService.updateScrap(scrapRequest, userId, scrapId);
        return BaseResponse.success();
    }

    /**
     * 스크랩을 삭제하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 삭제하려는 스크랩 ID
     * @return 200
     */
    @DeleteMapping("/{scrapId}")
    public BaseResponse<?> deleteScrap(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId){
        UUID userId = getUserId(user);
        scrapService.deleteScrap(userId, scrapId);
        return BaseResponse.success();
    }

    /**
     * 기본 스크랩에 특정 카페를 추가하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param cafeId 추가하려는 카페 ID
     * @return 200
     */
    @PostMapping("/all/{cafeId}")
    public BaseResponse<?> addCafeToDefaultScrap(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "cafeId") UUID cafeId) {

        UUID userId = getUserId(user);
        // Service 단계에서 해당 유저의 'isDefault'가 true인 스크랩을 찾아 처리하도록 넘김
        scrapService.addCafeToDefaultScrap(userId, cafeId);

        return BaseResponse.success();
    }

    /**
     * 특점 스크랩에 특정 카페를 추가하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 카페를 추가하려는 스크랩 ID
     * @param cafeId 추가할 카페 ID
     * @return 200
     */
    @PostMapping("/{scrapId}/cafes/{cafeId}")
    public BaseResponse<?> addCafeToScrap(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId,
            @PathVariable(value = "cafeId") UUID cafeId){
        UUID userId = getUserId(user);
        scrapService.addCafeToScrap(userId, scrapId, cafeId);
        return BaseResponse.success();
    }

    /**
     * 스크랩한 카페를 삭제하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 카페를 삭제하려는 스크랩 ID
     * @param cafeId 삭제할 카페 ID
     * @return 200
     */
    @DeleteMapping("/{scrapId}/cafes/{cafeId}")
    public BaseResponse<?> removeCafeFromScrap(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId,
            @PathVariable(value = "cafeId") UUID cafeId){
        UUID userId = getUserId(user);
        scrapService.removeCafeFromScrap(userId, scrapId, cafeId);
        return BaseResponse.success();
    }

    /**
     * 스크랩 공유 링크를 생성하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param scrapId 공유하려는 스크랩 ID
     * @return 200, 공유 링크
     */
    @PostMapping("/{scrapId}/share-links")
    public BaseResponse<ScrapShareResponse> getShareLink(
            @AuthenticationPrincipal UserDetails user,
            @PathVariable(value = "scrapId") UUID scrapId){
        UUID userId = getUserId(user);
        ScrapShareResponse url = scrapService.generateShareLink(userId, scrapId);
        return BaseResponse.success(url);
    }
}
