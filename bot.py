import asyncio
import logging
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError
from config import (
    BOT_TOKEN,
    WEBHOOK_URL,
    PORT,
    MAX_FILE_SIZE,
    SUPPORTED_IMAGE_MIMES,
    SUPPORTED_VIDEO_MIMES,
    MEDIA_GROUP_COLLECT_DELAY,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

media_group_buffer: dict[str, list] = defaultdict(list)
media_group_tasks: dict[str, asyncio.Task] = {}


async def process_group(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    group_key: str,
    status_message_id: int,
):
    items = media_group_buffer.pop(group_key, [])
    media_group_tasks.pop(group_key, None)

    if not items:
        return

    total = len(items)

    async def update_status(current: int):
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message_id,
                text=f"⚙️ Processing... ({current}/{total})",
            )
        except TelegramError:
            pass

    photos: list[InputMediaPhoto] = []
    videos: list[InputMediaVideo] = []
    skipped: list[str] = []
    original_message_ids: list[int] = []

    for idx, item in enumerate(items, start=1):
        await update_status(idx)
        file_id = item["file_id"]
        mime = item.get("mime_type", "")
        file_size = item.get("file_size", 0)
        file_name = item.get("file_name", "file")
        original_message_ids.append(item["message_id"])

        if file_size and file_size > MAX_FILE_SIZE:
            skipped.append(f"❌ `{file_name}` exceeds 50 MB limit")
            continue

        if mime not in SUPPORTED_IMAGE_MIMES and mime not in SUPPORTED_VIDEO_MIMES:
            skipped.append(f"❌ `{file_name}` — unsupported type (`{mime}`)")
            continue

        try:
            tg_file = await context.bot.get_file(file_id)
            file_bytes = await tg_file.download_as_bytearray()
        except TelegramError as e:
            logger.error("Download error: %s", e)
            skipped.append(f"❌ `{file_name}` — download failed")
            continue

        if mime in SUPPORTED_IMAGE_MIMES:
            photos.append(InputMediaPhoto(media=bytes(file_bytes)))
        else:
            videos.append(InputMediaVideo(media=bytes(file_bytes)))

    all_media = photos + videos
    sent_ok = 0

    for i in range(0, len(all_media), 10):
        chunk = all_media[i : i + 10]
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=chunk)
            sent_ok += len(chunk)
        except TelegramError as e:
            logger.error("Send error: %s", e)
            skipped.append(f"❌ Failed to send a batch: {e}")

    for msg_id in set(original_message_ids):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except TelegramError as e:
            logger.warning("Could not delete message %s: %s", msg_id, e)

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=status_message_id)
    except TelegramError:
        pass

    if skipped:
        summary = (
            f"✅ Converted {sent_ok}/{total} file(s).\n\n"
            + "\n".join(skipped)
        )
        await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if chat.type != "private":
        return

    doc = message.document
    if not doc:
        return

    mime = doc.mime_type or ""
    if mime not in SUPPORTED_IMAGE_MIMES and mime not in SUPPORTED_VIDEO_MIMES:
        await message.reply_text(
            f"⚠️ Unsupported file type: `{mime}`\nSupported: JPEG, PNG, WEBP, GIF, BMP, MP4, MKV, MOV, AVI, WEBM",
            parse_mode="Markdown",
        )
        return

    item = {
        "file_id": doc.file_id,
        "mime_type": mime,
        "file_size": doc.file_size,
        "file_name": doc.file_name or "file",
        "message_id": message.message_id,
    }

    group_id = message.media_group_id
    group_key = group_id if group_id else f"single_{chat.id}_{message.message_id}"

    media_group_buffer[group_key].append(item)

    if group_key in media_group_tasks:
        media_group_tasks[group_key].cancel()

    if len(media_group_buffer[group_key]) == 1:
        status_msg = await context.bot.send_message(
            chat_id=chat.id,
            text="⚙️ Processing... (0/?)",
        )
        context.chat_data[f"status_{group_key}"] = status_msg.message_id

    status_message_id = context.chat_data.get(f"status_{group_key}")

    async def delayed_process():
        await asyncio.sleep(MEDIA_GROUP_COLLECT_DELAY)
        await process_group(context, chat.id, group_key, status_message_id)

    task = asyncio.create_task(delayed_process())
    media_group_tasks[group_key] = task


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Send me images or videos *as documents/files* and I'll convert them to normal media.\n\n"
        "✅ Supports: JPEG, PNG, WEBP, GIF, BMP, MP4, MKV, MOV, AVI, WEBM\n"
        "📦 Send multiple files at once — I'll handle them all!\n"
        "⚠️ Max file size: 50 MB per file",
        parse_mode="Markdown",
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/start"), start))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_document))

    if WEBHOOK_URL:
        logger.info("Starting webhook on port %s", PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            url_path=BOT_TOKEN,
        )
    else:
        logger.info("Starting polling (local mode)")
        app.run_polling()


if __name__ == "__main__":
    main()
