package com.degging.be.scrap.service;

import com.degging.be.scrap.repository.ScrapRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * 카페 스크랩을 관리하는 서비스 클래스
 */
@Service
@RequiredArgsConstructor
public class ScrapService {
    private final ScrapRepository scrapRepository;
}
