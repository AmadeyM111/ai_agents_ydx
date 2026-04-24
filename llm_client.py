import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


print("ENV CHECK:")
print("FOLDER:", YANDEX_FOLDER_ID)
print("KEY:", OPENAI_API_KEY is not None)

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден. Проверь .env")

import openai

client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    project=YANDEX_FOLDER_ID,
    base_url="https://ai.api.cloud.yandex.net/v1"
)

__all__ = ["client", "YANDEX_FOLDER_ID"]