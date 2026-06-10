import asyncio
import logging
import os
import time
import httpx
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
FM_KEY = os.environ["CLOUDRU_FM_KEY"]

MODELS = {
    "gigachat": "ai-sage/GigaChat3-10B-A1.8B",
    "deepseek": "deepseek-ai/DeepSeek-V3",
    "gpt-oss":  "openai/gpt-oss-20b",
    "gpt-nano": "openai/gpt-5.4-nano",
    "glm":      "zai-org/GLM-5.1",
    "qwen":     "Qwen/Qwen3-Coder-Next",
    "minimax":  "MiniMaxAI/MiniMax-M2.5",
}
DEFAULT_KEY = "gigachat"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("bot")

chat_models = {}

session = AiohttpSession(proxy="socks5://127.0.0.1:1080")
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

http = httpx.AsyncClient(
    base_url="https://foundation-models.api.cloud.ru/v1",
    headers={"Authorization": f"Bearer {FM_KEY}"},
    timeout=60,
)

def current_model(chat_id: int) -> str:
    return MODELS[chat_models.get(chat_id, DEFAULT_KEY)]

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    log.info(f"start chat_id={message.chat.id} user={message.from_user.full_name}")
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        f"Я бот с {len(MODELS)} моделями. По умолчанию: {MODELS[DEFAULT_KEY]}\n\n"
        f"/models - список моделей\n"
        f"/model KEY - переключить (например /model deepseek)\n\n"
        f"Просто напиши вопрос."
    )

@dp.message(Command("models"))
async def cmd_models(message: types.Message):
    cur = chat_models.get(message.chat.id, DEFAULT_KEY)
    lines = ["Доступные модели:", ""]
    for k, m in MODELS.items():
        mark = "  *** текущая" if k == cur else ""
        lines.append(f"{k} -> {m}{mark}")
    lines.append("")
    lines.append("Переключить: /model KEY")
    await message.answer("\n".join(lines))

@dp.message(Command("model"))
async def cmd_model(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if not parts[1:]:
        await message.answer("Использование: /model KEY (см. /models)")
        return
    key = parts[1].strip()
    if key not in MODELS:
        await message.answer(f"Неизвестная модель '{key}'. Доступные: {', '.join(MODELS.keys())}")
        return
    chat_models[message.chat.id] = key
    log.info(f"model_switch chat_id={message.chat.id} key={key} model={MODELS[key]}")
    await message.answer(f"Переключила на: {MODELS[key]}")

@dp.message()
async def chat(message: types.Message):
    if not message.text:
        await message.answer("Я понимаю только текст.")
        return
    model = current_model(message.chat.id)
    prompt = message.text
    start = time.monotonic()
    try:
        r = await http.post("/chat/completions", json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
        })
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if r.status_code != 200:
            log.warning(f"api_error chat_id={message.chat.id} model={model} status={r.status_code} latency_ms={elapsed_ms}")
            await message.answer(f"Ошибка API ({r.status_code}): {r.text[:200]}")
            return
        data = r.json()
        usage = data.get("usage", {})
        prompt_tok = usage.get("prompt_tokens", 0)

        completion_tok = usage.get("completion_tokens", 0)
        answer = data["choices"][0]["message"]["content"] or "(пустой ответ)"
        log.info(
            f"chat chat_id={message.chat.id} model={model} "
            f"prompt_len={len(prompt)} prompt_tok={prompt_tok} "
            f"completion_tok={completion_tok} latency_ms={elapsed_ms}"
        )
        await message.answer(answer)
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log.exception(f"exception chat_id={message.chat.id} model={model} latency_ms={elapsed_ms}")
        await message.answer(f"Ошибка: {type(e).__name__}: {e}")

async def main():
    log.info(f"bot starting, {len(MODELS)} models, default={DEFAULT_KEY}")
    try:
        await dp.start_polling(bot)
    finally:
        await http.aclose()
        log.info("bot stopped")

if __name__ == "__main__":
    asyncio.run(main())