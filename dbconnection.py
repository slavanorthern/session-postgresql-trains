
import psycopg2


class DbConnection:
    """Подключение к PostgreSQL."""

    def __init__(self, config):
        self.schema = config.dbtableprefix.rstrip(".")

        if not self.schema:
            raise ValueError("Не указана схема базы данных.")

        self.conn = psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            connect_timeout=5,
        )

    def test(self):
        """Проверка подключения без изменения данных."""
        with self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone()[0] == 1

    def close(self):
        """Закрытие соединения."""
        if self.conn and not self.conn.closed:
            self.conn.close()
