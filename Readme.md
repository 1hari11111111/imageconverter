# 🤖 Doc2Media Telegram Bot

Converts images/videos sent as Telegram documents → normal viewable media.

## Features
- Works in private chat (DM) only
- Handles single or multiple files/albums at once
- Live progress: `Processing... (3/10)`
- Auto-deletes original document message after converting
- 50 MB max per file with skip notification
- Webhook mode for Heroku, polling mode for local

## File Structure
├── bot.py
├── config.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md


## Environment Variables
| Variable     | Required    | Description                          |
|--------------|-------------|--------------------------------------|
| BOT_TOKEN    | ✅ Always   | Token from @BotFather                |
| WEBHOOK_URL  | Heroku only | https://your-app-name.herokuapp.com  |
| PORT         | Auto        | Set by Heroku automatically          |

## Notes
- Use Eco dyno (~$5/mo) on Heroku for always-on
- Never commit your real .env file to GitHub
