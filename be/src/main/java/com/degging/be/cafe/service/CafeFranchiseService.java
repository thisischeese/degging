package com.degging.be.cafe.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * 프랜차이즈 여부를 판단하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeFranchiseService {

    private final CafeRepository cafeRepository;

    /**
     * 프랜차이즈 식별 및 정보 업데이트
     * 사전 정의된 목록 매칭 + 브랜드명 빈도 분석 기반
     */
    @Transactional
    public void updateFranchiseStatus() {
        List<CafeEntity> allCafes = cafeRepository.findAll();

        // 브랜드명 빈도 계산
        Map<String, Integer> brandCountMap = new HashMap<>();
        for (CafeEntity cafe : allCafes) {
            String potentialBrand = extractPotentialBrand(cafe.getName());
            brandCountMap.put(potentialBrand, brandCountMap.getOrDefault(potentialBrand, 0) + 1);
        }

        // 개별 카페 정보 업데이트
        int totalUpdated = 0;
        int threshold = 10; // 동일 브랜드명이 10개 이상이면 프랜차이즈로 간주

        for (CafeEntity cafe : allCafes) {
            String originalName = cafe.getName();
            String matchedPredefined = CafeEntity.getMatchedFranchiseName(originalName);
            String potentialBrand = extractPotentialBrand(originalName);

            boolean isFranchise = (matchedPredefined != null) || (brandCountMap.get(potentialBrand) >= threshold);

            String finalBrandName = potentialBrand;
            if (matchedPredefined != null) {
                finalBrandName = matchedPredefined;
            }

            // 지점명 추출: 원본 상호명에서 최종 브랜드명을 제외한 나머지
            String finalBranchName = extractBranchName(originalName, finalBrandName);

            // 상태가 변했거나 브랜드 정보가 다른 경우 업데이트
            if (cafe.isFranchise() != isFranchise ||
                    !Objects.equals(cafe.getBrandName(), finalBrandName) ||
                    !Objects.equals(cafe.getBranchName(), finalBranchName)) {

                cafe.updateFranchiseInfo(finalBrandName, finalBranchName, isFranchise);
                totalUpdated++;
            }
        }

        log.info("프랜차이즈 업데이트 완료. 총 대상 건수: {}, 업데이트 수행 건수: {}", allCafes.size(), totalUpdated);
    }

    /**
     * 상호명에서 지점 정보를 제거하여 브랜드명 추출
     */
    private String extractPotentialBrand(String name) {
        if (name == null)
            return "";
        // 흔히 사용되는 지점 패턴들 제거
        return name.replaceAll("\\s+\\d*호점$", "")
                .replaceAll("\\s+\\w+점$", "")
                .replaceAll("\\s+\\w+역점$", "")
                .replaceAll("\\s+본점$", "")
                .replaceAll("\\s+본사$", "")
                .replaceAll("\\([^)]*\\)", "") // 괄호 내용 제거 (예: (주), (유) 등)
                .trim();
    }

    /**
     * 원본 상호명에서 브랜드명을 제외한 지점명 추출
     */
    private String extractBranchName(String original, String brand) {
        if (original == null || brand == null || original.equals(brand))
            return null;
        String branch = original.replace(brand, "").trim();
        return branch.isEmpty() ? null : branch;
    }
}