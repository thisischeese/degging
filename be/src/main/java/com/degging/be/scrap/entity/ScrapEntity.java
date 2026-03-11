package com.degging.be.scrap.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;

/**
 * 스크랩 정보를 담는 Entity
 */
@Entity
public class ScrapEntity {
    @Id
    private UUID scrapId;
}
