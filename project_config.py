from pathlib import Path

import yaml


class ProjectConfig:
    """Загрузка настроек подключения к PostgreSQL."""

    def __init__(self):
        config_path = Path(__file__).resolve().parent / "config.yaml"

        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if not isinstance(config, dict):
            raise ValueError("Некорректный файл config.yaml")

        required = (
            "dbname", "user", "password",
            "host", "dbtableprefix"
        )

        for key in required:
            if key not in config:
                raise ValueError(f"Отсутствует параметр: {key}")

        self.dbname = config["dbname"]
        self.user = config["user"]
        self.password = config["password"]
        self.host = config["host"]
        self.dbtableprefix = config["dbtableprefix"]


if __name__ == "__main__":
    ProjectConfig()
    print("Конфигурация успешно загружена.")