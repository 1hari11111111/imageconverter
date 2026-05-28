import asyncio
import logging
from telegram.ext import ContextTypes
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

AUTO_DELETE_SECONDS = 5 * 60  # 5 minutes


async def schedule_auto_delete(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    message_ids: list[int],
):
    """Send warning message then delete all messages after 5 minutes."""

    # Send warning to user
    warning = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "⏳ *Heads up!*\n\n"
            "The converted files above will be *automatically deleted in 5 minutes* to protect your privacy.\n\n"
            "📥 *Forward or save them before they're gone!*"
        ),
        parse_mode="Markdown",
    )

    # Wait 5 minutes
    await asyncio.sleep(AUTO_DELETE_SECONDS)

    # Delete all converted media messages
    all_to_delete = message_ids + [warning.message_id]
    for msg_id in all_to_delete:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except TelegramError as e:
            logger.warning("Auto-delete failed for msg %s: %s", msg_id, e)

    # Notify user files are gone
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🗑️ Converted files have been deleted.",
        )
    except TelegramError:
        pass
