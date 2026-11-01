
# ФИО: Ожиганов В. В.
# Вариант: 5
# Сессионный проект по PostgreSQL.
#
# Условие варианта:
# Таблицы поездов и станций без связей с другими таблицами.
# Интерфейс только для начальной и конечной станций.
#
# Используются таблицы stations и routes из предыдущего
# учебного проекта о пригородных поездах.
#
# Реализованы просмотр, добавление, изменение и удаление
# станций, а также просмотр, добавление и удаление маршрутов.
# Суррогатные ключи не вводятся пользователем.

import psycopg2
from psycopg2 import errors

from project_config import ProjectConfig
from dbconnection import DbConnection
from dbtable import DbTable
from tables.stations_table import StationsTable
from tables.routes_table import RoutesTable


MAX_INTEGER = 2147483647


def read_number(message, default=None):
    """Чтение положительного целого числа. 0 означает отмену."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{message}{suffix} (0 - отмена): ").strip()

        if value == "0":
            return None

        if value == "" and default is not None:
            return default

        if not value.isascii() or not value.isdigit():
            print("Ошибка: введите положительное целое число.")
            continue

        if len(value) > 10:
            print("Ошибка: число слишком большое.")
            continue

        number = int(value)

        if not 1 <= number <= MAX_INTEGER:
            print("Ошибка: число вне допустимого диапазона.")
            continue

        return number


def read_name(message, default=None):
    """Чтение названия станции с проверкой длины."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{message}{suffix} (0 - отмена): ").strip()

        if value == "0":
            return None

        if not value and default is not None:
            return default

        if not value:
            print("Ошибка: название не может быть пустым.")
            continue

        if len(value) > 100:
            print("Ошибка: допускается не более 100 символов.")
            continue

        return value


def read_position(total):
    """Выбор порядкового номера строки."""
    while True:
        value = input(
            "Введите номер записи (0 - назад): "
        ).strip()

        if value == "0":
            return None

        if not value.isascii() or not value.isdigit():
            print("Ошибка: введите номер строки.")
            continue

        if len(value) > 10:
            print("Ошибка: неверный номер.")
            continue

        number = int(value)

        if 1 <= number <= total:
            return number

        print(f"Ошибка: выберите номер от 1 до {total}.")


def confirm(message):
    """Подтверждение потенциально опасных действий."""
    while True:
        answer = input(
            f"{message} (да/нет): "
        ).strip().lower()

        if answer in ("да", "д", "yes", "y"):
            return True

        if answer in ("нет", "н", "no", "n", ""):
            return False

        print("Введите 'да' или 'нет'.")


