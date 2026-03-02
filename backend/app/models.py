from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="uploaded")
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    vision_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recipe_json: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
