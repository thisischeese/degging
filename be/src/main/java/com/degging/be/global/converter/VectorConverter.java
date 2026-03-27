package com.degging.be.global.converter;

import com.pgvector.PGvector;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.sql.SQLException;

@Converter(autoApply = true)
public class VectorConverter implements AttributeConverter<float[], String> {

    @Override
    public String convertToDatabaseColumn(float[] attribute) {
        if (attribute == null) {
            return null;
        }
        return new PGvector(attribute).toString();
    }

    @Override
    public float[] convertToEntityAttribute(String dbData) {
        if (dbData == null) {
            return null;
        }
        try {
            return new PGvector(dbData).toArray();
        } catch (SQLException e) {
            throw new RuntimeException("Failed to convert string to vector", e);
        }
    }
}
