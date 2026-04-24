# Client initialize
from llm_client import client, YANDEX_FOLDER_ID

YANDEX_MODEL = "aliceai-llm"

response = client.responses.create(
    model=f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
    input="Придумай 3 необычные идеи для стартапа в сфере путешествий.",
    temperature=0.8,
    max_output_tokens=1500
)

print(response.output[0].content[0].text)