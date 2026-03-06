package com.degging.be.global.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/**
 * Jpa 설정 파일
 */
@Configuration
@EnableJpaAuditing // 엔티티의 @CreatedDate, @LastModifiedDate 활성화
public class JpaConfig {
}