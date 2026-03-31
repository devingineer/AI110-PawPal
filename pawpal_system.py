from dataclasses import dataclass, field
from typing import Optional

VALID_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Pet:
    name: str
    species: str
    needs: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    preferred_time_of_day: Optional[str] = None  # "morning", "afternoon", "evening"

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")

    def is_high_priority(self) -> bool:
        pass


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferred_start_time: str = "08:00",
        preferences: Optional[dict] = None,
    ):
        self.name = name
        self.available_minutes = available_minutes
        self.preferred_start_time = preferred_start_time
        self.preferences: dict = preferences or {}  # e.g. {"no_walks_after": "20:00"}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[dict] = field(default_factory=list)
    skipped_tasks: list[dict] = field(default_factory=list)  # tasks excluded + reason why
    total_minutes_used: int = 0
    explanations: list[str] = field(default_factory=list)

    def display(self) -> str:
        pass

    def summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass

    def generate_plan(self) -> DailyPlan:
        pass

    def _sort_by_priority(self) -> list[Task]:
        pass

    def _fits_in_time(self, task: Task, used: int) -> bool:
        pass

    def _calculate_start_time(self, minutes_offset: int) -> str:
        pass
