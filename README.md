# Antifraud Lab

Учебный SOC pipeline на базе FastAPI + PostgreSQL + Loki + Grafana.
Симулирует антифрод систему с real-time мониторингом и алертами в Telegram.

## Архитектура

```
                        Internet
                            │
                       nginx 80/443
                       Let's Encrypt
                            │
              ┌─────────────┼─────────────┐
              │                           │
         /fraud-api/                      /
        FastAPI :8100               Grafana :3001
              │                           │
         PostgreSQL :5433            Loki :3100
              │                           │
           Promtail ◄──── Docker logs ────┘
```

Все внутренние порты слушают только `127.0.0.1`. Наружу открыты только 80/443 через nginx.

## Стек

- **FastAPI** — API сервис с Pydantic валидацией и JSON логированием
- **PostgreSQL** — хранение событий и истории пользователей
- **Loki + Promtail** — сбор и хранение логов
- **Grafana** — дашборд и алерты
- **Docker Compose** — оркестрация 6 сервисов
- **nginx + Let's Encrypt** — reverse proxy с SSL

## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/aadov/antifraud-lab.git
cd antifraud-lab
```

### 2. Создай `.env`

```bash
cp .env.example .env
```

Заполни переменные:

```env
# Telegram алерты
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Grafana SMTP (опционально)
GF_SMTP_ENABLED=true
GF_SMTP_HOST=smtp.gmail.com:587
GF_SMTP_USER=your@gmail.com
GF_SMTP_PASSWORD=your_app_password
GF_SMTP_FROM_ADDRESS=your@gmail.com
GF_SMTP_FROM_NAME=Grafana
GF_SMTP_STARTTLS_POLICY=MandatoryStartTLS
```

Получить `TELEGRAM_CHAT_ID`:

```bash
# Напиши боту любое сообщение, потом:
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
# Ищи "chat":{"id": ЧИСЛО}
```

### 3. Запусти

```bash
docker compose up -d
```

- API: `http://localhost:8100`
- Grafana: `http://localhost:3001` (admin/admin)

## API

### POST /login

Принимает событие входа и возвращает оценку риска.

Пример запроса:

```json
{
  "user_id": "client_001",
  "ip": "185.22.10.11",
  "country": "RU",
  "device": "new",
  "hour": 3,
  "failed_attempts": 4
}
```

Пример ответа:

```json
{
  "risk_score": 95,
  "decision": "BLOCK",
  "reasons": ["new_device", "night_login", "many_failed_attempts", "foreign_country"]
}
```

## Антифрод логика

### Базовые правила

| Правило | Условие | Вес |
|---------|---------|-----|
| new_device | device == "new" | +30 |
| night_login | hour < 6 или hour > 23 | +20 |
| many_failed_attempts | failed_attempts > 3 | +25 |
| foreign_country | country != "KZ" | +20 |

### Контекстные правила (история за 10 минут)

| Правило | Условие | Вес |
|---------|---------|-----|
| impossible_travel | смена страны с KZ на другую | +40 |
| multiple_ips | 3+ разных IP за период | +30 |
| accumulated_failed_attempts | сумма failed_attempts > 10 | +35 |
| bruteforce_detected | более 15 запросов за период | +40 |

### Решения

| Score | Решение |
|-------|---------|
| >= 70 | BLOCK |
| >= 40 | 2FA |
| < 40 | ALLOW |

## Генерация трафика

`seed.sh` симулирует три сценария атак:

```bash
bash seed.sh
```

- **burst** — массовая атака с одного IP
- **impossible_travel** — смена страны за короткое время
- **normal** — легитимный трафик для фона

## Дашборд

Grafana дашборд включает 5 панелей:

| Панель | Описание |
|--------|----------|
| Block\|2FA\|Allow | Распределение решений по времени |
| BLOCK rate % | Процент блокировок |
| TOP IP BLOCK | Источники атак по IP |
| TOP users BLOCK | Пользователи с наибольшим числом блокировок |
| География атак | Распределение по странам |

## Алерты

### Telegram

Алерт `High BLOCK rate` срабатывает когда BLOCK rate превышает 50% за 5 минут.

Настройка через provisioning — токен и chat_id берутся из `.env`:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Конфиги алертов: `provisioning/alerting/`

## Grafana Provisioning

Все настройки Grafana хранятся в репозитории и применяются автоматически при запуске:

| Файл | Назначение |
|------|-----------|
| `provisioning/datasources/loki.yaml` | Datasource Loki с UID `loki` |
| `provisioning/dashboards/dashboard.yaml` | Подключение папки с дашбордами |
| `provisioning/alerting/contactpoints.yaml` | Telegram contact point |
| `provisioning/alerting/rules.yaml` | Правило High BLOCK rate |
| `dashboards/antifraud-dashboard.json` | JSON дашборда |

После обновления на VPS:

```bash
git pull
docker compose up -d --force-recreate grafana
```

## Продакшен (VPS)

Развёрнут на Oracle Cloud, Ubuntu 22.04.

| Сервис | URL |
|--------|-----|
| Grafana | https://antifraud-aadov.duckdns.org/ |
| Dashboard | https://antifraud-aadov.duckdns.org/d/antifraud-lab/antifraud-lab |
| FastAPI | https://antifraud-aadov.duckdns.org/fraud-api/ |

Внутренние порты привязаны к `127.0.0.1` и не доступны напрямую из интернета.
