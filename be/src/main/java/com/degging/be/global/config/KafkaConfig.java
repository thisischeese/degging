package com.degging.be.global.config;

import org.springframework.kafka.support.serializer.JsonSerializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;

import java.util.HashMap;
import java.util.Map;

/**
 * Kafka 설정 클래스
 */
@EnableKafka
@Configuration
public class KafkaConfig {

    @Value("${spring.kafka.bootstrap-servers}")
    private String bootstrapServers;

    // Producer 설정
    @Bean
    public ProducerFactory<String, Object> producerFactory(){
        Map<String, Object> config = new HashMap<>();

        // 어디로 보낼지 (서버 주소)
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        // 메시지 '키' 형식 지정 (문자열)
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);

        // 날짜 처리가 가능한 전용 JsonSerializer 생성
        ObjectMapper objectMapper = new ObjectMapper()
                .registerModule(new JavaTimeModule()) // LocalDate 를 인식함
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // 타임스탬프 대신 문자열로 변환

        return new DefaultKafkaProducerFactory<>(
                config,
                new StringSerializer(),
                new JsonSerializer<>(objectMapper)
        );
    }

    // 서비스 코드에서 주입받아 사용할 도구 
    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        // kafkaTemplate.send("토픽", 데이터) 로 호출 시, 설정을 토대로 메시지 전송
        return new KafkaTemplate<>(producerFactory());
    }
}
