# Lunar Run — Симулятор лунных доставок

Пошаговая стратегия: вы управляете базой **«Скол-9»** и тремя роверами, выполняете заказы на доставку по четырём зонам Луны. Нужно балансировать риск, заряд батареи, грузоподъёмность и рейтинг базы.

Игра длится **15 дней**. Цель — не дать рейтингу обнулиться и набрать максимальный итоговый счёт:

```text
score = деньги + рейтинг × 5
```

---

## Как запустить

### Требования
- Python 3.10+
- Node.js 18+ и npm

### Backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Важно: запускать из папки backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173  
(Vite проксирует `/api` → `http://localhost:8000`)

### Сброс игры
`POST /api/reset` или кнопка «Новая игра» в интерфейсе.

---

## Что сделано

Полноценный fullstack-проект с чистой архитектурой.

| Слой | Технологии |
|------|------------|
| Backend | FastAPI, SQLite, Pydantic |
| Frontend | React 18 + Vite, чистый CSS |
| Данные | SQLite (`backend/lunar_run.db`) |

**Реализовано:**
- 4 зоны Луны с разным риском, стоимостью батареи и множителем награды
- 3 ровера с уникальными характеристиками (батарея + грузоподъёмность)
- Генерация 2–3 заказов в день (вес, срочность, награда)
- Проверка возможности отправки (вес ≤ capacity, батарея ≥ cost)
- Аварии по риску зоны → ровер ломается на 2 дня
- Платный и автоматический ремонт
- Подзарядка idle-роверов каждый день
- Просрочка заказов → штраф рейтинга
- Журнал событий, карта Луны, детали заказа, список роверов
- Конец игры: рейтинг ≤ 0 или день > 15

**Архитектура backend (слои):**
- `api/` — HTTP-эндпоинты
- `services/` — бизнес-логика (Game, Rover, Order, Delivery)
- `repositories/` — работа с SQLite
- `models/` — доменные сущности и Enum
- `core/` — конфиг, зоны, зависимости
- `schemas/` — Pydantic-схемы запросов
- `db/` — подключение к БД

---

## Логика веса / риска / доставки

### Зоны (`app/core/zones.py`)

| ID | Название | Риск | base_cost | reward_mult |
|----|----------|------|-----------|-------------|
| z1 | Море Спокойствия | 5 % | 15 | 1.0 |
| z2 | Кратер Тихо | 15 % | 30 | 1.4 |
| z3 | Тёмная сторона | 30 % | 55 | 2.0 |
| z4 | Равнина Заката | 10 % | 22 | 1.2 |

### Расход батареи
```text
cost = round(zone.base_cost + weight × 1.6)
```
Ровер может взять заказ только если `cost ≤ battery` **и** `weight ≤ cargo_capacity`.

### Награда за заказ
```text
reward = round(weight × 6 × zone.reward_mult + (6 − urgency_days) × 14 + random(0…18))
```
- `urgency_days` ∈ [2; 5]
- дедлайн = день создания + urgency

### «Невозможные» заказы
С вероятностью **12 %** генерируется заказ с весом 37–48 кг (больше максимальной грузоподъёмности любого ровера). Выполнить нельзя — игнорируй или жди просрочки.

### Исход доставки (при `advance_day`)

1. **Для каждого ровера в статусе `delivering`:**
   - с вероятностью `zone.risk` → **авария**:
     - заказ → `failed`
     - ровер → `broken`, `repair_days_left = 2`
     - рейтинг − (8 + risk × 20)
   - иначе → **успех**:
     - заказ → `completed`
     - деньги += reward
     - рейтинг += 2
     - батарея − `pending_cost`

2. **Автоматический ремонт:** каждый день `repair_days_left −= 1`. При 0 ровер возвращается в `idle` с **40 %** батареи.

3. **Платный ремонт** (`POST /api/repair`): 60 кредитов → сразу `idle` с **60 %** батареи.

