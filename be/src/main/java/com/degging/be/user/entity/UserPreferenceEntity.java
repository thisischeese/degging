package com.degging.be.user.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.ColumnTransformer;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import com.degging.be.global.converter.VectorConverter;

@Entity
@Table(name = "user_preference")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class UserPreferenceEntity {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private UserEntity user;

    @Convert(converter = VectorConverter.class)
    @Column(name = "preference_vector", columnDefinition = "vector(64)")
    @ColumnTransformer(write = "?::vector")
    private float[] preferenceVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "preference_tags", columnDefinition = "jsonb")
    private List<String> preferenceTags;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    public void updatePreference(float[] vector, List<String> tags) {
        this.preferenceVector = vector;
        this.preferenceTags = tags;
    }
}
