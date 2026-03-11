package com.degging.be.scrap.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.ScrapErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.dto.response.ScrapCafeResponse;
import com.degging.be.scrap.dto.response.ScrapDetailResponse;
import com.degging.be.scrap.dto.response.ScrapResponse;
import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * 카페 스크랩을 관리하는 서비스 클래스
 */
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
    @Transactional(readOnly = true)
    public List<ScrapResponse> getScrapsByUserId(UUID userId) {
        // user 검증
        User user = getValidUser(userId);
        
        // 스크랩 목록 조회
        List<ScrapEntity> entities = scrapRepository.findAllByUserUserId(user);
        
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

        // scrap 과 cafe 조회
        ScrapEntity scrap = scrapRepository.findByIdWithCafes(scrapId)
                .orElseThrow(()-> new BaseException(ScrapErrorCode.SCRAP_NOT_FOUND));

        // 반환 객체인 ScrapDetailResponse 에 맞게 담아줌
        // TODO : 썸네일을 어떤 식으로 할지 확인 후 진행
        List<ScrapCafeResponse> cafes = scrap.getScrapItems().stream()
                .map(item -> ScrapCafeResponse.builder()
                        .cafeId(item.getCafe().getCafeId())
                        .name(item.getCafe().getName())
                        .thumbnailUrl("")
                        .cafeIntro(item.getCafe().getCafeIntro())
                        .build()
                ).toList();
        return null;
    }

    /**
     * 유효성 검사
     */

    // 회원 유효성
    public User getValidUser(UUID userId){
        return userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));
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
