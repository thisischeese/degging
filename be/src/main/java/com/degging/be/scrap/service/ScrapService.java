package com.degging.be.scrap.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import com.degging.be.global.exception.errorcode.ScrapErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.dto.response.ScrapCafeResponse;
import com.degging.be.scrap.dto.response.ScrapDetailResponse;
import com.degging.be.scrap.dto.response.ScrapResponse;
import com.degging.be.scrap.dto.response.ScrapShareResponse;
import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.entity.ScrapItemEntity;
import com.degging.be.scrap.entity.ScrapShareLinkEntity;
import com.degging.be.scrap.repository.ScrapItemRepository;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.scrap.repository.ScrapShareLinkRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * 카페 스크랩을 관리하는 서비스 클래스
 */
@Transactional(readOnly = true)
@Service
@RequiredArgsConstructor
public class ScrapService {
    private final ScrapRepository scrapRepository;
    private final UserRepository userRepository;
    private final CafeRepository cafeRepository;
    private final ScrapItemRepository scrapItemRepository;
    private final ScrapShareLinkRepository scrapShareLinkRepository;
    
    @Value("${app.frontend.base-url}")
    private String frontEndBaseUrl; // 토큰 생성에 사용


    // 썸네일 동기화 메서드 (스크랩에 카페 추가/삭제 시 호출)
    private void syncScrapThumbnails(ScrapEntity scrap) {
        // DB에서 최신 4장 조회
        List<String> latest4Urls = scrapItemRepository.findTopImageUrlsByScrapId(
                scrap.getScrapId(), PageRequest.of(0, 4)
        );
        // 엔티티에 덮어쓰기 (Dirty Checking 적용)
        scrap.updateThumbnailUrls(latest4Urls);
    }

    /**
     * 스크랩 폴더 생성하는 메서드 
     */
    @Transactional
    public void createScrap(ScrapRequest scrapRequest, UUID userId) {
        // user 검증
        User user = getValidUser(userId);

        // 스크랩 명 중복 확인
        checkScrapValidation(scrapRequest.getName(), user);
        
        // Entity 에 name, color 와 user 정보를 담아줌
        ScrapEntity entity = ScrapEntity.builder()
                        .name(scrapRequest.getName())
                        .color(scrapRequest.getColor())
                        .user(user)
                        .build();

        // DB 저장
        scrapRepository.save(entity);
    }

    /**
     * 회원의 스크랩 목록을 조회하는 메서드
     */
    public List<ScrapResponse> getScrapsByUserId(UUID userId) {
        // user 검증
        User user = getValidUser(userId);
        
        // 커스텀 스크랩 목록 조회
        List<ScrapEntity> entities = scrapRepository.findAllByUserUserId(userId);
        // DTO 로 변환
        List<ScrapResponse> customFolders = entities.stream()
                .map(ScrapResponse::toDto)
                .toList();

        // 전체 스크랩 조회 (썸네일) - 해당 유저의 전체 최신 스크랩 이미지 4장을 가져와 사용
        List<String> allFolderThumbnails = scrapItemRepository.findTopImageUrlsByUserId(userId,
                PageRequest.of(0, 4)
        );

        // 모든 스크랩의 가상 DTO 생성
        ScrapResponse allScrapFolder = ScrapResponse.builder()
                .scrapId(null)
                .name("모든 스크랩")
                .thumbnailUrls(allFolderThumbnails) // 조립한 썸네일 4장
                .build();

        // 4. 리스트 조립 (전체 폴더를 맨 앞에 배치)
        List<ScrapResponse> result = new ArrayList<>();
        result.add(allScrapFolder);
        result.addAll(customFolders);

        return result;
    }

    /**
     * 특정 스크랩의 상세 정보를 조회하는 메서드
     */
    public ScrapDetailResponse getScrapDetail(UUID scrapId, UUID userId) {
        // user 검증
        User user = getValidUser(userId);

        // scrap 과 cafe, item 조회
        ScrapEntity scrap = scrapRepository.findByIdWithCafesAndImages(scrapId)
                .orElseThrow(()-> new BaseException(ScrapErrorCode.SCRAP_NOT_FOUND));

        // 내 스크랩인지 확인
        if (!scrap.getUser().getUserId().equals(userId)) {
            throw new BaseException(ScrapErrorCode.SCRAP_ACCESS_DENIED);
        }

        // 썸네일 최대 4장 가져와
        List<String> thumbnailUrls = scrap.getScrapItems().stream()
                .sorted(Comparator.comparing(ScrapItemEntity::getCreatedAt).reversed()) // 최신순으로
                .limit(4) // 최대 4장
                .map(item -> item.getCafe().getThumbnailUrl())
                .toList();

        // 반환 객체인 ScrapDetailResponse 에 맞게 담아줌
        List<ScrapCafeResponse> cafes = scrap.getScrapItems().stream()
                .map(ScrapCafeResponse::toDto).toList();

        // 스크랩 정보, 카페 정보, 썸네일을 담아 반환
        return ScrapDetailResponse.builder()
                .scrapId(scrap.getScrapId())
                .name(scrap.getName())
                .color(scrap.getColor())
                .thumbnailUrls(thumbnailUrls)
                .cafes(cafes)
                .build();
    }

