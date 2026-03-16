package com.degging.be;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication(exclude = { // GCP 연결 전 읽지 않도록 설정
        com.google.cloud.spring.autoconfigure.core.GcpContextAutoConfiguration.class,
        com.google.cloud.spring.autoconfigure.storage.GcpStorageAutoConfiguration.class
})
public class BeApplication {

    public static void main(String[] args) {
        SpringApplication.run(BeApplication.class, args);
    }

}
