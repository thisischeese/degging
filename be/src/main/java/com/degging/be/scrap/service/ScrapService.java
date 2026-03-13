package com.degging.be.scrap.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.ScrapErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.dto.response.ScrapCafeResponse;
import com.degging.be.scrap.dto.response.ScrapDetailResponse;
import com.degging.be.scrap.dto.response.ScrapResponse;
import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.entity.ScrapItemEntity;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * 카페 스크랩을 관리하는 서비스 클래스
 */
@Transactional(readOnly = true)
@Service
@RequiredArgsConstructor
public class ScrapService {
    private final ScrapRepository scrapRepository;
    private final UserRepository userRepository;

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
        
        // 스크랩 목록 조회
        List<ScrapEntity> entities = scrapRepository.findAllByUserUserId(userId);
        
        // List<Entity> -> List<Dto> 로 반환
        return entities.stream()
                .map(ScrapResponse::toDto)
                .toList();
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
