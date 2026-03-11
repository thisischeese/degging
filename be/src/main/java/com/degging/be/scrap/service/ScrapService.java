package com.degging.be.scrap.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.ScrapErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.scrap.dto.request.ScrapRequest;
import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

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
        User user = userRepository.findById(userId)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 스크랩 명 중복 확인
        boolean isExist = scrapRepository.existsByNameAndUser(scrapRequest.getName(), user);
        if (isExist){
            throw new BaseException(ScrapErrorCode.SCRAP_NAME_DUPLICATED);
        }
        
        // Entity 에 name, color 와 user 정보를 담아줌
        ScrapEntity entity = ScrapEntity.builder()
                        .name(scrapRequest.getName())
                        .color(scrapRequest.getColor())
                        .user(user)
                        .build();

        // DB 저장
        scrapRepository.save(entity);
    }
}
