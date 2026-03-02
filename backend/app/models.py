import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RecipeJob(Base):
    __tablename__ = "recipe_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String, default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    input_path: Mapped[str] = mapped_column(String)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipe_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
