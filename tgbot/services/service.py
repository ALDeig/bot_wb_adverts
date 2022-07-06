import asyncio
from collections import namedtuple

from aiogram import Bot
from httpx import AsyncClient
from sqlalchemy.orm.session import sessionmaker
from tgbot.keyboards import kb_user

from tgbot.keyboards.kb_user import unsubscribe
from .db_queries import delete_tracking, get_all_tracking
from .wb import errors, common, wb, wb_selenium


Notification = namedtuple("Notification", "user_id, text, kb")


async def send_update_price(session_factory: sessionmaker, bot: Bot):
    async with session_factory() as session:
        tracking_list = await get_all_tracking(session)
        users = set(tracking.user_id for tracking in tracking_list)
        list_notifications = []
        async with AsyncClient(headers=common.get_headers(), timeout=common.TIMEOUT) as client:
            for tracking in tracking_list:
                try:
                    if tracking.query_text:
                        # notification_text = await wb.get_adverts_by_query_search(client, tracking.query_text)
                        adverts, positions = await wb.get_adverts_by_query_search(client, tracking.query_text)
                        notification_text = wb_selenium.get_adverts(tracking.query_text, adverts, positions)
                        # notification_text = await ads_by_query.get_adverts(tracking.query_text)
                    else: 
                        notification_text = await wb.get_adverts_by_scu(client, tracking.scu)
                except errors.BadRequestInWB:
                        await delete_tracking(session, tracking.user_id, tracking.query_text, tracking.scu)
                        continue
                kb = unsubscribe("scu" if tracking.scu else "text")
                list_notifications.append(Notification(user_id=tracking.user_id, text=notification_text, kb=kb))
            await asyncio.sleep(1)
    for notification in list_notifications:
        await bot.send_message(notification.user_id, notification.text, reply_markup=notification.kb)
        await asyncio.sleep(0.2)
    for user in users:
        await bot.send_message(user, "Узнать ставки", reply_markup=kb_user.menu)

