package com.degging.be.cafe.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 프랜차이즈 여부를 판단하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeFranchiseService {

    private final CafeRepository cafeRepository;

    /**
     * 동일 브랜드명이 10개 이상인 카페를 찾아 프랜차이즈로 일괄 업데이트
     */
    @Transactional
    public void updateFranchiseStatus() {
        // 10개 이상 중복된 브랜드명 리스트 조회
        List<String> franchiseBrands = cafeRepository.findBrandNamesExceedingThreshold();

        int totalUpdated = 0;

        // 해당 브랜드명을 가진 카페들의 franchise 필드 업데이트
        for (String brand : franchiseBrands) {
            List<CafeEntity> cafes = cafeRepository.findAllByBrandName(brand);
            for (CafeEntity cafe : cafes) {
                // 이미 true인 경우 중복 업데이트 방지
                if (!cafe.isFranchise()) {
                    cafe.updateFranchise(true);
                    totalUpdated++;
                }
            }
        }

        log.info("프랜차이즈 업데이트 완료. 업데이트된 총 카페 수: {}", totalUpdated);
    }
}