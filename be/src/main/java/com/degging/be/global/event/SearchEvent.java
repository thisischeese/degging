package com.degging.be.global.event;

/**
 * 검색 발생 시 전달할 데이터를 담는 이벤트 클래스
 */
public record SearchEvent(String keyword) {
}