class TrainApp:
    """Консольный интерфейс управления станциями и маршрутами."""

    def __init__(self):
        self.stations = StationsTable()
        self.routes = RoutesTable()

    def show_stations(self):
        """Показать станции с порядковыми номерами."""
        records = self.stations.all()

        print("\n=== СПИСОК СТАНЦИЙ ===")

        if not records:
            print("Станции отсутствуют.")
            return records

        print(
            f"{'№':<4} {'Название':<26} "
            f"{'Тарифная зона':<16} {'Порядок'}"
        )
        print("-" * 65)

        for number, station in enumerate(records, start=1):
            print(
                f"{number:<4} "
                f"{station['name']:<26} "
                f"{station['tariff_zone']:<16} "
                f"{station['position_number']}"
            )

        return records

    def select_station(self):
        """Выбрать станцию без ввода ее ID."""
        records = self.show_stations()

        if not records:
            return None

        number = read_position(len(records))

        if number is None:
            return None

        return records[number - 1]

    def add_station(self):
        print("\n=== ДОБАВЛЕНИЕ СТАНЦИИ ===")

        name = read_name("Название станции")
        if name is None:
            return

        tariff = read_number("Тарифная зона")
        if tariff is None:
            return

        position = read_number("Порядок на линии")
        if position is None:
            return

        self.stations.add(name, tariff, position)
        print(f"Станция «{name}» успешно добавлена.")

    def edit_station(self):
        print("\n=== ИЗМЕНЕНИЕ СТАНЦИИ ===")

        station = self.select_station()
        if station is None:
            return

        print(f"\nВыбрана станция: {station['name']}")
        print("Enter - сохранить прежнее значение.")

        name = read_name(
            "Новое название",
            station["name"]
        )
        if name is None:
            return

        tariff = read_number(
            "Новая тарифная зона",
            station["tariff_zone"]
        )
        if tariff is None:
            return

        position = read_number(
            "Новый порядок на линии",
            station["position_number"]
        )
        if position is None:
            return

        count = self.stations.update(
            station["station_id"],
            name,
            tariff,
            position
        )

        if count:
            print("Станция успешно изменена.")
        else:
            print("Станция не найдена. Изменения не внесены.")

    def delete_station(self):
        print("\n=== УДАЛЕНИЕ СТАНЦИИ ===")

        station = self.select_station()
        if station is None:
            return

        related = self.stations.count_routes(
            station["station_id"]
        )

        print(f"\nСтанция: {station['name']}")

        if related:
            print(f"Связанных маршрутов: {related}")
            print(
                "При удалении станции связанные маршруты "
                "тоже будут удалены."
            )

        if not confirm("Подтвердить удаление"):
            print("Удаление отменено.")
            return

        result = self.stations.delete(
            station["station_id"],
            delete_related=(related > 0)
        )

        if result["blocked"]:
            print(
                "Удаление не выполнено: появились связанные "
                "маршруты. Повторите операцию."
            )
        elif result["deleted"]:
            print("Станция успешно удалена.")
        else:
            print("Станция не найдена.")

    def show_routes(self, station):
        """Показать маршруты выбранной станции."""
        records = self.routes.all_by_station(
            station["station_id"]
        )

        print(f"\n=== МАРШРУТЫ: {station['name']} ===")

        if not records:
            print("Связанных маршрутов нет.")
            return records

        print(
            f"{'№':<4} {'Начальная станция':<26} "
            f"{'Конечная станция'}"
        )
        print("-" * 65)

        for number, route in enumerate(records, start=1):
            print(
                f"{number:<4} "
                f"{route['start_station']:<26} "
                f"{route['end_station']}"
            )

        return records

    def add_route(self, station):
        print("\n=== ДОБАВЛЕНИЕ МАРШРУТА ===")
        print(f"Выбранная станция: {station['name']}")
        print("1 - выбранная станция является начальной")
        print("2 - выбранная станция является конечной")
        print("0 - отмена")

        while True:
            direction = input("Выберите направление: ").strip()

            if direction == "0":
                return

            if direction in ("1", "2"):
                break

            print("Ошибка: выберите 1, 2 или 0.")

        print("\nВыберите вторую станцию маршрута:")

        other_station = self.select_station()
        if other_station is None:
            return

        if station["station_id"] == other_station["station_id"]:
            print(
                "Ошибка: начальная и конечная станции "
                "не могут совпадать."
            )
            return

        if direction == "1":
            start_id = station["station_id"]
            end_id = other_station["station_id"]
        else:
            start_id = other_station["station_id"]
            end_id = station["station_id"]

        self.routes.add(start_id, end_id)
        print("Маршрут успешно добавлен.")

    def delete_route(self, station):
        print("\n=== УДАЛЕНИЕ МАРШРУТА ===")

        records = self.show_routes(station)

        if not records:
            return

        number = read_position(len(records))
        if number is None:
            return

        route = records[number - 1]

        print(
            f"\nМаршрут: {route['start_station']} -> "
            f"{route['end_station']}"
        )

        if not confirm("Удалить выбранный маршрут"):
            print("Удаление отменено.")
            return

        deleted = self.routes.delete_by_position(
            station["station_id"],
            number
        )

        if deleted:
            print("Маршрут успешно удален.")
        else:
            print("Маршрут не найден.")

    def manage_routes(self):
        print("\n=== ВЫБОР СТАНЦИИ ===")

        station = self.select_station()

        if station is None:
            return

        while True:
            self.show_routes(station)

            print("\nОПЕРАЦИИ С МАРШРУТАМИ")
            print("1 - добавить маршрут")
            print("2 - удалить маршрут")
            print("0 - главное меню")

            choice = input("Выберите действие: ").strip()

            if choice == "0":
                return
            elif choice == "1":
                self.add_route(station)
            elif choice == "2":
                self.delete_route(station)
            else:
                print("Ошибка: неизвестная команда.")

    def run(self):
        """Основной цикл приложения."""
        while True:
            print("\n" + "=" * 50)
            print("ПРИГОРОДНЫЕ ПОЕЗДА: УПРАВЛЕНИЕ ДАННЫМИ")
            print("=" * 50)

            print("1 - просмотр станций")
            print("2 - добавление станции")
            print("3 - изменение станции")
            print("4 - удаление станции")
            print("5 - маршруты выбранной станции")
            print("9 - выход")

            choice = input("\nВыберите действие: ").strip()

            try:
                if choice == "1":
                    self.show_stations()
                elif choice == "2":
                    self.add_station()
                elif choice == "3":
                    self.edit_station()
                elif choice == "4":
                    self.delete_station()
                elif choice == "5":
                    self.manage_routes()
                elif choice == "9":
                    print("Работа завершена.")
                    return
                else:
                    print("Ошибка: неизвестная команда.")

            except errors.UniqueViolation as exc:
                constraint = exc.diag.constraint_name or ""

                if "name" in constraint:
                    print("Ошибка: станция с таким названием уже есть.")
                elif "position" in constraint:
                    print("Ошибка: этот порядковый номер уже занят.")
                else:
                    print("Ошибка: запись с такими данными уже есть.")

            except errors.ForeignKeyViolation:
                print(
                    "Ошибка: запись связана с другими данными "
                    "или выбранная станция не существует."
                )

            except errors.CheckViolation:
                print("Ошибка: нарушены ограничения данных.")

            except psycopg2.DataError:
                print("Ошибка: недопустимый формат или размер данных.")

            except ValueError as exc:
                print(f"Ошибка: {exc}")

            except psycopg2.OperationalError:
                print("Ошибка: соединение с PostgreSQL потеряно.")
                return

            except psycopg2.Error:
                print(
                    "Ошибка базы данных. Изменения отменены."
                )


def main():
    connection = None

    try:
        config = ProjectConfig()
        connection = DbConnection(config)

        DbTable.dbconn = connection

        if not connection.test():
            print("Не удалось проверить подключение к PostgreSQL.")
            return

        print("Подключение к PostgreSQL установлено.")

        application = TrainApp()
        application.run()

    except (psycopg2.Error, OSError, KeyError, ValueError) as exc:
        print("Не удалось запустить приложение.")
        print(f"Проверьте конфигурацию и PostgreSQL: {type(exc).__name__}")

    except (KeyboardInterrupt, EOFError):
        print("\nРабота прервана пользователем.")

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
