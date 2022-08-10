from datetime import date, timedelta

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.orm.session import sessionmaker

from tgbot.models.tables import User, Tracking, PromoCode
from tgbot.services.exceptions import CantAddPromoCode


async def add_new_tracking(session: AsyncSession, user_id: int, query_text: str = None, scu: int = None):
    """Добавляет новое отслеживание"""
    await session.execute(sa.delete(Tracking).where(Tracking.user_id == user_id, Tracking.query_text == query_text,
                                                    Tracking.scu == scu))
    await session.commit()
    tracking = Tracking(user_id=user_id, query_text=query_text, scu=scu)
    session.add(tracking)
    try:
        await session.commit()
        return True
    except DBAPIError:
        await session.rollback()


async def add_user(session: AsyncSession, user_id: int, subscribe: int) -> bool:
    """
    Добавляет нового пользователя
    :param session:
    :param user_id:
    :param subscribe: Количество дней, на сколько активируется подписка у человека
    :return:
    """
    user = User(id=user_id, subscribe=date.today() + timedelta(days=subscribe) if subscribe else None)
    session.add(user)
    try:
        await session.commit()
        return True
    except (IntegrityError, DBAPIError):
        await session.rollback()
        return False


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Возвращает объект пользователя если он есть в базе, иначе None"""
    user = await session.execute(sa.select(User).where(User.id == user_id))
    return user.scalar()


async def delete_user(session: AsyncSession, user_id: int) -> tuple | None:
    """Удаляет пользователя по его id"""
    result = await session.execute(sa.delete(User).where(User.id == user_id).returning("*"))
    await session.commit()
    return result.first()


async def delete_tracking(session: AsyncSession, user_id: int, query_text: str = None, scu: int = None) -> tuple | None:
    """Удаляет отслеживание, которые выбрал пользователь"""
    result = await session.execute(
        sa.delete(Tracking).where(Tracking.user_id == user_id, Tracking.query_text == query_text, Tracking.scu == scu).returning("*")
    )
    await session.commit()
    return result.first()


async def get_users(session: AsyncSession) -> list[User]:
    """Возвращает всех пользователей"""
    users = await session.execute(sa.select(User).order_by(User.id))
    return users.scalars().all()


async def remove_users_without_subscribe(session_factory: sessionmaker):
    """Удаляет пользователей у которых срок подписки меньше сегодняшней даты"""
    async with session_factory() as session:
        result = await session.execute(sa.delete(User).where(User.subscribe.isnot(None), User.subscribe < date.today())\
                              .returning("*"))
        await session.commit()
        return result.scalars().all()


async def get_all_tracking(session: AsyncSession) -> list[Tracking]:
    """Возвращает все отслеживания в базе"""
    tracking = await session.execute(sa.select(Tracking).order_by(Tracking.user_id))
    return tracking.scalars().all()


async def get_tracking_by_user_id(session: AsyncSession, user_id: int) -> list[Tracking] | None:
    """Возвращает отслеживания пользователя"""
    tracking = await session.execute(sa.select(Tracking).where(Tracking.user_id == user_id))
    return tracking.scalars().all()


async def get_promo_code(session: AsyncSession, code: str) -> PromoCode | None:
    code = await session.execute(sa.select(PromoCode).where(PromoCode.code == code))
    return code.scalar()


async def add_promo_code(session: AsyncSession, code: str, user: int, discount_size: int):
    session.add(PromoCode(code=code, user=user, amount_use=0, discount_size=discount_size))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise CantAddPromoCode


async def get_all_promo_code(session: AsyncSession) -> list[PromoCode]:
    codes = await session.execute(sa.select(PromoCode))
    return codes.scalars().all()


async def delete_promo_code(session: AsyncSession, code: str):
    await session.execute(sa.delete(PromoCode).where(PromoCode.code == code))
    await session.commit()


async def increment_amount_use_code(session: AsyncSession, code: str):
    await session.execute(sa.update(PromoCode).where(PromoCode.code == code)
                               .values({"amount_use": PromoCode.amount_use + 1}))
    await session.commit()
