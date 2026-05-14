from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, select
from datetime import datetime
from config.settings import settings

engine = create_async_engine(settings.db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ModelRecord(Base):
    """Tracks which model is active and logs switches."""
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_key: Mapped[str] = mapped_column(String(128))
    switched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    switched_by: Mapped[str] = mapped_column(String(64), default="system")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_active_model() -> str | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelRecord).order_by(ModelRecord.switched_at.desc()).limit(1)
        )
        record = result.scalar_one_or_none()
        return record.model_key if record else None


async def record_model_switch(model_key: str, switched_by: str = "api") -> None:
    async with AsyncSessionLocal() as session:
        session.add(ModelRecord(model_key=model_key, switched_by=switched_by))
        await session.commit()
