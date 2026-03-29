package com.degging.be.user.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.infra.ai.AiClient;
import com.degging.be.user.dto.request.AiOnboardingRequest;
import com.degging.be.user.dto.request.UserOnboardingRequest;
import com.degging.be.user.dto.response.AiOnboardingResponse;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserProfileEntity;
import com.degging.be.user.entity.mongodb.UserOnboarding;
import com.degging.be.user.repository.UserProfileRepository;
import com.degging.be.user.repository.UserRepository;
import com.degging.be.user.repository.mongodb.UserOnboardingRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserOnboardingService {

    private final CafeRepository cafeRepository;
    private final UserOnboardingRepository onboardingRepository;
    private final UserRepository userRepository;
    private final UserProfileRepository userProfileRepository;
    private final AiClient aiClient;

    /**
     * 사용자의 온보딩 설문 결과를 분석하고 취향 데이터를 저장합니다.
     *
     * @param userId  유저 식별자
     * @param request 온보딩 요청 데이터
     */
    public void processOnboarding(UUID userId, UserOnboardingRequest request) {
        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));
        UserProfileEntity profile = userProfileRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 선택된 카페 및 분위기 태그 조회
        List<CafeEntity> cafes = cafeRepository.findAllWithVibesById(request.getCafeIds());

        // 분위기 태그 빈도 분석
        Map<String, Integer> preferredTags = analyzePreferredTags(cafes);

        // MongoDB 도큐먼트 생성
        UserOnboarding onboarding = UserOnboarding.of(
                userId,
                preferredTags,
                request.getCafeIds(),
                request.getMenuNames());

        // MongoDB에 최종 적재
        onboardingRepository.save(onboarding);

        // userEntity 온보딩 컬럼 업데이트
        profile.updateIsOnboarding();

        // AI 서버에 온보딩 결과 전송
        notifyAiServer(user, profile, request, cafes);
    }

    /**
     * AI 서버에 온보딩 결과 전송
     * AI 서버 호출 실패 시 예외를 전파하지 않고 로그만 기록
     *
     * @param userId  유저 식별자
     * @param request 온보딩 요청 데이터
     */
    private void notifyAiServer(UserEntity user, UserProfileEntity profile,
                               UserOnboardingRequest request, List<CafeEntity> cafes) {
        try {
            // 선택된 카페들의 분위기 태그 이름 수집 (중복 제거)
            List<String> moodTagNames = cafes.stream()
                    .flatMap(cafe -> cafe.getVibeTags().stream())
                    .map(cafeVibeTag -> cafeVibeTag.getVibe().getTagName())
                    .distinct()
                    .toList();

            AiOnboardingRequest aiRequest = AiOnboardingRequest.of(
                    user.getUserId(),
                    profile.getNickname(),
                    user.getEmail(),
                    request.getMenuNames(),
                    moodTagNames,
                    request.getCafeIds());

            AiOnboardingResponse response = aiClient.sendOnboarding(aiRequest);

            if (response == null || !response.isSuccess()) {
                log.warn("AI 서버 온보딩 처리 실패 또는 응답 없음 (user_id: {})", user.getUserId());
            } else {
                log.info("AI 서버 온보딩 처리 완료 (user_id: {}, updated_at: {})",
                        user.getUserId(), response.getData() != null ? response.getData().getUpdated_at() : "N/A");
            }
        } catch (Exception e) {
            log.error("AI 서버 온보딩 요청 중 예외 발생 (user_id: {}): {}", user.getUserId(), e.getMessage());
        }
    }

    /**
     * 선택된 카페들의 분위기 태그 식별자를 수집하고 빈도수 계산
     *
     * @param cafes 사용자가 선택한 카페 엔티티 목록
     * @return 태그 식별자별 중복 횟수를 담은 맵
     */
    private Map<String, Integer> analyzePreferredTags(List<CafeEntity> cafes) {
        return cafes.stream()
                .flatMap(cafe -> cafe.getVibeTags().stream())
                .map(cafeVibeTag -> cafeVibeTag.getVibe().getTagId())
                .collect(Collectors.groupingBy(UUID::toString, Collectors.summingInt(id -> 1)));
    }

}
