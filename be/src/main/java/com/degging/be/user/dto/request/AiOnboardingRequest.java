package com.degging.be.user.dto.request;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * AI 서버에 전송하는 온보딩 요청 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AiOnboardingRequest {

    private UUID user_id;

    private String nickname;

    private String email;

    private List<String> favorite_menus;

    private List<String> mood_tags;

    private List<String> cafes;

    public static AiOnboardingRequest of(
            UUID userId,
            String nickname,
            String email,
            List<String> menuNames,
            List<String> moodTagNames,
            List<UUID> cafeIds) {

        List<String> cafeIdStrings = cafeIds.stream()
                .map(UUID::toString)
                .toList();

        return new AiOnboardingRequest(userId, nickname, email, menuNames, moodTagNames, cafeIdStrings);
    }
}
