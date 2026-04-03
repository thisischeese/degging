package com.degging.be.discovery.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.discovery.dto.response.DiscoveryResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.infra.ai.AiClient;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserPreferenceEntity;
import com.degging.be.user.repository.UserPreferenceRepository;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Slice;
import org.springframework.data.domain.SliceImpl;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DiscoveryService {

    private final CafeRepository cafeRepository;
    private final UserPreferenceRepository userPreferenceRepository;
    private final UserRepository userRepository;
    private final AiClient aiClient;

    /**
     * 무한 스크롤 지원: 개인화 추천 및 일일 고정 랜덤 리스트 반환
     * 
     * @param page 페이지 번호
     * @param size 페이지 당 썸네일 수
     * @param userId 유저 식별자
     * @return 일일 랜덤 카페 썸네일 무한스크롤 데이터(Slice)
     */
    public Slice<DiscoveryResponse> getDailyDiscoveryCafes(int page, int size, UUID userId) {
        
        // 사용자 유효성 체크 및 그룹 확인
        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));
        
        String abGroup = user.getAbGroup() != null ? String.valueOf(user.getAbGroup()) : "A";

        // 그룹 B인 경우 AI 호출을 건너뛰고 바로 랜덤 추천 반환
        if ("B".equals(abGroup)) {
            return getRandomDiscoveryCafes(page, size, abGroup);
        }

        // 취향 정보(벡터 또는 태그)가 존재하면 AI 추천 요청
        Optional<UserPreferenceEntity> preference = userPreferenceRepository.findById(userId);
        if (preference.isPresent()) {
            Map<UUID, Integer> recommendations = aiClient.getDiscoveryRecommendations(userId);
            
            // AI 응답이 있으면 해당 카페들 정렬하여 반환
            if (recommendations != null && !recommendations.isEmpty()) {
                List<UUID> cafeIds = new ArrayList<>(recommendations.keySet());
                List<CafeEntity> cafes = cafeRepository.findAllByCafeIdIn(cafeIds);
                return getSortedSlice(cafes, recommendations, page, size, abGroup);
            }
        }

        // 취향 벡터가 없거나 AI 서버 오류 시 일일 랜덤 추천으로 폴백
        return getRandomDiscoveryCafes(page, size, abGroup);
    }

    /**
     * AI 순위(Integer) 기준 정렬 및 Slice 변환
     * 
     * @param cafes 카페 엔티티 리스트
     * @param rankMap 카페 ID와 순위를 담은 맵
     * @param page 페이지 번호
     * @param size 페이지 당 썸네일 수
     * @param abGroup A/B 테스트 그룹
     * @return 정렬된 카페 썸네일 무한스크롤 데이터(Slice)
     */
    private Slice<DiscoveryResponse> getSortedSlice(List<CafeEntity> cafes, Map<UUID, Integer> rankMap, int page, int size, String abGroup) {
        List<DiscoveryResponse> sortedContent = cafes.stream()
                .sorted(Comparator.comparingInt(c -> rankMap.getOrDefault(c.getCafeId(), 999)))
                .map(cafe -> DiscoveryResponse.from(cafe, abGroup))
                .collect(Collectors.toList());

        return getSliceFromList(sortedContent, page, size);
    }

    /**
     * 일일 고정 시드 기반 랜덤 추천 (Top 500)
     * 
     * @param page 페이지 번호
     * @param size 페이지 당 썸네일 수
     * @param abGroup A/B 테스트 그룹
     * @return 랜덤 카페 썸네일 무한스크롤 데이터(Slice)
     */
    private Slice<DiscoveryResponse> getRandomDiscoveryCafes(int page, int size, String abGroup) {
        List<CafeEntity> cafes = cafeRepository.findTop500ByThumbnailUrlIsNotNullAndStatusAndIsCafeTrue(CafeStatus.OPEN);

        // 오늘 날짜 기준 시드 고정
        long seed = LocalDate.now().toEpochDay();
        Collections.shuffle(cafes, new Random(seed));

        List<DiscoveryResponse> randomContent = cafes.stream()
                .map(cafe -> DiscoveryResponse.from(cafe, abGroup))
                .collect(Collectors.toList());

        return getSliceFromList(randomContent, page, size);
    }

    /**
     * 리스트 데이터에 대한 Slice(페이징) 처리
     * 
     * @param list 리스트 데이터
     * @param page 페이지 번호
     * @param size 페이지 당 썸네일 수
     * @return Slice 데이터
     */
    private <T> Slice<T> getSliceFromList(List<T> list, int page, int size) {
        int start = page * size;
        if (start >= list.size()) {
            return new SliceImpl<>(Collections.emptyList(), PageRequest.of(page, size), false);
        }

        int end = Math.min(start + size, list.size());
        boolean hasNext = end < list.size();

        return new SliceImpl<>(list.subList(start, end), PageRequest.of(page, size), hasNext);
    }
}
