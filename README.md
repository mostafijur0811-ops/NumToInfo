# 📱 Number To Country Info Bot

A Telegram bot that identifies the **country** behind a phone number's
international calling code, and shows rich, publicly available country
information — capital, currency, timezone, population, and more.

> ⚠️ **Privacy by design:** this bot never reveals or attempts to look up
> the phone's owner, carrier, IMEI, SIM details, address, email, or live
> location. It only maps a **calling code / region** (e.g. `+880` →
> Bangladesh) to public country data.

---

## ✨ Features

- 🔎 Parses any phone number (with or without `+`) using `phonenumbers`
- 🌍 Resolves the country via `pycountry` + the free REST Countries API
- 🕒 Shows the current local time for the country using `pytz`
- 🎛 Inline keyboard menu (`Search Number`, `Help`, `About`)
- 🚦 Simple in-memory per-user rate limiter
- 🧱 Fully modular, typed, and commented codebase
- 🪵 Structured logging
- 🛡 Robust error handling — the bot never crashes on bad input or API errors
- 🗄 No database required

---

## 📁 Project Structure

```
number-to-country-bot/
├── main.py           # Entry point: handlers, application setup, polling loop
├── country.py         # Phone parsing + country lookup (phonenumbers/pycountry/pytz/API)
├── utils.py            # Rate limiter + message formatting helpers
├── keyboard.py         # Inline keyboard layouts
├── config.py            # Env vars + logging configuration
├── requirements.txt      # Python dependencies
├── .env.example            # Example environment file
└── README.md
```

---

## 🚀 1. Create Your Telegram Bot

1. Open Telegram and message **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot` and follow the prompts (choose a name and username).
3. BotFather will give you a **bot token** that looks like:
   `123456789:ABCdefGhIJKlmNoPQRstuVwxYZ`
4. Keep this token secret — it's your `BOT_TOKEN`.

---

## 🛠 2. Installation (Local)

**Requirements:** Python 3.13+

```bash
# Clone / copy the project, then enter the folder
cd number-to-country-bot

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔑 3. Set BOT_TOKEN

Copy the example env file and fill in your token:

```bash
cp .env.example .env
```

Edit `.env`:

```
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVwxYZ
```

Alternatively, export it directly in your shell (no `.env` needed):

```bash
export BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRstuVwxYZ"   # Linux/macOS
setx BOT_TOKEN "123456789:ABCdefGhIJKlmNoPQRstuVwxYZ"      # Windows
```

---

## ▶️ 4. Run Locally

```bash
python main.py
```

You should see log output like:

```
... | INFO | number2country | Starting Number To Country Info Bot...
```

Open Telegram, find your bot, send `/start`, then send a phone number such
as `+8801712345678`.

---

## ☁️ 5. Deploy to Koyeb

1. Push this project to a GitHub repository.
2. Go to [Koyeb](https://www.koyeb.com/) → **Create App** → connect your
   GitHub repo.
3. Choose **Dockerfile** or **Buildpack** deployment:
   - If using a buildpack, set the **Run command** to:
     ```
     python main.py
     ```
4. Under **Environment Variables**, add:
   - `BOT_TOKEN` = your bot token
5. Deploy. Koyeb will keep the process running continuously (long polling
   works fine on a persistent worker/service instance).

> Optional `Dockerfile` if you prefer container-based deployment:
> ```dockerfile
> FROM python:3.13-slim
> WORKDIR /app
> COPY requirements.txt .
> RUN pip install --no-cache-dir -r requirements.txt
> COPY . .
> CMD ["python", "main.py"]
> ```

---

## 🚂 6. Deploy to Railway

1. Push the project to GitHub.
2. Go to [Railway](https://railway.app/) → **New Project** → **Deploy from
   GitHub repo**.
3. Railway auto-detects Python. Under **Settings → Deploy**, set the
   **Start Command** to:
   ```
   python main.py
   ```
4. Under **Variables**, add:
   - `BOT_TOKEN` = your bot token
5. Deploy — Railway runs the bot as a persistent worker.

---

## 🎨 7. Deploy to Render

1. Push the project to GitHub.
2. Go to [Render](https://render.com/) → **New** → **Background Worker**
   (recommended for long-polling bots, since it doesn't need an open HTTP
   port).
3. Connect your repo, set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. Under **Environment**, add:
   - `BOT_TOKEN` = your bot token
5. Deploy.

---

## 🧩 Commands

| Command  | Description                      |
|----------|-----------------------------------|
| `/start` | Welcome message with menu buttons |
| `/help`  | Usage instructions                |
| `/about` | About the bot & tech stack        |

## 💬 Usage

Just send a number in any of these formats:

```
+8801712345678
8801712345678
+919876543210
```

The bot replies with a formatted card of public country information. If the
number can't be parsed, it replies:

```
❌ Invalid phone number.
```

---

## 🔒 Data & Privacy Notice

This bot performs **country-code lookup only**. It does not, and cannot,
determine:

- Owner name or identity
- SIM/carrier owner
- Real-time or historical location
- Carrier name
- Address, email, or IMEI
- Any other personal data

All information shown is public, country-level data sourced from the free
[REST Countries API](https://restcountries.com/).

---

## 🧪 Tech Stack

- Python 3.13
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21+
- [phonenumbers](https://pypi.org/project/phonenumbers/)
- [pycountry](https://pypi.org/project/pycountry/)
- [pytz](https://pypi.org/project/pytz/)
- [requests](https://pypi.org/project/requests/)

## 📄 License

Free to use and modify for personal or commercial projects.
