
from psycopg2 import sql

from dbtable import DbTable


class StationsTable(DbTable):
    """Работа со станциями пригородных поездов."""

    table = "stations"

    def all(self):
        """Все станции в порядке следования."""
        query = sql.SQL("""
            SELECT station_id, name, tariff_zone, position_number
            FROM {}
            ORDER BY position_number, station_id
        """).format(self.table_name())

        return self.fetch_all(query)

    def find_by_position(self, number):
        """Поиск станции по номеру строки в интерфейсе."""
        if number < 1:
            return None

        query = sql.SQL("""
            SELECT station_id, name, tariff_zone, position_number
            FROM {}
            ORDER BY position_number, station_id
            LIMIT 1 OFFSET %s
        """).format(self.table_name())

        return self.fetch_one(query, (number - 1,))

    def add(self, name, tariff_zone, position_number):
        """Добавление станции."""
        query = sql.SQL("""
            INSERT INTO {} (name, tariff_zone, position_number)
            VALUES (%s, %s, %s)
            RETURNING station_id
        """).format(self.table_name())

        return self.execute_returning(
            query,
            (name, tariff_zone, position_number)
        )

    def update(self, station_id, name, tariff_zone, position_number):
        """Изменение станции."""
        query = sql.SQL("""
            UPDATE {}
            SET name = %s,
                tariff_zone = %s,
                position_number = %s
            WHERE station_id = %s
        """).format(self.table_name())

        return self.execute(
            query,
            (name, tariff_zone, position_number, station_id)
        )

    def count_routes(self, station_id):
        """Количество маршрутов, связанных со станцией."""
        routes_table = sql.Identifier(
            self.dbconn.schema, "routes"
        )

        query = sql.SQL("""
            SELECT COUNT(*) AS total
            FROM {}
            WHERE start_station_id = %s
               OR end_station_id = %s
        """).format(routes_table)

        result = self.fetch_one(
            query, (station_id, station_id)
        )
        return result["total"]

    def delete(self, station_id, delete_related=False):
        """
        Удаление станции.

        Если имеются связанные маршруты, удаление
        требует отдельного подтверждения пользователя.
        """
        routes_table = sql.Identifier(
            self.dbconn.schema, "routes"
        )

        with self.transaction() as cursor:
            cursor.execute(
                sql.SQL("""
                    SELECT COUNT(*) AS total
                    FROM {}
                    WHERE start_station_id = %s
                       OR end_station_id = %s
                """).format(routes_table),
                (station_id, station_id)
            )
            related = cursor.fetchone()["total"]

            if related > 0 and not delete_related:
                return {
                    "deleted": False,
                    "related_routes": related,
                    "blocked": True
                }

            if related > 0:
                cursor.execute(
                    sql.SQL("""
                        DELETE FROM {}
                        WHERE start_station_id = %s
                           OR end_station_id = %s
                    """).format(routes_table),
                    (station_id, station_id)
                )

            cursor.execute(
                sql.SQL("""
                    DELETE FROM {}
                    WHERE station_id = %s
                    RETURNING station_id
                """).format(self.table_name()),
                (station_id,)
            )

            deleted = cursor.fetchone() is not None

            return {
                "deleted": deleted,
                "related_routes": related,
                "blocked": False
            }
