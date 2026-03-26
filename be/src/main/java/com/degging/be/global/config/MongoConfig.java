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
    public MongoTransactionManager mongoTransactionManager(MongoDatabaseFactory dbFactory) {
        // 이름을 mongoTransactionManager로 지정하여 기본 JPA transactionManager를 덮어쓰지 않도록 함
        return new MongoTransactionManager(dbFactory);
    }
}