4. **Idle-роверы** подзаряжаются на **30 %** от max каждый день.

5. **Просроченные** `pending`-заказы (deadline ≤ текущий день) → `expired`, рейтинг −5.

### Роверы

| ID | Имя | Батарея max | Грузоподъёмность |
|----|-----|-------------|------------------|
| r1 | Улитка-1 | 100 | 20 кг |
| r2 | Барсук-2 | 140 | 35 кг |
| r3 | Сокол-3 | 85 | 15 кг |

---

## Где хранятся данные

Всё состояние игры — в **SQLite**-файле:

```
backend/lunar_run.db
```

| Таблица | Содержимое |
|--------|------------|
| `game_state` | день, деньги, рейтинг, game_over, счётчик заказов |
| `rovers` | текущее состояние каждого ровера |
| `orders` | все заказы (pending / in_transit / completed / failed / expired) |
| `deliveries` | история доставок |
| `events` | журнал событий (клиенту отдаются последние 60) |

Зоны и шаблоны роверов — константы в `app/core/zones.py` (не в БД).

Frontend хранит только UI-состояние (выбранный заказ/ровер) в React-хуках. Всё игровое состояние приходит с `GET /api/state`.

---

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/state` | Полное состояние игры |
| POST | `/api/reset` | Новая игра |
| POST | `/api/send` | `{ "order_id", "rover_id" }` — отправить ровер |
| POST | `/api/repair` | `{ "rover_id" }` — платный ремонт |
| POST | `/api/advance_day` | Перейти к следующему дню |
| GET | `/api/health` | Health-check |

---

## Что использовали из AI

В самом проекте **нет вызовов LLM / ML-моделей**. Вся логика — детерминированные правила + `random`.

При разработке использовались AI-ассистенты (генерация структуры FastAPI + React, подсказки по формулам баланса, оформление UI, рефакторинг на слои). Итоговый код — чистый Python/JS без внешних AI-API.

---

## Структура проекта

```
lunar-delivery/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Точка входа FastAPI
│   │   ├── api/v1/endpoints.py     # HTTP-эндпоинты
│   │   ├── core/
│   │   │   ├── config.py           # Константы баланса
│   │   │   ├── zones.py            # Зоны и шаблоны роверов
│   │   │   └── dependencies.py     # DI
│   │   ├── db/database.py          # SQLite
│   │   ├── models/                 # Domain models + Enums
│   │   ├── repositories/           # Доступ к данным
│   │   ├── services/               # Бизнес-логика
│   │   │   ├── game_service.py
│   │   │   ├── rover_service.py
│   │   │   ├── order_service.py
│   │   │   └── delivery_service.py
│   │   └── schemas/                # Pydantic-запросы
│   ├── requirements.txt
│   └── lunar_run.db                # Создаётся при первом запуске
│
└── frontend/
    ├── src/
    │   ├── components/             # App, MoonMap, RoverList, OrderDetail, EventLog…
    │   ├── hooks/                  # useGame, useActions, useSelection
    │   ├── api/                    # HTTP-клиент
    │   ├── utils/
    │   └── styles/
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## Скрины работы

<img width="1400" height="891" alt="image" src="https://github.com/user-attachments/assets/bd2dfd47-a44f-4aa9-884f-0ed765e37d88" />
<img width="1412" height="869" alt="image" src="https://github.com/user-attachments/assets/8d574fad-00c9-49fe-8379-8fd6e60f8630" />
<img width="1397" height="864" alt="image" src="https://github.com/user-attachments/assets/b3409173-32cd-4b4b-bbcc-ac89a4c37be7" />
<img width="1316" height="856" alt="image" src="https://github.com/user-attachments/assets/bdb4ac9a-4b4d-4a55-9475-a18af6dce442" />
<img width="1383" height="849" alt="image" src="https://github.com/user-attachments/assets/d75c0a2f-c80b-4a2e-94b0-7210d2e06e56" />

---

Удачной миссии на Луне! 🌕
