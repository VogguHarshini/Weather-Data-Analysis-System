-- MySQL database design for Weather Data Analysis System
CREATE DATABASE IF NOT EXISTS weather_analysis;
USE weather_analysis;

CREATE TABLE IF NOT EXISTS weather_records (
    record_id INT PRIMARY KEY,
    observation_date DATE NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL COMMENT 'Degrees Celsius (°C)',
    humidity DECIMAL(5,2) NOT NULL COMMENT 'Relative humidity (%)',
    rainfall DECIMAL(8,2) NOT NULL COMMENT 'Rainfall in millimetres (mm)',
    CHECK (humidity >= 0 AND humidity <= 100),
    CHECK (rainfall >= 0)
);

CREATE INDEX idx_weather_date_location
ON weather_records(observation_date, location);
