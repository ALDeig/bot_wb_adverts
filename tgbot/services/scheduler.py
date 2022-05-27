from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from .service import send_update_price
from .db_queries import remove_users_without_subscribe


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def task_sending_notification(bot, session_factory):
    """Задача по отправке уведомления, если товара на складе меньше, чем указал пользователь"""
    await send_update_price(session_factory, bot)


async def task_remove_user_without_subscribe(bot, session_factory):
    """Задача на удаление пользователей без подписки"""
    users = await remove_users_without_subscribe(session_factory)
    for user in users:
        print(user)
        try:
            await bot.send_message(user, "Ваша подписка закончилась. Для дальнейшего использования нажмите /start")
        except Exception as er:
            logger.error(er)


def add_jobs(bot, session_factory):
    # scheduler.add_job(task_sending_notification, "cron", hour=9, args=[bot, session])
    # scheduler.add_job(task_sending_notification, "cron", hour=12, args=[bot, session])
    # scheduler.add_job(task_sending_notification, "cron", hour=20, args=[bot, session])
    scheduler.add_job(task_sending_notification, "interval", minutes=15, args=[bot, session_factory])
    scheduler.add_job(task_remove_user_without_subscribe, "cron", hour=8, args=[bot, session_factory])
    return scheduler
