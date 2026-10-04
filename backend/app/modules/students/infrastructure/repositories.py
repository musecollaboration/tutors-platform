from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.entities import Subject
from app.modules.users.infrastructure.models import SubjectModel


class SqlAlchemySubjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Subject]:
        rows = await self._session.scalars(select(SubjectModel).order_by(SubjectModel.name))
        return [Subject(id=row.id, name=row.name) for row in rows]
