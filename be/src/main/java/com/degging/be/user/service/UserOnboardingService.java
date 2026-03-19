package com.degging.be.user.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.user.dto.request.UserOnboardingRequest;
import com.degging.be.user.entity.mongodb.UserOnboarding;
import com.degging.be.user.repository.mongodb.UserOnboardingRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class UserOnboardingService {

    private final CafeRepository cafeRepository;
    private final UserOnboardingRepository onboardingRepository;

    /**
     * 사용자의 온보딩 설문 결과를 분석하고 취향 데이터를 저장합니다.
     *
     * @param userId 유저 식별자
     * @param request 온보딩 요청 데이터
     */
    public void processOnboarding(UUID userId, UserOnboardingRequest request) {
        // 분위기 태그 빈도 분석
        Map<UUID, Integer> preferredTags = analyzePreferredTags(request.getCafeIds());

        // MongoDB 도큐먼트 생성
        UserOnboarding onboarding = UserOnboarding.of(
                userId,
                preferredTags,
                request.getCafeIds(),
                request.getMenuIds());

        // MongoDB에 최종 적재
        onboardingRepository.save(onboarding);
    }

    /**
     * 선택된 카페들의 분위기 태그 식별자를 수집하고 빈도수 계산
     *
     * @param cafeIds 사용자가 선택한 카페 식별자 목록
     * @return 태그 식별자별 중복 횟수를 담은 맵
     */
    private Map<UUID, Integer> analyzePreferredTags(List<UUID> cafeIds) {

        // 해당 카페가 가지고 있는 분위기 태그 전부 가져옴
        List<CafeEntity> cafes = cafeRepository.findAllWithVibesById(cafeIds);

        return cafes.stream()
                .flatMap(cafe -> cafe.getVibeTags().stream())
                .map(cafeVibeTag -> cafeVibeTag.getVibe().getTagId())
                .collect(Collectors.groupingBy(tagId -> tagId, Collectors.summingInt(id -> 1)));
    }

}
