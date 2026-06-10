# zhenya-ai-bot

Telegram-бот с переключаемыми LLM-моделями.
Работает на cloud.ru VM с обходом блокировки Telegram через sing-box VPN.

## Что умеет

- Принимает текстовые сообщения в Telegram
- Передаёт их в выбранную модель Cloud.ru Foundation Models
- Возвращает ответ модели обратно в Telegram
- Поддерживает 7 моделей разных провайдеров: GigaChat, DeepSeek, GPT, GLM, Qwen, MiniMax
- Команда `/model KEY` переключает текущую модель per chat_id
- Логирует каждый вызов: модель, токены, latency

## Стек

- Ubuntu 22.04 на cloud.ru VM
- Python 3.10 + venv
- aiogram 3.x - Telegram Bot API
- httpx - HTTP-клиент для Foundation Models API
- python-dotenv - секреты из .env
- sing-box - VPN-туннель к Telegram (через NovaVPS, Нидерланды)
- systemd - автозапуск бота при ребуте

## Установка с нуля

### 1. Cloud.ru VM
Создать free-tier VM (Ubuntu 22.04, 2 vCPU, 4 ГБ RAM, 30 ГБ диск), привязать SSH-ключ.

### 2. Подключение
```
ssh user1@
```

### 3. Базовые пакеты
```
sudo apt update
sudo apt install -y python3-pip python3-venv git
```

### 4. VPN через sing-box
```
curl -fsSL https://sing-box.app/install.sh | sudo bash
```
Положить конфиг в `/etc/sing-box/config.json` (VLESS+Reality к NovaVPS).
```
sudo systemctl enable sing-box
sudo systemctl start sing-box
```

### 5. Папка проекта и зависимости
```
mkdir ~/zhenya-bot && cd ~/zhenya-bot
python3 -m venv venv
source venv/bin/activate
pip install aiogram openai python-dotenv httpx aiohttp-socks
```

### 6. Секреты в .env
Создать файл `~/zhenya-bot/.env`:
```
TELEGRAM_BOT_TOKEN=
CLOUDRU_FM_KEY=
```

### 7. systemd-сервис
Положить файл в `/etc/systemd/system/zhenya-bot.service`, затем:
```
sudo systemctl daemon-reload
sudo systemctl enable zhenya-bot
sudo systemctl start zhenya-bot
```

## Команды бота

- `/start` - приветствие
- `/models` - список доступных моделей
- `/model KEY` - переключить модель (например `/model deepseek`)
- любой текст - вопрос модели, она ответит

## Архитектура

```
Telegram ← (VPN sing-box) ← bot.py
                                ↓
                           Foundation Models API
                           (foundation-models.api.cloud.ru)
```

- Telegram-трафик: VM → sing-box → NovaVPS Нидерланды → api.telegram.org
- LLM-трафик: VM → foundation-models.api.cloud.ru (напрямую, без VPN)

## Логи

- `bot.log` в папке проекта - собственный лог с метриками вызовов
- `journalctl -u zhenya-bot` - системный лог systemd

## Автор

Евгения, практика 2026.
