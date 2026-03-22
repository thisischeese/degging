package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.CafeCrawlingDto;
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
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CafeCrawlingService {

    private final CafeRepository cafeRepository;
    private final VibeRepository vibeRepository;
    private final UserRepository userRepository;
    private final ReviewRepository reviewRepository;
    private final EntityManager em;

    /**
     * 전달받은 크롤링 데이터 DB에 반영
     */
    @Transactional
    public void processCrawlingData(List<CafeCrawlingDto> dataList) {
        log.info("Starting bulk update for {} crawled cafes...", dataList.size());

        for (CafeCrawlingDto dto : dataList) {
            try {
                updateSingleCafe(dto);
            } catch (Exception e) {
                log.error("Error updating cafe {}: {}", dto.getCafeId(), e.getMessage());
            }
        }

        log.info("Finished processing crawling data.");
    }

    private void updateSingleCafe(CafeCrawlingDto dto) {
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

        // 기본 정보 업데이트
        cafe.updateCrawledData(
                dto.getCafes().getThumbnailUrl(),
                dto.getCafes().getCafeIntro());

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
                    dto.getCafeBusinessHours().getThursHours(),
                    dto.getCafeBusinessHours().getFriHours(),
                    dto.getCafeBusinessHours().getSatHours(),
                    dto.getCafeBusinessHours().getSunHours());
        }

        // 카페 이미지 업데이트 (기존 데이터 일괄 삭제 후 추가 - OrphanRemoval 작동)
        if (dto.getCafeImages() != null) {
            cafe.getImages().clear();
            for (CafeCrawlingDto.CafeImageDto imgDto : dto.getCafeImages()) {
                CafeImageEntity img = CafeImageEntity.builder()
                        .cafe(cafe)
                        .imageUrl(imgDto.getImageUrl())
                        .sortOrder(imgDto.getSortOrder() != null ? imgDto.getSortOrder() : 0)
                        .build();
                cafe.getImages().add(img);
            }
        }

        // 카페 메뉴 업데이트 (기존 데이터 일괄 삭제 후 추가)
        if (dto.getCafeMenus() != null) {
            cafe.getMenus().clear();
            for (CafeCrawlingDto.CafeMenuDto menuDto : dto.getCafeMenus()) {
                CafeMenuEntity menu = CafeMenuEntity.builder()
                        .cafe(cafe)
                        .menuName(menuDto.getMenuName())
                        .price(menuDto.getPrice())
                        .menuDescription(menuDto.getMenuDescription())
                        .build();
                cafe.getMenus().add(menu);
            }
        }

        // 카페 분위기 태그 업데이트 (기존 데이터 일괄 삭제 후 추가)
        if (dto.getCafeVibeTags() != null) {
            cafe.getVibeTags().clear();
            for (CafeCrawlingDto.CafeVibeTagDto tagDto : dto.getCafeVibeTags()) {
                if (tagDto.getTagId() != null) {
                    VibeEntity vibe = vibeRepository.findById(tagDto.getTagId()).orElse(null);
                    if (vibe != null) {
                        CafeVibeTagEntity vibeTag = CafeVibeTagEntity.builder()
                                .cafe(cafe)
                                .vibe(vibe)
                                .build();
                        cafe.getVibeTags().add(vibeTag);
                    }
                }
            }
        }

        // 콜드스타트용 리뷰 데이터 업데이트
        if (dto.getCafeReviews() != null && !dto.getCafeReviews().isEmpty()) {

            // 기존 크롤링된 리뷰 삭제 (내부 회원 리뷰 보호) - email prefix로 식별
            List<ReviewEntity> oldReviews = em.createQuery(
                    "SELECT r FROM ReviewEntity r WHERE r.cafe = :cafe AND r.user.email LIKE 'crawler_%'",
                    ReviewEntity.class)
                    .setParameter("cafe", cafe)
                    .getResultList();
            reviewRepository.deleteAll(oldReviews);

            // 새 크롤링 리뷰 저장
            for (CafeCrawlingDto.CafeReviewDto reviewDto : dto.getCafeReviews()) {
                if (reviewDto.getUserId() == null || reviewDto.getContent() == null)
                    continue;

                String dummyEmail = "crawler_" + reviewDto.getUserId().toString() + "@degging.com";

                UserEntity dummyUser = userRepository.findByEmail(dummyEmail).orElseGet(() -> {
                    // 유저 엔티티 생성
                    UserEntity newUser = UserEntity.of(dummyEmail, "dummy_crawler_password", 'A');

                    // 유저 프로필 생성 (닉네임 중복 및 NULL 방지 위해 랜덤 8자리 부여)
                    String shortUuid = reviewDto.getUserId().toString().substring(0, 8);
                    UserProfileEntity profile = UserProfileEntity.builder()
                            .user(newUser)
                            .nickname("크롤러_" + shortUuid)
                            .gender(Gender.MALE) // 더미 성별
                            .birthDate(LocalDate.of(2000, 1, 1)) // 더미 생년월일
                            .build();

                    newUser.setProfile(profile);
                    return userRepository.save(newUser); // 연관된 프로필도 Cascade 처리됨
                });

                ReviewEntity newReview = ReviewEntity.builder()
                        .cafe(cafe)
                        .user(dummyUser)
                        .rating(reviewDto.getRating() != null ? reviewDto.getRating() : 5)
                        .content(reviewDto.getContent())
                        .build();

                reviewRepository.save(newReview);
            }
        }

        // 현재 처리중인 카페의 영속성 컨텍스트를 DB에 쏘고 비워 OOM 방지
        em.flush();
        em.clear();
    }
}
