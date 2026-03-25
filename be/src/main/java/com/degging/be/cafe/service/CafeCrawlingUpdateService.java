package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.external.AiCrawlerItemResponse;
import com.degging.be.cafe.entity.*;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.cafe.repository.VibeRepository;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.repository.ReviewRepository;
import com.degging.be.user.entity.Gender;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserProfileEntity;
import com.degging.be.user.repository.UserRepository;
import jakarta.persistence.EntityManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CafeCrawlingUpdateService {

    private final CafeRepository cafeRepository;
    private final VibeRepository vibeRepository;
    private final UserRepository userRepository;
    private final ReviewRepository reviewRepository;
    private final EntityManager em;

    @Transactional
    public void updateSingleCafe(AiCrawlerItemResponse dto) {
        if (dto.getCafes() == null || dto.getCafes().getCafeId() == null) {
            log.warn("CafeId is missing. Skipping...");
            return;
        }

        UUID cafeId;
        try {
            cafeId = UUID.fromString(dto.getCafes().getCafeId());
        } catch (IllegalArgumentException e) {
            log.warn("Invalid CafeId format: {}", dto.getCafes().getCafeId());
            return;
        }

        CafeEntity cafe = cafeRepository.findById(cafeId).orElse(null);
        if (cafe == null) {
            log.warn("Cafe not found in DB: {}", cafeId);
            return;
        }

        // 기본 정보 업데이트 (전제: 현재 비어있음)
        cafe.updateCrawledData(
                dto.getCafes().getThumbnailUrl(),
                dto.getCafes().getCafeIntro());
        log.info("기본 정보 업데이트 완료 (thumbnail: {}, intro: {})",
                cafe.getThumbnailUrl() != null ? "O" : "X",
                cafe.getCafeIntro() != null ? "O" : "X");

        // 평점 통계 정보 (CafeRatingStatsEntity) 업데이트
        if (dto.getCafeRatingStats() != null) {
            CafeRatingStatsEntity stats = cafe.getRatingStats();
            if (stats == null) {
                stats = CafeRatingStatsEntity.from(cafe);
                em.persist(stats);
            }
            stats.updateCrawledStats(
                    dto.getCafeRatingStats().getReviewCount() != null ? dto.getCafeRatingStats().getReviewCount() : 0,
                    dto.getCafeRatingStats().getSoloRatio(),
                    dto.getCafeRatingStats().getDateRatio(),
                    dto.getCafeRatingStats().getFriendsRatio());
        }

        // 영업 시간 (CafeBusinessHoursEntity) 업데이트
        if (dto.getCafeBusinessHours() != null) {
            CafeBusinessHoursEntity hours = cafe.getBusinessHoursEntity();
            if (hours == null) {
                hours = CafeBusinessHoursEntity.builder()
                        .cafeId(cafe.getCafeId())
                        .cafe(cafe)
                        .build();
                em.persist(hours);
            }
            hours.updateCrawledHours(
                    dto.getCafeBusinessHours().getMonHours(),
                    dto.getCafeBusinessHours().getTuesHours(),
                    dto.getCafeBusinessHours().getWedHours(),
                    dto.getCafeBusinessHours().getThurHours(),
                    dto.getCafeBusinessHours().getFriHours(),
                    dto.getCafeBusinessHours().getSatHours(),
                    dto.getCafeBusinessHours().getSunHours());
        }

        // 카페 이미지 추가 (전제: 현재 비어있음)
        if (dto.getCafeImages() != null && !dto.getCafeImages().isEmpty()) {
            for (AiCrawlerItemResponse.CafeImageDto imgDto : dto.getCafeImages()) {
                CafeImageEntity img = CafeImageEntity.builder()
                        .cafe(cafe)
                        .imageUrl(imgDto.getImageUrl())
                        .sortOrder(imgDto.getSortOrder() != null ? imgDto.getSortOrder() : 0)
                        .build();
                cafe.getImages().add(img);
            }
            log.info("이미지 {}건 추가", dto.getCafeImages().size());
        }

        // 카페 메뉴 추가 (전제: 현재 비어있음)
        if (dto.getCafeMenus() != null && !dto.getCafeMenus().isEmpty()) {
            for (AiCrawlerItemResponse.CafeMenuDto menuDto : dto.getCafeMenus()) {
                CafeMenuEntity menu = CafeMenuEntity.builder()
                        .cafe(cafe)
                        .menuName(menuDto.getMenuName())
                        .price(menuDto.getPrice())
                        .menuDescription(menuDto.getMenuDescription())
                        .build();
                cafe.getMenus().add(menu);
            }
            log.info("메뉴 {}건 추가", dto.getCafeMenus().size());
        }

        // 카페 분위기 태그 추가 (전제: 현재 비어있음)
        if (dto.getCafeVibeTags() != null && !dto.getCafeVibeTags().isEmpty()) {
            
            // 이번 카페에서 필요한 태그 ID 목록 수집
            Set<UUID> targetVibeIds = dto.getCafeVibeTags().stream()
                    .map(AiCrawlerItemResponse.CafeVibeTagDto::getTagId)
                    .filter(id -> id != null)
                    .collect(Collectors.toSet());

            if (!targetVibeIds.isEmpty()) {
                // 태그 정보 한꺼번에 조회
                List<VibeEntity> vibes = vibeRepository.findAllById(targetVibeIds);

                for (VibeEntity vibe : vibes) {
                    CafeVibeTagEntity vibeTag = CafeVibeTagEntity.builder()
                            .cafe(cafe)
                            .vibe(vibe)
                            .build();
                    cafe.getVibeTags().add(vibeTag);
                }
                log.info("분위기 태그 {}건 추가", vibes.size());
            }
        }

        // 콜드스타트용 리뷰 데이터 업데이트 (벌크 처리)
        if (dto.getCafeReviews() != null && !dto.getCafeReviews().isEmpty()) {

            // 이번 카페의 모든 리뷰어 정보 수집 (이메일 맵핑)
            Map<String, AiCrawlerItemResponse.CafeReviewDto> reviewDtoMap = new HashMap<>();
            for (AiCrawlerItemResponse.CafeReviewDto reviewDto : dto.getCafeReviews()) {
                if (reviewDto.getUserId() != null && reviewDto.getUserReview() != null) {
                    String dummyEmail = "crawler_" + reviewDto.getUserId() + "@degging.com";
                    reviewDtoMap.put(dummyEmail, reviewDto);
                }
            }

            if (reviewDtoMap.isEmpty())
                return;

            // 이미 존재하는 유저들을 한꺼번에 조회 (N+1 방지)
            List<UserEntity> existingUsers = userRepository.findAllByEmailIn(reviewDtoMap.keySet());
            Map<String, UserEntity> userCache = existingUsers.stream()
                    .collect(Collectors.toMap(UserEntity::getEmail, u -> u));

            // DB에 없는 유저들을 미리 생성하여 한꺼번에 저장
            List<UserEntity> newUsersToSave = new ArrayList<>();
            for (String email : reviewDtoMap.keySet()) {
                if (!userCache.containsKey(email)) {
                    AiCrawlerItemResponse.CafeReviewDto reviewDto = reviewDtoMap.get(email);

                    UserEntity newUser = UserEntity.of(email, "dummy_crawler_password", 'A');
                    String shortUuid = reviewDto.getUserId().toString().substring(0, 8);

                    UserProfileEntity profile = UserProfileEntity.builder()
                            .user(newUser)
                            .nickname("크롤러_" + shortUuid)
                            .gender(Gender.MALE)
                            .birthDate(LocalDate.of(2000, 1, 1))
                            .build();

                    newUser.setProfile(profile);
                    newUsersToSave.add(newUser);
                }
            }

            if (!newUsersToSave.isEmpty()) {
                List<UserEntity> savedNewUsers = userRepository.saveAll(newUsersToSave);
                for (UserEntity u : savedNewUsers) {
                    userCache.put(u.getEmail(), u);
                }
            }

            // 5. 모든 리뷰 엔티티를 생성하여 한꺼번에 저장
            List<ReviewEntity> reviewsToSave = new ArrayList<>();
            for (String email : reviewDtoMap.keySet()) {
                UserEntity user = userCache.get(email);
                AiCrawlerItemResponse.CafeReviewDto reviewDto = reviewDtoMap.get(email);

                ReviewEntity newReview = ReviewEntity.builder()
                        .cafe(cafe)
                        .user(user)
                        .rating(reviewDto.getRating() != null ? reviewDto.getRating() : (short) 5)
                        .content(reviewDto.getUserReview())
                        .build();

                reviewsToSave.add(newReview);
            }

            reviewRepository.saveAll(reviewsToSave);
            log.info("리뷰 {}건 저장 완료", reviewsToSave.size());
        }

        // 최종 반영 (더티 체킹 보완을 위해 명시적 호출)
        cafeRepository.save(cafe);
        log.info("카페 ID: {} 최종 저장 완료", cafeId);
    }
}
