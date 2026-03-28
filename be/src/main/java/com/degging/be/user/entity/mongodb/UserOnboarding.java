package com.degging.be.user.entity.mongodb;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 유저의 온보딩 선택 결과와 분석된 태그 빈도를 관리하는 MongoDB 도큐먼트
 */
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Document(collection = "user_onboardings")
public class UserOnboarding {

    @Id
    private String id;

    @Field("user_id")
    private UUID userId; // RDB 유저 엔티티와 매핑하기 위한 식별자

    @Field("preferred_tags")
    private Map<String, Integer> preferredTags; // 분석된 선호 분위기 태그 식별자별 선택 빈도

    @Field("selected_data")
    private SelectedData selectedData; // 사용자가 직접 선택한 카페와 메뉴의 식별자 목록

    @Field("created_at")
    private LocalDateTime createdAt; // 취향 정보가 처음 생성된 시점

    /**
     * 사용자 선택 정보를 그룹화하여 관리하는 내부 클래스
     */
    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SelectedData {
        private List<UUID> cafeIds; // 선택된 카페 식별자 목록
        private List<String> menuNames; // 선택된 메뉴 식별자 목록
    }

    /**
     * 유저 취향 정보 도큐먼트 생성을 위한 정적 팩토리 메서드
     *
     * @param userId 유저 식별자
     * @param tags 분석된 태그 맵
     * @param cafeIds 선택한 카페 목록
     * @param menuNames 선택한 메뉴 목록
     * @return 생성된 유저 취향 도큐먼트 객체
     */
    public static UserOnboarding of(UUID userId, Map<String, Integer> tags, List<UUID> cafeIds, List<String> menuNames) {
        return UserOnboarding.builder()
                .userId(userId)
                .preferredTags(tags)
                .selectedData(SelectedData.builder()
                                      .cafeIds(cafeIds)
                                      .menuNames(menuNames)
                                      .build())
                .createdAt(LocalDateTime.now())
                .build();
    }

}