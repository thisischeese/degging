package com.degging.be.discovery.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.discovery.dto.response.DiscoveryResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Slice;
import org.springframework.data.domain.SliceImpl;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DiscoveryService {

    private final CafeRepository cafeRepository;

    /**
     * 무한 스크롤 지원: 1일 단위로 새로고침해도 동일한 순서를 유지하는 카페 리스트 반환
     */
    public Slice<DiscoveryResponse> getDailyDiscoveryCafes(int page, int size) {
        
        // 충분한 풀(Pool) 조회를 위해 썸네일 있는 상위 500개 확보
        List<CafeEntity> cafes = cafeRepository.findTop500ByThumbnailUrlIsNotNullAndStatusAndIsCafeTrue(CafeStatus.OPEN);

        // 오늘 날짜를 기준으로 Seed 고정
        long seed = LocalDate.now().toEpochDay();
        Collections.shuffle(cafes, new Random(seed));

        int start = page * size;
        if (start >= cafes.size()) {
            return new SliceImpl<>(Collections.emptyList(), PageRequest.of(page, size), false);
        }

        int end = Math.min(start + size, cafes.size());
        boolean hasNext = end < cafes.size();

        List<DiscoveryResponse> content = cafes.subList(start, end).stream()
                .map(DiscoveryResponse::from)
                .collect(Collectors.toList());

        return new SliceImpl<>(content, PageRequest.of(page, size), hasNext);
    }
}
