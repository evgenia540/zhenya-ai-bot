import os
import httpx
from dotenv import load_dotenv

load_dotenv()
FM_KEY = os.environ["CLOUDRU_FM_KEY"]
HEADERS = {"Authorization": f"Bearer {FM_KEY}"}

print("=== GET /v1/models ===")
r = httpx.get(
    "https://foundation-models.api.cloud.ru/v1/models",
    headers=HEADERS,
    timeout=15
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Total models available: {len(items)}")
    for m in items[:30]:
        print(f"  - {m.get('id')}")
else:
    print(f"Body: {r.text[:300]}")

print()
print("=== Testing cheap models ===")
MODELS_TO_TRY = [
    "openai/gpt-oss-20b",
    "ai-sage/GigaChat3-10B-A1.8B",
    "deepseek-ai/DeepSeek-V3",
    "qwen/Qwen3-30B-A3B",
]
PAYLOAD = {
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 10
}
for model in MODELS_TO_TRY:
    try:
        r = httpx.post(
            "https://foundation-models.api.cloud.ru/v1/chat/completions",
            headers=HEADERS,
            json={"model": model, **PAYLOAD},
            timeout=15
        )
        print(f"{model}: status={r.status_code}, body={r.text[:120]}")
    except Exception as e:
        print(f"{model}: error={e}")
