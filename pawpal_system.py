from dataclasses import dataclass, field
from typing import Optional


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

    def is_high_priority(self) -> bool:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferred_start_time: str = "08:00"):
        self.name = name
        self.available_minutes = available_minutes
        self.preferred_start_time = preferred_start_time
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[dict] = field(default_factory=list)
    total_minutes_used: int = 0
    explanations: list[str] = field(default_factory=list)

    def display(self) -> str:
        pass

    def summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
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
