# Включение планировщика уведомлений

Планировщик отключен для демонстрации, но его легко включить обратно.

## Быстрое включение (3 шага)

### 1. Установить зависимость

```bash
pip install APScheduler==3.10.4
```

### 2. Раскомментировать импорт в main.py

```python
# Было:
# from utils.scheduler import start_scheduler, stop_scheduler

# Стало:
from utils.scheduler import start_scheduler, stop_scheduler
```

### 3. Раскомментировать вызовы и изменить флаг

```python
# Изменить:
ENABLE_SCHEDULER = False

# На:
ENABLE_SCHEDULER = True

# И раскомментировать в функции main():
def main():
    # ...
    if ENABLE_SCHEDULER:
        logger.info("Starting scheduler...")
        start_scheduler(bot)  # Убрать комментарий
    # ...
```

## Что делает планировщик?

- Проверяет дни рождения каждый день в настроенное время (по умолчанию 9:00)
- Отправляет уведомления когда день рождения сегодня
- Отправляет напоминания за N дней (настраивается для каждого дня рождения)
- Автоматически очищает старые записи rate limiter

## Настройка времени уведомлений

В файле `.env`:

```bash
NOTIFICATION_HOUR=9
NOTIFICATION_MINUTE=0
```

## Зачем отключен?

- Упрощает демонстрацию (не нужно ждать назначенного времени)
- Меньше зависимостей при установке
- Легче объяснить базовую функциональность
- Показывает понимание разницы между "код есть" и "код используется"

## Альтернативы планировщику

### Вариант 1: Ручная проверка через команду

```python
@bot.message_handler(commands=['check_birthdays'])
def manual_check(message):
    check_birthdays()  # Вызов вручную
```

### Вариант 2: Внешний cron (Linux)

```bash
# В crontab:
0 9 * * * cd /path/to/bot && python3 -c "from utils.scheduler import check_birthdays; check_birthdays()"
```

### Вариант 3: Celery для больших проектов

Для production с большой нагрузкой лучше использовать Celery + Redis/RabbitMQ.
