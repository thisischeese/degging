package com.degging.be.global.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 전역 시스템 설정 키-값을 관리하는 엔티티
 * 구글 API 리프레시 토큰 등을 서버 파일시스템 대신 DB 영속성으로 관리할 목적으로 사용
 */
@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "system_entity")
public class SystemEntity extends BaseEntity {

    @Id
    @Column(name = "config_key", nullable = false, length = 100)
    private String configKey;

    @Column(name = "config_value", nullable = false, length = 1000)
    private String configValue;

    @Builder
    public SystemEntity(String configKey, String configValue) {
        this.configKey = configKey;
        this.configValue = configValue;
    }
}
