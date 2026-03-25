package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.external.AiCrawlerResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * AI 크롤링 응답 데이터를 로컬 파일시스템에 JSON으로 백업하는 서비스
 * DB 저장 실패 시 데이터 유실을 방지하기 위한 안전망
 */
@Slf4j
@Service
public class CrawlingBackupService {

    private static final DateTimeFormatter TIMESTAMP_FMT =
            DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");

    private final ObjectMapper objectMapper;
    private final String backupDir;

    public CrawlingBackupService(
            @Value("${crawling.backup.dir:/app/crawling-backup}") String backupDir) {
        this.objectMapper = new ObjectMapper()
                .enable(SerializationFeature.INDENT_OUTPUT);
        this.backupDir = backupDir;
    }

    /**
     * AI 크롤링 응답을 JSON 파일로 저장
     *
     * @param response  AI 서버 응답 객체
     * @param loop      현재 루프 번호
     * @param batchIdx  현재 배치(워커) 번호
     */
    public void backup(AiCrawlerResponse response, int loop, int batchIdx) {
        try {
            File dir = new File(backupDir);
            if (!dir.exists() && !dir.mkdirs()) {
                log.warn("[백업] 디렉토리 생성 실패: {}", backupDir);
                return;
            }

            String timestamp = LocalDateTime.now().format(TIMESTAMP_FMT);
            String filename = String.format("crawling_loop%d_worker%d_%s.json",
                    loop, batchIdx, timestamp);
            File file = new File(dir, filename);

            objectMapper.writeValue(file, response);
            log.info("[백업] JSON 저장 완료: {} ({}건)",
                    file.getAbsolutePath(),
                    response.getItems() != null ? response.getItems().size() : 0);

        } catch (IOException e) {
            // 백업 실패는 크롤링 흐름을 중단시키지 않음
            log.error("[백업] JSON 저장 실패 (loop={}, worker={}): {}", loop, batchIdx, e.getMessage());
        }
    }
}
