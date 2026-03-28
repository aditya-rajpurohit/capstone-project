import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.metadata.models.data_source import DataSourceConfigModel
from app.database.metadata.session import get_async_session
from app.database.metadata.snapshot_refresher import SnapshotRefresher
from app.database.registry.database_registry import DatabaseRegistry


class DatasourceService:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._Session = sessionmaker or get_async_session()
        self._snapshot_refresher = SnapshotRefresher()

    async def register_postgres(
        self,
        *,
        name: str,
        config: dict,
    ) -> DataSourceConfigModel:
        async with self._Session() as session:
            # check duplicate name
            stmt = select(DataSourceConfigModel).where(
                DataSourceConfigModel.name == name
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError("Datasource with this name already exists")

            # create model
            ds = DataSourceConfigModel(
                id=uuid.uuid4(),
                name=name,
                dialect="POSTGRES",
                host=config["host"],
                port=config["port"],
                database_name=config["database_name"],
                username=config["username"],
                encrypted_password=config["password"],  # TODO: encrypt later
                is_active=True,
            )

            session.add(ds)
            await session.commit()
            await session.refresh(ds)

        # 🔥 Load into registry immediately
        registry = DatabaseRegistry.get_instance()
        async with self._Session() as session:
            await registry.load_from_appdb(session)

        # 🔥 Create initial snapshot
        async with self._Session() as session:
            await self._snapshot_refresher.refresh(
                session=session,
                data_source_id=str(ds.id),
            )

        return ds

    async def list_datasources(self):
        async with self._Session() as session:
            stmt = select(DataSourceConfigModel)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_datasource(self, datasource_id: str):
        async with self._Session() as session:
            stmt = select(DataSourceConfigModel).where(
                DataSourceConfigModel.id == uuid.UUID(datasource_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def delete_datasource(self, datasource_id: str) -> bool:
        async with self._Session() as session:
            stmt = select(DataSourceConfigModel).where(
                DataSourceConfigModel.id == uuid.UUID(datasource_id)
            )
            result = await session.execute(stmt)
            ds = result.scalar_one_or_none()

            if not ds:
                return False

            await session.delete(ds)
            await session.commit()

        # reload registry
        registry = DatabaseRegistry.get_instance()
        async with self._Session() as session:
            await registry.load_from_appdb(session)

        return True
