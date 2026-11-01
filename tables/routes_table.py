
from psycopg2 import sql

from dbtable import DbTable


class RoutesTable(DbTable):
    """Работа с маршрутами пригородных поездов."""

    table = "routes"

    def all_by_station(self, station_id):
        """Маршруты, проходящие через выбранную станцию
        в качестве начальной или конечной.
        """
        stations_table = sql.Identifier(
            self.dbconn.schema, "stations"
        )

        query = sql.SQL("""
            SELECT
                r.route_id,
                s1.name AS start_station,
                s2.name AS end_station
            FROM {} AS r
            JOIN {} AS s1
                ON r.start_station_id = s1.station_id
            JOIN {} AS s2
                ON r.end_station_id = s2.station_id
            WHERE r.start_station_id = %s
               OR r.end_station_id = %s
            ORDER BY r.route_id
        """).format(
            self.table_name(),
            stations_table,
            stations_table
        )

        return self.fetch_all(
            query, (station_id, station_id)
        )

    def add(self, start_station_id, end_station_id):
        """Добавление нового маршрута."""
        if start_station_id == end_station_id:
            raise ValueError(
                "Начальная и конечная станции должны различаться."
            )

        query = sql.SQL("""
            INSERT INTO {}
                (start_station_id, end_station_id)
            VALUES (%s, %s)
            RETURNING route_id
        """).format(self.table_name())

        return self.execute_returning(
            query,
            (start_station_id, end_station_id)
        )

    def delete_by_position(self, station_id, number):
        """Удаление маршрута по номеру строки в списке."""
        if number < 1:
            return False

        with self.transaction() as cursor:
            cursor.execute(
                sql.SQL("""
                    SELECT route_id
                    FROM {}
                    WHERE start_station_id = %s
                       OR end_station_id = %s
                    ORDER BY route_id
                    LIMIT 1 OFFSET %s
                    FOR UPDATE
                """).format(self.table_name()),
                (station_id, station_id, number - 1)
            )

            route = cursor.fetchone()

            if route is None:
                return False

            cursor.execute(
                sql.SQL("""
                    DELETE FROM {}
                    WHERE route_id = %s
                """).format(self.table_name()),
                (route["route_id"],)
            )

            return cursor.rowcount == 1
