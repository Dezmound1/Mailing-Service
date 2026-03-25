# TODO — Mailing Service


## Фаза 2: Django-приложение `mailings`

- [ ] `python manage.py startapp mailings` (внутри `mailing_service/`)
- [ ] Зарегистрировать `mailings` в `INSTALLED_APPS`

### Модель `MailingRecord`

- [ ] Поля:
  - `external_id: CharField(max_length=255, unique=True, db_index=True)`
  - `user_id: CharField(max_length=255)`
  - `email: EmailField()`
  - `subject: CharField(max_length=500)`
  - `message: TextField()`
  - `status: CharField(choices=Status)` — enum: `pending`, `sent`, `failed`
  - `created_at: DateTimeField(auto_now_add=True)`
  - `updated_at: DateTimeField(auto_now=True)`
  - `error_message: TextField(blank=True, default="")` — для записи причины ошибки
- [ ] Enum `Status` через `models.TextChoices`
- [ ] `class Meta: ordering = ["-created_at"]`
- [ ] `__str__` — `f"MailingRecord {self.external_id} → {self.email}"`
- [ ] Миграция: `makemigrations` + `migrate`

### Admin (опционально, но полезно для проверки)

- [ ] Зарегистрировать `MailingRecord` в admin с `list_display`, `list_filter`, `search_fields`

---

## Фаза 3: Сервисный слой

### `mailings/services/importer.py` — ImportService

- [ ] Класс / функция `import_from_xlsx(file_path, batch_size=500, dry_run=False)`
- [ ] Чтение XLSX через `openpyxl` в `read_only=True` режиме
- [ ] Валидация заголовков (первая строка)
- [ ] Построчный парсинг с валидацией (email формат, обязательные поля)
- [ ] Чанкинг: накопление батча → обработка:
  - запрос existing `external_id` из БД
  - фильтрация дубликатов
  - `bulk_create` новых записей (`ignore_conflicts=True`)
  - отправка Celery-задач для созданных записей
- [ ] `--dry-run`: пропустить `bulk_create` и dispatch задач, только считать статистику
- [ ] Возвращает dataclass со статистикой:
  - `total_rows` — обработано строк
  - `created` — создано записей
  - `skipped` — пропущено (дубликаты)
  - `errors` — ошибки валидации
  - `error_details: list[str]` — описания ошибок (строка N: причина)

### `mailings/services/email.py` — EmailService (Celery task)

- [ ] `@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=True)`
- [ ] Логика:
  - загрузить `MailingRecord` по `id`
  - `sleep(randint(5, 20))`
  - `structlog.info("Send EMAIL", to=record.email, subject=record.subject)`
  - обновить `status = sent`
- [ ] Обработка ошибок:
  - при исключении — `status = failed`, сохранить `error_message`
  - retry через механизм Celery

---

## Фаза 4: Management command

### `mailings/management/commands/import_mailings.py`

- [ ] Аргументы:
  - `file_path` (positional) — путь к XLSX файлу
  - `--batch-size` (default=500) — размер чанка
  - `--dry-run` — режим предпросмотра
- [ ] Валидация: файл существует, расширение `.xlsx`
- [ ] Вызов `ImportService.import_from_xlsx(...)`
- [ ] Вывод результата в stdout:
  ```
  Import complete:
    Total rows:  1000
    Created:      950
    Skipped:       45
    Errors:         5
  ```
- [ ] При `--dry-run` — префикс `[DRY RUN]`, пояснение что записи не созданы
- [ ] При наличии ошибок — вывод деталей (первые N ошибок)

---

## Фаза 5: Тесты

### `mailings/tests/test_models.py`

- [ ] Создание `MailingRecord`, проверка полей и default status
- [ ] Уникальность `external_id` (IntegrityError при дубликате)
- [ ] `__str__` формат

### `mailings/tests/test_importer.py`

- [ ] Фикстура: генерация тестового XLSX файла (openpyxl)
- [ ] Импорт валидного файла — все записи созданы
- [ ] Повторный импорт того же файла — все записи пропущены
- [ ] Файл с невалидными строками (пустой email, отсутствующие поля)
- [ ] `--dry-run` — записи НЕ созданы в БД
- [ ] `--batch-size` — корректная работа при разных размерах чанка
- [ ] Пустой файл (только заголовки)
- [ ] Файл с неверными заголовками

### `mailings/tests/test_tasks.py`

- [ ] `send_email` task — статус меняется на `sent`
- [ ] `send_email` task — при ошибке статус `failed`, `error_message` заполнен
- [ ] Mock `sleep` для ускорения тестов

### `mailings/tests/test_command.py`

- [ ] Запуск команды через `call_command`
- [ ] Проверка stdout вывода (статистика)
- [ ] `--dry-run` не создаёт записей
- [ ] Несуществующий файл — ошибка `CommandError`

### Инфраструктура тестов

- [ ] `conftest.py` — общие фикстуры (tmp XLSX файл, factory)
- [ ] `factories.py` — `MailingRecordFactory` (factory-boy)
- [ ] Настройка pytest: `pytest.ini` / `pyproject.toml` → `DJANGO_SETTINGS_MODULE`

---

## Фаза 6: Docker & финализация

- [ ] Проверить `docker compose up` — все сервисы стартуют
- [ ] Проверить `make import FILE=data/test.xlsx` — полный цикл
- [ ] **Makefile** — расширить:
  - `make test` — запуск pytest
  - `make lint` — запуск ruff
  - `make import FILE=...` — запуск import_mailings
  - `make shell` — Django shell
  - `make logs` — docker compose logs
- [ ] Подготовить тестовый XLSX файл в `data/sample.xlsx`

---

## Фаза 7: Документация

- [ ] **README.md**:
  - описание проекта
  - стек технологий
  - быстрый старт (Docker Compose)
  - использование management command (примеры)
  - описание архитектуры (коротко)
  - запуск тестов
  - переменные окружения (таблица)

---

## Порядок выполнения

```
Фаза 1 → Фаза 2 → Фаза 3 → Фаза 4 → Фаза 5 → Фаза 6 → Фаза 7
celery    app       logic    command   tests    docker     docs
```

Каждая фаза — отдельный коммит (или группа коммитов).
