
from contextlib import contextmanager

from psycopg2 import sql
from psycopg2.extras import RealDictCursor


class DbTable:
    """Базовый класс для работы с таблицами PostgreSQL."""

    dbconn = None
    table = None

    def __init__(self):
        if self.dbconn is None:
            raise RuntimeError(
                "Подключение к базе данных не настроено."
            )

        if not self.table:
            raise NotImplementedError(
                "Не указано имя таблицы."
            )

    def table_name(self):
        """Безопасное указание схемы и имени таблицы."""
        return sql.Identifier(
            self.dbconn.schema,
            self.table
        )

    @contextmanager
    def transaction(self):
        """Транзакция с автоматическим откатом при ошибке."""
        with self.dbconn.conn:
            with self.dbconn.conn.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:
                yield cursor

    def fetch_all(self, query, params=()):
        """Получить все строки результата."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    def fetch_one(self, query, params=()):
        """Получить одну строку результата."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute(self, query, params=()):
        """Выполнить INSERT, UPDATE или DELETE."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_returning(self, query, params=()):
        """Выполнить запрос с RETURNING."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
