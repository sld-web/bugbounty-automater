"""Skill progression model for tracking hunter's skill development over time."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.program import Program


class SkillProgression(BaseModel):
    """Tracks hunter's skill progression in different vulnerability types and techniques."""
    __tablename__ = "skill_progression"

    # Optional: link to a specific program or target if we want to track per-program skills
    program_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("programs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    skill_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    proficiency_level: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    practice_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Optional: notes or examples of successful applications
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="skill_progressions")

    def update_proficiency(self) -> None:
        """Update proficiency level based on success rate."""
        if self.practice_count > 0:
            self.proficiency_level = self.success_count / self.practice_count
        else:
            self.proficiency_level = 0.0
        self.last_practiced = datetime.utcnow()

    def record_practice(self, success: bool = False) -> None:
        """Record a practice attempt."""
        self.practice_count += 1
        if success:
            self.success_count += 1
        self.update_proficiency()

    def get_mastery_level(self) -> str:
        """Get a human-readable mastery level."""
        if self.proficiency_level >= 0.9:
            return "Expert"
        elif self.proficiency_level >= 0.7:
            return "Advanced"
        elif self.proficiency_level >= 0.4:
            return "Intermediate"
        elif self.proficiency_level > 0:
            return "Beginner"
        else:
            return "Novice"