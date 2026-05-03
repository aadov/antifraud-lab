## Быстрый старт

```bash
git clone https://github.com/aadov/antifraud-lab.git
cd antifraud-lab
docker compose up -d
```

API доступен на `http://localhost:8100`
Grafana доступна на `http://localhost:3001` (admin/admin)

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

## Дашборд

Grafana дашборд включает 5 панелей:

- **Block/2FA/Allow** - распределение решений по времени
- **BLOCK rate %** - процент блокировок
- **TOP IP** - источники атак по IP
- **TOP users** - пользователи с наибольшим числом блокировок
- **География** - распределение атак по странам

## Grafana provisioning

Настройки Grafana хранятся в репозитории и автоматически применяются при запуске контейнера:

- `provisioning/datasources/loki.yaml` создает datasource Loki со стабильным UID `loki`
- `provisioning/dashboards/dashboard.yaml` подключает папку с JSON-дашбордами
- `dashboards/antifraud-dashboard.json` содержит дашборд Antifraud Lab

После обновления на VPS применить настройки можно так:

```bash
git pull
docker compose up -d --force-recreate grafana
```

Если Grafana уже была запущена со старым volume и дашборд не обновился, перезапусти только Grafana. Удалять `grafana_data` обычно не нужно.
