package com.degging.be.user.repository.mongodb;

import jakarta.persistence.Id;
import lombok.Getter;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.List;
import java.util.UUID;

/**
 * MongoDB 의 User_Profile 테이블에 접근하는 repository
 */
@Document(collection = "user_profiles")
@Getter
public class UserProfileRepository {
    @Id
    private String id;

    @Field("user_id")
    private UUID userId;

    // 다른 필드가 수십 개 더 있어도, 이것만 필요하면 이것만 적으면 됩니다.
    @Field("preferred_tags")
    private List<String> preferredTags;
}