package com.degging.be.global.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Redis 설정 파일
 */
@Configuration
public class RedisConfig {

    @Value("${spring.data.redis.host}")
    private String host;

    @Value("${spring.data.redis.port}")
    private int port;

    @Value("${spring.data.redis.password}")
    private String password;

    // Redis 와의 연결을 관리하는 팩토리 설정
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        // Redis 설정 정보 객체 생성
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName(host);
        config.setPort(port);
        config.setPassword(password);

        return new LettuceConnectionFactory(config);
    }

    // jwt, auth 등에서 사용하는 빈
    @Bean
    public RedisTemplate<Object, Object> objectRedisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<Object, Object> redisTemplate = new RedisTemplate<>();
        redisTemplate.setConnectionFactory(connectionFactory);

        // 기본형은 보통 별도의 Serializer 설정을 하지 않거나 기본 JDK 설정을 따릅니다.
        // 기존에 별도 설정 없이 쓰셨다면 이대로 두시면 됩니다.
        return redisTemplate;
    }

    // rank 에서 사용하는 빈
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
        redisTemplate.setConnectionFactory(connectionFactory);

        // "ranking:keywords" 같은 키 값을 문자열로 저장
        redisTemplate.setKeySerializer(new StringRedisSerializer());
        redisTemplate.setHashKeySerializer(new StringRedisSerializer());

        // ZSet 의 keyword(Member) 를 문자열로 저장
        // 단순 키워드(String)라서 StringRedisSerializer 를 사용함
        redisTemplate.setValueSerializer(new StringRedisSerializer());
        redisTemplate.setHashValueSerializer(new StringRedisSerializer());

        return redisTemplate;
    }
}