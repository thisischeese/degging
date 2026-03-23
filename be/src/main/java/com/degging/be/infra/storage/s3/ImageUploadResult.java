package com.degging.be.infra.storage.s3;

/**
 * S3 이미지 업로드 결과를 담을 DTO
 */
public record ImageUploadResult(String storedName, String originName) {}
