package com.degging.be.scrap.controller;

import com.degging.be.scrap.service.ScrapService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 카페 스크랩 관련 API 컨트롤러
 */
@RestController
@RequestMapping("/api/scrap")
@RequiredArgsConstructor
public class ScrapController {
    private final ScrapService scrapService;
}
