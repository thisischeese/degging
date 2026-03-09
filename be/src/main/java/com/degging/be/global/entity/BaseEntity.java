package com.degging.be.global.entity;

import jakarta.persistence.Column;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * 모든 엔티티에서 공통으로 사용하는 매핑 정보를 정의하는 추상 클래스
 * 엔티티의 생성 일자와 수정 일자를 자동으로 관리
 */

@Getter
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity {

    // 엔티티가 생성되어 저장될 때 생성시간 자동 기록
    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    // 엔티티의 값이 변경될 때 수정시간 자동 기록
    @LastModifiedDate
    private LocalDateTime updatedAt;
}