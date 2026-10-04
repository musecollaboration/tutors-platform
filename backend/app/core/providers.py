from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, settings
from app.core.db import SessionFactory
from app.core.ports import UnitOfWork
from app.core.unit_of_work import SqlAlchemyUnitOfWork


class CoreProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def provide_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return SessionFactory

    @provide(scope=Scope.REQUEST)
    async def provide_session(self, factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def provide_uow(self, session: AsyncSession) -> UnitOfWork:
        return SqlAlchemyUnitOfWork(session=session)
