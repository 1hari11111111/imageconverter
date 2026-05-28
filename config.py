import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set! Check your .env or Heroku config vars.")

WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")
PORT: int = int(os.environ.get("PORT", 5000))

MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB

SUPPORTED_IMAGE_MIMES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
}

SUPPORTED_VIDEO_MIMES: set[str] = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
}

MEDIA_GROUP_COLLECT_DELAY: float = 1.5
