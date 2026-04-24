from llm_client import client, YANDEX_FOLDER_ID
import openai

YANDEX_MODEL = "gpt-oss-20b/latest"

response = client.responses.create(
  model=f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
  temperature=0.3,
  instructions="",
  input="Придумай 3 необычные идеи для стартапа в сфере путешествий.",
  max_output_tokens=500
)

print(response.output_text)