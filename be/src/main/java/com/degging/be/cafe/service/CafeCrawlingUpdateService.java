package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.external.AiCrawlerItemResponse;
import com.degging.be.cafe.entity.*;
import com.degging.be.cafe.repository.*;
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
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CafeCrawlingUpdateService {

    private static final List<String> ADJECTIVES = List.of("맑은", "고운", "푸른", "깊은", "밝은", "기쁜", "멋진", "착한", "숲속", "새벽");
    private static final List<String> NOUNS = List.of("하늘", "바다", "나무", "요정", "라떼", "하루", "소망", "미소", "햇살", "구름");

    private final CafeRepository cafeRepository;
    private final VibeRepository vibeRepository;
    private final UserRepository userRepository;
    private final ReviewRepository reviewRepository;
    private final EntityManager em;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateSingleCafe(AiCrawlerItemResponse dto) {
        if (dto.getCafes() == null || dto.getCafes().getCafeId() == null) {
            log.warn("카페 ID가 누락되었습니다. 해당 항목을 건너뜁니다.");
            return;
        }

        UUID cafeId;
        try {
            cafeId = UUID.fromString(dto.getCafes().getCafeId());
        } catch (IllegalArgumentException e) {
            log.warn("잘못된 카페 ID 형식: {}", dto.getCafes().getCafeId());
            return;
        }

        CafeEntity cafe = cafeRepository.findById(cafeId).orElse(null);
        if (cafe == null) {
            log.warn("DB에서 카페를 찾을 수 없습니다: {}", cafeId);
            return;
        }

        // 기본 정보 업데이트 (전제: 현재 비어있음)
        String intro = dto.getCafes().getCafeIntro();
        if (intro != null && intro.length() > 495) {
            intro = intro.substring(0, 495);
        }

        cafe.updateCrawledData(
                dto.getCafes().getThumbnailUrl(),
                intro);
        log.info("기본 정보 업데이트 완료 (thumbnail: {}, intro: {})",
                cafe.getThumbnailUrl() != null ? "O" : "X",
                cafe.getCafeIntro() != null ? "O" : "X");

        // 평점 통계 정보 (CafeRatingStatsEntity) 업데이트
        if (dto.getCafeRatingStats() != null) {
            CafeRatingStatsEntity stats = cafe.getRatingStats();
            if (stats == null) {
                stats = CafeRatingStatsEntity.from(cafe);
                cafe.setRatingStats(stats); // 양방향 연관관계 설정
                em.persist(stats);
            }
            stats.updateCrawledStats(
                    dto.getCafeRatingStats().getReviewCount() != null ? dto.getCafeRatingStats().getReviewCount() : 0,
                    dto.getCafeRatingStats().getRatingSum() != null ? dto.getCafeRatingStats().getRatingSum() : 0,
                    dto.getCafeRatingStats().getSoloRatio(),
                    dto.getCafeRatingStats().getDateRatio(),
                    dto.getCafeRatingStats().getFriendsRatio());
        }

        // 영업 시간 (CafeBusinessHoursEntity) 업데이트
        if (dto.getCafeBusinessHours() != null) {
            CafeBusinessHoursEntity hours = cafe.getBusinessHoursEntity();
            AiCrawlerItemResponse.CafeBusinessHoursDto hDto = dto.getCafeBusinessHours();
            
            if (hours == null) {
                hours = CafeBusinessHoursEntity.builder()
                        .cafe(cafe)
                        .monHours(hDto.getMonHours())
                        .tuesHours(hDto.getTuesHours())
                        .wedHours(hDto.getWedHours())
                        .thurHours(hDto.getThurHours())
                        .friHours(hDto.getFriHours())
                        .satHours(hDto.getSatHours())
                        .sunHours(hDto.getSunHours())
                        .build();
                cafe.setBusinessHoursEntity(hours);
                em.persist(hours);
            } else {
                hours.updateCrawledHours(
                        hDto.getMonHours(), hDto.getTuesHours(), hDto.getWedHours(),
                        hDto.getThurHours(), hDto.getFriHours(), hDto.getSatHours(), hDto.getSunHours());
            }
            log.info("영업 시간 업데이트 완료");
        }

        // 카페 이미지 업데이트
        if (dto.getCafeImages() != null && !dto.getCafeImages().isEmpty()) {
            cafe.getImages().clear(); // orphanRemoval=true로 인해 전파됨
            
            for (AiCrawlerItemResponse.CafeImageDto imgDto : dto.getCafeImages()) {
                CafeImageEntity image = CafeImageEntity.builder()
                        .cafe(cafe)
                        .imageUrl(imgDto.getImageUrl())
                        .sortOrder(imgDto.getSortOrder() != null ? imgDto.getSortOrder() : 0)
                        .build();
                cafe.getImages().add(image);
            }
            log.info("이미지 {}건 추가", dto.getCafeImages().size());
        }

        // 카페 메뉴 업데이트
        if (dto.getCafeMenus() != null && !dto.getCafeMenus().isEmpty()) {
            cafe.getMenus().clear(); // orphanRemoval=true로 인해 전파됨
            
            for (AiCrawlerItemResponse.CafeMenuDto menuDto : dto.getCafeMenus()) {
                String desc = menuDto.getMenuDescription();
                if (desc != null && desc.length() > 495) {
                    desc = desc.substring(0, 495);
                }
                String name = menuDto.getMenuName();
                if (name != null && name.length() > 95) {
                    name = name.substring(0, 95);
                }
                
                CafeMenuEntity menu = CafeMenuEntity.builder()
                        .cafe(cafe)
                        .menuName(name)
                        .menuImageUrl(menuDto.getMenuImgUrl())
                        .price(menuDto.getPrice())
                        .menuDescription(desc)
                        .build();
                cafe.getMenus().add(menu);
            }
            log.info("메뉴 {}건 추가", dto.getCafeMenus().size());
        }

        // 카페 분위기 태그 업데이트
        if (dto.getCafeVibeTags() != null && !dto.getCafeVibeTags().isEmpty()) {
            cafe.getVibeTags().clear(); // 기존 태그 관계 삭제 (orphanRemoval)
            
            Set<UUID> targetVibeIds = dto.getCafeVibeTags().stream()
                    .map(AiCrawlerItemResponse.CafeVibeTagDto::getTagId)
                    .filter(Objects::nonNull)
                    .collect(Collectors.toSet());

            if (!targetVibeIds.isEmpty()) {
                List<VibeEntity> vibes = vibeRepository.findAllById(targetVibeIds);
                for (VibeEntity vibe : vibes) {
                    CafeVibeTagEntity tag = CafeVibeTagEntity.builder()
                            .cafe(cafe)
                            .vibe(vibe)
                            .build();
                    cafe.getVibeTags().add(tag);
                }
            }
            log.info("분위기 태그 {}건 추가", cafe.getVibeTags().size());
        }

        // 콜드스타트용 리뷰 데이터 업데이트
        if (dto.getCafeReviews() != null && !dto.getCafeReviews().isEmpty()) {
            try {
                // 이번 카페의 모든 리뷰어 정보 수집 (이메일 맵핑)
                Map<String, AiCrawlerItemResponse.CafeReviewDto> reviewDtoMap = new HashMap<>();
                for (AiCrawlerItemResponse.CafeReviewDto reviewDto : dto.getCafeReviews()) {
                    if (reviewDto.getUserId() != null && reviewDto.getUserReview() != null) {
                        String userIdStr = reviewDto.getUserId();
                        String emailId = userIdStr.substring(0, Math.min(userIdStr.length(), 20));
                        String dummyEmail = "crawler_" + emailId + "@degging.com";
                        reviewDtoMap.put(dummyEmail, reviewDto);
                    }
                }

                if (!reviewDtoMap.isEmpty()) {
                    // 이미 존재하는 유저들을 한꺼번에 조회 (N+1 방지)
                    List<UserEntity> existingUsers = userRepository.findAllByEmailIn(reviewDtoMap.keySet());
                    Map<String, UserEntity> userCache = existingUsers.stream()
                            .collect(Collectors.toMap(UserEntity::getEmail, u -> u));

                    // DB에 없는 유저들을 미리 생성하여 한꺼번에 저장
                    List<UserEntity> newUsersToSave = new ArrayList<>();
                    for (String email : reviewDtoMap.keySet()) {
                        if (!userCache.containsKey(email)) {
                            UserEntity newUser = UserEntity.of(email, "dummy_crawler_password", 'A');
                            
                            // 자연스러운 닉네임 생성 로직 (2자 + 2자 + 6자 = 총 10자)
                            int adjIndex = Math.abs(email.hashCode()) % ADJECTIVES.size();
                            int nounIndex = Math.abs((email + "seed").hashCode()) % NOUNS.size();
                            
                            // email: crawler_{emailId}@degging.com 에서 emailId 부분 6자리 추출
                            String idPart = email.substring(8, email.indexOf("@"));
                            String suffix = idPart.substring(0, Math.min(idPart.length(), 6)); 
                            String naturalNickname = ADJECTIVES.get(adjIndex) + NOUNS.get(nounIndex) + suffix;

                            UserProfileEntity profile = UserProfileEntity.builder()
                                    .user(newUser)
                                    .nickname(naturalNickname)
                                    .gender(Gender.MALE)
                                    .birthDate(LocalDate.of(2000, 1, 1))
                                    .build();

                            newUser.setProfile(profile);
                            newUsersToSave.add(newUser);
                        }
                    }

                    if (!newUsersToSave.isEmpty()) {
                        try {
                            List<UserEntity> savedNewUsers = userRepository.saveAll(newUsersToSave);
                            for (UserEntity u : savedNewUsers) {
                                userCache.put(u.getEmail(), u);
                            }
                        } catch (Exception e) {
                            log.warn("일부 신규 유저 저장 중 오류 발생 (이미 생성되었을 수 있음): {}", e.getMessage());
                            // 개별 조회하여 다시 캐시 구성 (충돌 방지)
                            for (String email : reviewDtoMap.keySet()) {
                                if (!userCache.containsKey(email)) {
                                    userRepository.findByEmail(email).ifPresent(u -> userCache.put(email, u));
                                }
                            }
                        }
                    }

                    // 모든 리뷰 엔티티를 생성하여 한꺼번에 저장
                    List<ReviewEntity> reviewsToSave = new ArrayList<>();
                    for (String email : reviewDtoMap.keySet()) {
                        UserEntity user = userCache.get(email);
                        if (user == null) continue;

                        AiCrawlerItemResponse.CafeReviewDto reviewDto = reviewDtoMap.get(email);
                        ReviewEntity newReview = ReviewEntity.builder()
                                .cafe(cafe)
                                .user(user)
                                .rating(reviewDto.getRating() != null ? reviewDto.getRating() : (short) 5)
                                .content(reviewDto.getUserReview())
                                .build();

                        reviewsToSave.add(newReview);
                    }

                    if (!reviewsToSave.isEmpty()) {
                        reviewRepository.saveAll(reviewsToSave);
                        log.info("리뷰 {}건 저장 완료", reviewsToSave.size());
                    }
                }
            } catch (Exception e) {
                // 리뷰 저장 실패는 전체 카페 정보 업데이트를 중단시키지 않음
                log.error("리뷰 데이터 처리 중 예외 발생 (카페 ID: {}): {}", cafeId, e.getMessage());
            }
        }

        // 최종 반영 (더티 체킹 보완을 위해 명시적 호출)
        cafeRepository.save(cafe);
        log.info("카페 ID: {} 최종 저장 완료", cafeId);
    }
}