    /**
     * 스크랩 정보 수정
     */
    @Transactional
    public void updateScrap(@Valid ScrapRequest scrapRequest, UUID userId, UUID scrapId) {
        User user = getValidUser(userId);
        ScrapEntity scrap = getValidScrap(scrapId);

        // 본인 스크랩인지 유효성 검사
        validateUser(user, scrap);

        // 제목 중복 검사 (이름이 변경된 경우에만)
        if (!scrap.getName().equals(scrapRequest.getName())) {
            checkScrapValidation(scrapRequest.getName(), user);
        }

        // 수정 사항 반영
        scrap.update(scrapRequest.getName(), scrapRequest.getColor());
    }

    /**
     * 스크랩을 삭제하는 메서드
     */
    @Transactional
    public void deleteScrap(UUID userId, UUID scrapId) {
        // 회원, 작성자 본인 확인, 스크랩 유효성 검사
        User user = getValidUser(userId);
        ScrapEntity scrap = getValidScrap(scrapId);
        validateUser(user, scrap);

        // 스크랩 삭제 (cascade)
        scrapRepository.delete(scrap);
    }


    /**
     * 스크랩 폴더에 카페를 추가하는 메서드
     */
    @Transactional
    public void addCafeToScrap(UUID userId, UUID scrapId, UUID cafeId) {
        // 카페, 유저, 스크랩 유효성 검사
        User user = getValidUser(userId);
        ScrapEntity scrap = getValidScrap(scrapId);
        validateUser(user,scrap);
        CafeEntity cafe = cafeRepository.findById(cafeId)
                .orElseThrow(() -> new BaseException(CafeErrorCode.CAFE_NOT_FOUND));

        // 스크랩에 존재하는 카페인지 중복확인
        if (scrapItemRepository.existsByScrapAndCafe(scrap, cafe)) {
            throw new BaseException(ScrapErrorCode.CAFE_ALREADY_SCRAPPED);
        }

        // ScrapItemEntity 생성
        ScrapItemEntity entity = ScrapItemEntity.builder()
                        .scrap(scrap)
                        .cafe(cafe)
                        .build();
        // 스크랩에 카페 추가
        scrap.addScrapItem(entity);
        scrapItemRepository.save(entity);

        // 썸네일 동기화 (최신 4장 가져옴)
        syncScrapThumbnails(scrap);
    }

    /**
     * 스크랩에서 카페를 삭제하는 메서드 (스크랩 취소)
     */
    @Transactional
    public void removeCafeFromScrap(UUID userId, UUID scrapId, UUID cafeId) {
        // 유효성 검사
        User user = getValidUser(userId);
        ScrapEntity scrap = getValidScrap(scrapId);
        validateUser(user, scrap);

        // scrap 에서 cafe 삭제
        scrapItemRepository.deleteByScrap_ScrapIdAndCafe_CafeId(scrapId, cafeId);

        // 영속성 컨텍스트 플러시 (DB에 삭제 쿼리 즉시 반영)
        scrapItemRepository.flush();

        // 썸네일 동기화 (해당 카페가 삭제된 후 남은 최신 4장으로 갱신)
        syncScrapThumbnails(scrap);
    }

    /**
     * 스크랩 공유 링크 (토큰)를 생성하는 메서드
     */
    @Transactional
    public ScrapShareResponse generateShareLink(UUID userId, UUID scrapId){
        // 유효성 검사
        User user = getValidUser(userId);
        ScrapEntity scrap = getValidScrap(scrapId);
        validateUser(user, scrap);

        Optional<ScrapShareLinkEntity> existingUrl = scrapShareLinkRepository.findByScrapAndIsActiveTrue(scrap);
        if (existingUrl.isPresent()){
            // 공유 중인 링크가 있다면 반환
            return new ScrapShareResponse((buildShareUrl(existingUrl.get().getToken())));
        }

        // 없다면 새로 생성
        String newToken = UUID.randomUUID().toString().replace("-", "");

        ScrapShareLinkEntity entity = ScrapShareLinkEntity.builder()
                .token(newToken)
                .scrap(scrap)
                .build();
        // 추가
        scrapShareLinkRepository.save(entity);

        // 링크 생성 후 반환
        return new ScrapShareResponse(buildShareUrl(newToken));
    }

    // TODO : MVP 끝나면 스크랩 상세 조회 메서드 추가

    // 공유 링크 생성 메서드
    public String buildShareUrl(String token){
        return this.frontEndBaseUrl + token;
    }

    /**
     * 유효성 검사
     */

    // 회원 유효성
    public User getValidUser(UUID userId){
        return userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));
    }

    // 작성자 본인 여부 확인
    public void validateUser(User user, ScrapEntity scrap){
        if (!user.getUserId().equals(scrap.getUser().getUserId())){
            throw new BaseException(ScrapErrorCode.SCRAP_ACCESS_DENIED);
        }
    }

    // 스크랩명 중복 조회
    public void checkScrapValidation(String name, User user){
        boolean isExist = scrapRepository.existsByNameAndUser(name, user);
        if (isExist){
            throw new BaseException(ScrapErrorCode.SCRAP_NAME_DUPLICATED);
        }
    }

    // 스크랩 유효성
    public ScrapEntity getValidScrap(UUID scrapId){
        return scrapRepository.findById(scrapId)
                .orElseThrow(()-> new BaseException(ScrapErrorCode.SCRAP_NOT_FOUND));
    }
}
