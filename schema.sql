
-- Сессионный проект по PostgreSQL
-- Ожиганов В. В.
-- Вариант 5: пригородные поезда и станции

BEGIN;

-- Отдельная схема для сессионного проекта
CREATE SCHEMA IF NOT EXISTS session_trains;

-- Таблица станций из первого модуля
CREATE TABLE IF NOT EXISTS session_trains.stations (
    station_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    tariff_zone INTEGER NOT NULL,
    position_number INTEGER NOT NULL UNIQUE,

    CONSTRAINT chk_station_tariff_zone
        CHECK (tariff_zone > 0),

    CONSTRAINT chk_station_position
        CHECK (position_number > 0)
);

-- Таблица маршрутов из первого модуля
CREATE TABLE IF NOT EXISTS session_trains.routes (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    start_station_id BIGINT NOT NULL,
    end_station_id BIGINT NOT NULL,

    CONSTRAINT fk_routes_start_station
        FOREIGN KEY (start_station_id)
        REFERENCES session_trains.stations (station_id),

    CONSTRAINT fk_routes_end_station
        FOREIGN KEY (end_station_id)
        REFERENCES session_trains.stations (station_id),

    CONSTRAINT chk_route_different_stations
        CHECK (start_station_id <> end_station_id)
);

-- Исходные станции из второго модуля
INSERT INTO session_trains.stations
    (name, tariff_zone, position_number)
VALUES
    ('Новосибирск-Главный', 1, 1),
    ('Центр',               1, 2),
    ('Льниха',              7, 3),
    ('Буготак',             8, 4),
    ('Салаир',              9, 5),
    ('Тогучин',            13, 6)
ON CONFLICT DO NOTHING;

-- Пять маршрутов из второго модуля.
-- Повторяющиеся пары станций представляют разные рейсы.
-- Идентификаторы станций определяются автоматически по названиям.

INSERT INTO session_trains.routes
    (start_station_id, end_station_id)
SELECT
    s1.station_id,
    s2.station_id
FROM (
    VALUES
        (1, 'Новосибирск-Главный', 'Тогучин'),
        (2, 'Новосибирск-Главный', 'Тогучин'),
        (3, 'Новосибирск-Главный', 'Тогучин'),
        (4, 'Новосибирск-Главный', 'Буготак'),
        (5, 'Тогучин', 'Новосибирск-Главный')
) AS source (sort_order, start_name, end_name)
JOIN session_trains.stations AS s1
    ON s1.name = source.start_name
JOIN session_trains.stations AS s2
    ON s2.name = source.end_name
WHERE NOT EXISTS (
    SELECT 1 FROM session_trains.routes
)
ORDER BY source.sort_order;

COMMIT;
