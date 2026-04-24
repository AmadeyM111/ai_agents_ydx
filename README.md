# AI Agents Homework (SHAD)

Практическая работа по агентам: single-agent shopping, memory-agent и multi-agent coordinator с опциональным AI-ранкером на `gpt-oss`.

## Что внутри

- `submission.ipynb` — основной ноутбук для сдачи.
- `llm_client.py` — клиент для OpenAI-compatible API (Yandex AI Studio endpoint).
- `call_aistudio_gpt_oss.py` — smoke-тест реального вызова `gpt-oss`.
- `SESSION_CONTEXT.md` — краткий журнал изменений по этой сессии.

## Структура решения в ноутбуке

В ячейке `Tasks` код сегментирован на блоки:

- `Shared Utils`
- `Task 1: Single-Agent Shopping`
- `Task 2: Memory Agent`
- `Task 3: Multi-Agent Coordination`

Дополнительно:
- `AIRankerAgent` (опционально, через LLM).
- `CoordinatorAgent(use_ai_ranker=True)` для включения AI-ранжирования.
- Edge-case тесты `3.E ... 3.J`.

## Локальный запуск

```bash
cd /Users/amadey/devwork/shad
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install langchain-openai langchain-core openai python-dotenv jupyter
```

Открыть ноутбук:

```bash
jupyter lab
```

## Проверка перед сдачей

1. Запустить ноутбук сверху вниз.
2. Убедиться, что есть `OK 1.A ... OK 3.J`.
3. Убедиться, что в outputs нет ошибок.
4. Сохранить ноутбук с outputs.

## Важно для автопроверки

По условию задания код должен быть в `Tasks`-ячейке.  
Если добавляете служебные ячейки (например, для env/smoke-теста), удалите их перед отправкой, чтобы не сдвигать ожидаемый порядок ячеек.

## Подключение к gpt-oss (опционально)

Создайте `.env`:

```env
YANDEX_FOLDER_ID=...
YANDEX_API_KEY=...
```

Пример smoke-теста:

```bash
cd /Users/amadey/devwork/shad
./.venv/bin/python call_aistudio_gpt_oss.py
```

Модель:

```text
gpt://<YANDEX_FOLDER_ID>/gpt-oss-20b/latest
```

## Ошибка 401 (`UNAUTHENTICATED`)

Если видите `Unknown api key 'YOUR****HERE'`:

- не подхватился реальный ключ (взялся плейсхолдер),
- не задан `YANDEX_FOLDER_ID`,
- kernel не перезапущен после изменения `.env`.

Минимальная проверка в ячейке:

```python
from dotenv import load_dotenv
import os
load_dotenv(override=True)
print(os.getenv("YANDEX_FOLDER_ID"))
print(bool(os.getenv("YANDEX_API_KEY")))
```

## Короткий чеклист сдачи

- [ ] Лишние сервисные ячейки удалены.
- [ ] Код в нужной ячейке `Tasks`.
- [ ] Все `OK` напечатаны.
- [ ] Файл сохранён: `submission.ipynb`.

