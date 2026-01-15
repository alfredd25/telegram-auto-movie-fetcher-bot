# 🎬 Telegram Movie Search Bot

A production-ready Telegram bot that enables fast, keyword-based movie search from a large Telegram database channel using **metadata-only indexing**.
Designed to scale to **80k+ files**, with pagination, auto-delete for copyright safety, and admin-controlled advertisements — all without copying or storing media.

---

## ✨ Features

* 🔍 **Keyword-based movie search**
* ⚡ **Fast search using indexed metadata (no live scanning)**
* 📄 **Pagination** (Next / Previous buttons)
* 👋 **User tagging & greeting message**
* 🧹 **Auto-delete search results after 2 minutes**
* 📢 **Admin-configurable advertisement/footer**
* 🧠 **Resume-safe indexing for large channels**
* 🚫 **No media downloading or duplication**
* 🔄 **Works with test channel → production channel via config change**

---

## 🧠 How It Works (High Level)

1. The bot is added as an admin to a **database channel** (source of movie files).
2. A **one-time indexing process** scans historical messages and stores only:

   * File name
   * File size
   * Message ID
   * File ID
   * Searchable keywords
3. When a user searches:

   * The bot queries the indexed database
   * Fetches matching files dynamically from the DB channel
   * Posts results to the client channel with pagination
4. All result messages are **automatically deleted after 2 minutes**.

📌 **Important:**
No movie files are ever copied or stored by the bot.

---

## 🏗️ Project Structure

```
.
├── app/
│   ├── bot/                # Telegram bot handlers
│   ├── db/                 # Database models & queries
│   ├── indexer/            # Telethon indexing logic
│   ├── utils/              # Config, logging, helpers
│
├── telethon_scanner.py     # Initial indexing script
├── main.py                 # Bot entry point
├── .env.example            # Environment variable template
├── .gitignore
└── README.md
```

---

## ⚙️ Tech Stack

* **Python 3.10+**
* **python-telegram-bot** (Bot interactions)
* **Telethon** (Channel indexing)
* **MongoDB** (Metadata storage)
* **Telegram Channels** (DB channel + client channel)

---

## 🔐 Environment Configuration

Create a `.env` file (do **not** commit it):

```env
BOT_TOKEN=
TG_API_ID=
TG_API_HASH=
MONGO_URI=
DB_CHANNEL_ID=
CLIENT_CHANNEL_ID=
```

Refer to `.env.example` for required variables.

---

## 🚀 Setup & Usage

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2️⃣ Run Initial Indexing

This is a **one-time process** (or resumable if interrupted):

```bash
python telethon_scanner.py
```

* Safe for large channels (80k+ files)
* Resume-safe
* Metadata only

---

### 3️⃣ Start the Bot

```bash
python main.py
```

The bot is now live.

---

## 🧑‍💼 Admin Commands

| Command           | Description                         |
| ----------------- | ----------------------------------- |
| `/set_ad <text>`  | Set or update the ad/footer message |
| `/search <movie>` | Search for a movie                  |

Admins can change the ad **without redeploying the bot**.

---

## ⏱ Auto-Delete Policy

* All movie result messages are deleted after **2 minutes**
* Reduces copyright exposure
* Keeps channels clean

---

## ⚠️ Important Notes

* The bot **depends on continued access** to the database channel.
* If DB channel access is revoked, search functionality will stop.
* This is outside the developer’s control.
* Indexing stores **no media files**, only metadata.

---

## 🧪 Testing Workflow

1. Use a **test DB channel** with sample files
2. Validate:

   * Search
   * Pagination
   * Auto-delete
   * Ads
3. Switch to production DB channel by updating environment variables only

No code changes required.

---

## 📦 Deployment

* Designed to run on:

  * VPS
  * RDP
  * Cloud server
* MongoDB Atlas recommended
* Bot should run as a background service or task

---

## 🛡️ Security

* Secrets stored via environment variables
* MongoDB protected via authentication
* `.gitignore` prevents accidental leaks

---

## 📄 License

This project is intended for **private/client use**.
Redistribution or resale without permission is not allowed.

---

## 🤝 Support

For setup, deployment, or feature extensions, contact the developer.

---
