package com.degging.be.infra.cache.redis;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Redis CRUD 처리를 담당하는 공통 서비스
 */
@Service
@RequiredArgsConstructor
public class RedisService {

    private final RedisTemplate<String, Object> redisTemplate;

    /**
     * 데이터를 저장합니다.
     * @param key 저장할 키
     * @param value 저장할 값
     * @param duration 만료 시간
     * @param unit 시간 단위
     */
    public void setValues(String key, Object value, long duration, TimeUnit unit) {
        redisTemplate.opsForValue().set(key, value, duration, unit);
    }

    /**
     * 데이터를 조회합니다.
     * @param key 조회할 키
     * @return 저장된 값 (없을 경우 null)
     */
    public Object getValues(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    /**
     * 데이터를 삭제합니다.
     * @param key 삭제할 키
     */
    public void deleteValues(String key) {
        redisTemplate.delete(key);
    }

    /**
     * 리스트 형식의 데이터를 조회합니다 (형변환 포함).
     * @param key 조회할 키
     * @return String 리스트 (없을 경우 null)
     */
    @SuppressWarnings("unchecked")
    public List<String> getListValues(String key) {
        return (List<String>) redisTemplate.opsForValue().get(key);
    }
}
