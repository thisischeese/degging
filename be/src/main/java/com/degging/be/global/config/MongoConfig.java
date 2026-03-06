package com.degging.be.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

/**
 * MongoDB 설정 파일
 */
@Configuration
public class MongoConfig {

    @Bean
    public MongoTransactionManager transactionManager(MongoDatabaseFactory dbFactory) {
        // MongoDB는 설정이 없으면 서비스 레이어에서 트랜잭션 어노테이션 사용 불가
        return new MongoTransactionManager(dbFactory);
    }
}
