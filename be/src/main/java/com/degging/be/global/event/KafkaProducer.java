package com.degging.be.global.event;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * Kafka Producer 이벤트를 발행을 담당하는 클래스
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KafkaProducer {
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public void send(String topic, Object payload) {
        log.info("[Kafka] 전송 시도 - Topic: {}, Payload: {}", topic, payload);

        kafkaTemplate.send(topic, payload)
                .whenComplete((result, ex)-> {
                   if (ex == null) {
                       log.info("[Kafka] 전송 완료 - Topic: {}, Offset: {}",
                               topic, result.getRecordMetadata().offset());
                   } else {
                       log.error("[Kafka] 전송 실패 - Topic: {}, Error: {}",
                               topic, ex.getMessage());
                   }
                });
    }
}
