package com.degging.be.curation.service;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.curation.dto.response.CurationCafeResponse;
import com.degging.be.curation.dto.response.CurationMapResponse;
import com.degging.be.curation.dto.response.CurationResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CurationErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 큐레이션 서비스
 */

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CurationService {

    private final CafeRepository cafeRepository;
    private final UserRepository userRepository;

    // 큐레이션 카테고리별 카페 매핑
    private static final Map<String, List<String>> CURATION_MAP = new HashMap<>();

    static {
        // 카테고리별 카페 매핑
        CURATION_MAP.put("두쫀쿠", Arrays.asList("토끼네부엌", "커피스피릿", "카페 두댓", "낫배드커피 한남"));
        CURATION_MAP.put("소금빵 카페", Arrays.asList("아티스트베이커리 안국", "오소리 베이커리 어린이대공원", "서울소금빵", "베통 성수"));
        CURATION_MAP.put("망고빙수", Arrays.asList("로이즈 롯데월드몰점", "카페하인나", "달콤한거짓말", "고망고 건대1호점"));
        CURATION_MAP.put("딸기케이크", Arrays.asList("1020룸", "미니마이즈", "위베이브베이크샵", "아삐뽀레 익선점"));
    }

    /**
     * 큐레이션 미니맵 조회
     * 
     * @param userId   사용자 ID
     * @param category 큐레이션 카테고리
     * @param cafeName 카페 이름
     * @return 큐레이션 미니맵 응답 DTO
     */
    public CurationMapResponse getCurationMinimap(UUID userId, String category, String cafeName) {
        // 유저 검증
        validateUser(userId);

        // 카테고리 확인
        if (!CURATION_MAP.containsKey(category)) {
            throw new BaseException(CurationErrorCode.CURATION_CATEGORY_NOT_FOUND);
        }

        // 특정 카페 정보 조회 (Optional 활용)
        return cafeRepository.findAllByName(cafeName).stream()
                .findFirst()
                .map(CurationMapResponse::from)
                .orElseThrow(() -> {
                    log.error("큐레이션 미니맵 카페를 찾을 수 없습니다: {}", cafeName);
                    return new BaseException(CurationErrorCode.CURATION_NOT_FOUND);
                });
    }

    /**
     * 큐레이션 리스트 조회
     * 
     * @param userId   사용자 ID
     * @param category 큐레이션 카테고리
     * @return 큐레이션 리스트 응답 DTO
     */
    public CurationResponse getCurationList(UUID userId, String category) {
        // 유저 검증
        validateUser(userId);

        // 카페 이름 리스트 획득 (null 체크)
        List<String> cafeNames = CURATION_MAP.get(category);
        if (cafeNames == null) {
            throw new BaseException(CurationErrorCode.CURATION_CATEGORY_NOT_FOUND);
        }

        // 카페 정보 조회 (하나라도 없으면 에러)
        List<CafeEntity> cafes = cafeNames.stream()
                .map(name -> cafeRepository.findAllByName(name).stream()
                        .findFirst()
                        .orElseThrow(() -> {
                            log.error("큐레이션 리스트 내 카페를 찾을 수 없습니다: {}", name);
                            return new BaseException(CurationErrorCode.CURATION_NOT_FOUND);
                        }))
                .toList();

        // DTO 변환 및 반환
        List<CurationCafeResponse> cafeList = cafes.stream()
                .map(CurationCafeResponse::from)
                .collect(Collectors.toList());

        return CurationResponse.of(cafeList);
    }

    /**
     * 유저 존재 여부 검증 (공통 로직 분리)
     */
    private void validateUser(UUID userId) {
        if (userId != null) {
            userRepository.findById(userId)
                    .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));
        }
    }
}
