package com.degging.be.cafe.service;

import com.degging.be.infra.ai.dto.response.AiCrawlerResponse;
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

    /**
     * 기존 백업 파일의 내용을 업데이트 (부분 성공 시 내용 축소용)
     *
     * @param file     업데이트할 파일
     * @param response 새로운 응답 객체
     */
    public void updateBackupFile(File file, AiCrawlerResponse response) {
        try {
            objectMapper.writeValue(file, response);
            log.info("[백업] 파일 내용 갱신 완료 (남은 항목: {}건)", 
                    response.getItems() != null ? response.getItems().size() : 0);
        } catch (IOException e) {
            log.error("[백업] 파일 내용 갱신 실패 ({}): {}", file.getName(), e.getMessage());
        }
    }

    /**
     * 아직 처리되지 않은 모든 백업 파일 목록을 반환
     *
     * @return 백업 파일 목록
     */
    public File[] loadAllBackupFiles() {
        File dir = new File(backupDir);
        if (!dir.exists() || !dir.isDirectory()) {
            return new File[0];
        }
        // .json 파일만 필터링하여 반환
        return dir.listFiles((d, name) -> name.endsWith(".json"));
    }

    /**
     * 특정 백업 파일을 AiCrawlerResponse 객체로 로드
     *
     * @param file 백업 파일
     * @return 역직렬화된 응답 객체 (실패 시 null)
     */
    public AiCrawlerResponse loadResponse(File file) {
        try {
            return objectMapper.readValue(file, AiCrawlerResponse.class);
        } catch (IOException e) {
            log.error("[백업] JSON 파일 로드 실패 ({}): {}", file.getName(), e.getMessage());
            return null;
        }
    }

    /**
     * 처리가 완료된 백업 파일을 success 폴더로 이동 (아카이빙)
     *
     * @param file 이동할 파일
     */
    public void archiveBackupFile(File file) {
        try {
            File successDir = new File(backupDir, "success");
            if (!successDir.exists() && !successDir.mkdirs()) {
                log.warn("[백업] success 디렉토리 생성 실패");
                return;
            }

            File destFile = new File(successDir, file.getName());
            
            // 만약 동일한 이름의 파일이 이미 있다면 타임스탬프를 붙여 중복 방지
            if (destFile.exists()) {
                String newName = System.currentTimeMillis() + "_" + file.getName();
                destFile = new File(successDir, newName);
            }

            if (file.renameTo(destFile)) {
                log.info("[백업] 파일 아카이빙 완료: {} -> success/{}", file.getName(), destFile.getName());
            } else {
                log.warn("[백업] 파일 이동 실패: {}", file.getName());
            }
        } catch (Exception e) {
            log.error("[백업] 아카이빙 중 예외 발생: {}", e.getMessage());
        }
    }
}
