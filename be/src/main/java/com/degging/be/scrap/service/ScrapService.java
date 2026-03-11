package com.degging.be.scrap.service;

import com.degging.be.scrap.dto.request.ScrapRequset;
import com.degging.be.scrap.repository.ScrapRepository;
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

    /**
     * 스크랩 폴더 생성하는 메서드 
     */
    public void createScrap(ScrapRequset scrapRequset, UUID userId) {
    
    }
}
