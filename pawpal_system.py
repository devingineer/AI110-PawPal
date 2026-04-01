from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"daily", "weekly", "as_needed"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_TO_MINUTES = {"morning": 480, "afternoon": 720, "evening": 1080, None: 9999}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                        # "low", "medium", "high"
    frequency: str = "daily"             # "daily", "weekly", "as_needed"
    preferred_time_of_day: Optional[str] = None  # "morning", "afternoon", "evening"
    completed: bool = False
    last_completed_date: Optional[date] = None
    next_due: Optional[date] = None

    def __post_init__(self):
        """Validate that priority and frequency are one of the allowed values."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'")

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def mark_complete(self, on: Optional[date] = None) -> None:
        """Mark this task as completed and record the completion date."""
        self.completed = True
        self.last_completed_date = on or date.today()

    def reset(self) -> None:
        """Reset this task to incomplete (e.g. for a new day)."""
        self.completed = False

    def __repr__(self) -> str:
        status = "done" if self.completed else "pending"
        return f"Task('{self.title}', {self.duration_minutes}min, {self.priority}, {status})"


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    needs: list[str] = field(default_factory=list)
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove all tasks matching the given title from this pet's list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return tasks that have been marked complete."""
        return [t for t in self.tasks if t.completed]

    def __repr__(self) -> str:
        return f"Pet('{self.name}', {self.species}, {len(self.tasks)} tasks)"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

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
        """Add a pet to this owner's roster."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove all pets matching the given name from this owner's roster."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the Pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return only incomplete tasks across all pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]

    def __repr__(self) -> str:
        return f"Owner('{self.name}', {len(self.pets)} pets, {self.available_minutes}min available)"


# ---------------------------------------------------------------------------
# DailyPlan  (output container produced by Scheduler)
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    scheduled_tasks: list[dict] = field(default_factory=list)
    skipped_tasks: list[dict] = field(default_factory=list)
    total_minutes_used: int = 0
    explanations: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def display(self) -> str:
        """Return a formatted string of the full daily plan including skipped tasks and conflicts."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = ["=== Daily Plan ==="]
        for entry in self.scheduled_tasks:
            lines.append(
                f"  {entry['start_time']}  [{entry['pet']}]  {entry['task']}  "
                f"({entry['duration_minutes']}min, {entry['priority']})"
            )
        lines.append(f"\nTotal time: {self.total_minutes_used} min")
        if self.skipped_tasks:
            lines.append("\n--- Skipped ---")
            for s in self.skipped_tasks:
                lines.append(f"  {s['task']} ({s['pet']}): {s['reason']}")
        if self.conflicts:
            lines.append("\n*** CONFLICTS DETECTED ***")
            for warning in self.conflicts:
                lines.append(f"  WARNING: {warning}")
        return "\n".join(lines)

    def summary(self) -> str:
        """Return a one-line summary of scheduled vs. skipped tasks and total time."""
        n_scheduled = len(self.scheduled_tasks)
        n_skipped = len(self.skipped_tasks)
        return (
            f"{n_scheduled} task(s) scheduled, "
            f"{n_skipped} skipped, "
            f"{self.total_minutes_used} min total."
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Sort all pending tasks by priority and schedule as many as time allows."""
        plan = DailyPlan()
        minutes_used = 0
        sorted_pairs = self._sort_by_priority()

        for pet, task in sorted_pairs:
            if self._fits_in_time(task, minutes_used):
                start_time = self._calculate_start_time(minutes_used)
                plan.scheduled_tasks.append({
                    "start_time": start_time,
                    "pet": pet.name,
                    "task": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                })
                plan.explanations.append(
                    f"'{task.title}' for {pet.name} scheduled at {start_time} "
                    f"(priority: {task.priority}, {task.duration_minutes} min)."
                )
                minutes_used += task.duration_minutes
            else:
                plan.skipped_tasks.append({
                    "pet": pet.name,
                    "task": task.title,
                    "reason": (
                        f"Not enough time remaining "
                        f"({task.duration_minutes} min needed, "
                        f"{self.owner.available_minutes - minutes_used} min left)."
                    ),
                })

        plan.total_minutes_used = minutes_used
        plan.conflicts = self.detect_conflicts(plan.scheduled_tasks)
        return plan

    def complete_task(self, pet_name: str, task_title: str) -> bool:
        """Mark a task complete and append a fresh pending copy for daily/weekly recurrences."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.title == task_title and not task.completed:
                today = date.today()
                task.mark_complete(on=today)

                if task.frequency == "daily":
                    task.next_due = today + timedelta(days=1)
                    pet.add_task(Task(
                        title=task.title,
                        duration_minutes=task.duration_minutes,
                        priority=task.priority,
                        frequency=task.frequency,
                        preferred_time_of_day=task.preferred_time_of_day,
                        next_due=task.next_due,
                    ))
                elif task.frequency == "weekly":
                    task.next_due = today + timedelta(weeks=1)
                    pet.add_task(Task(
                        title=task.title,
                        duration_minutes=task.duration_minutes,
                        priority=task.priority,
                        frequency=task.frequency,
                        preferred_time_of_day=task.preferred_time_of_day,
                        next_due=task.next_due,
                    ))

                return True
        return False

    def reset_all_tasks(self) -> None:
        """Reset completion status on every task (e.g. start of new day)."""
        for _, task in self.owner.get_all_tasks():
            task.reset()

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks (complete or not) for the named pet."""
        pet = self.owner.get_pet(pet_name)
        return pet.tasks if pet else []

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs optionally narrowed by pet name and/or 'pending'/'completed' status."""
        pairs = self.owner.get_all_tasks()

        if pet_name is not None:
            pairs = [(pet, task) for pet, task in pairs if pet.name == pet_name]

        if status == "pending":
            pairs = [(pet, task) for pet, task in pairs if not task.completed]
        elif status == "completed":
            pairs = [(pet, task) for pet, task in pairs if task.completed]

        return pairs

    def detect_conflicts(self, scheduled_tasks: list[dict]) -> list[str]:
        """Return warning strings for every pair of scheduled tasks whose time windows overlap."""
        def to_minutes(hhmm: str) -> int:
            return int(hhmm[:2]) * 60 + int(hhmm[3:])

        warnings = []
        tasks = list(scheduled_tasks)  # copy so we don't mutate the original

        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                a_start = to_minutes(a["start_time"])
                a_end   = a_start + a["duration_minutes"]
                b_start = to_minutes(b["start_time"])
                b_end   = b_start + b["duration_minutes"]

                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"[{a['pet']}] '{a['task']}' ({a['start_time']}, {a['duration_minutes']}min) "
                        f"overlaps with [{b['pet']}] '{b['task']}' ({b['start_time']}, {b['duration_minutes']}min)"
                    )

        return warnings

    def _sort_by_priority(self) -> list[tuple[Pet, Task]]:
        """Sort pending tasks by priority then time-of-day (high/morning first)."""
        pending = self.owner.get_all_pending_tasks()
        return sorted(
            pending,
            key=lambda pair: (
                PRIORITY_ORDER[pair[1].priority],
                TIME_TO_MINUTES[pair[1].preferred_time_of_day],
            ),
        )

    def sort_by_time(self, scheduled_tasks: list[dict]) -> list[dict]:
        """Return scheduled_tasks sorted by start_time (HH:MM) ascending."""
        return sorted(
            scheduled_tasks,
            key=lambda entry: int(entry["start_time"][:2]) * 60 + int(entry["start_time"][3:]),
        )

    def _fits_in_time(self, task: Task, used: int) -> bool:
        """Return True if the task fits within the owner's remaining available time."""
        return used + task.duration_minutes <= self.owner.available_minutes

    def _calculate_start_time(self, minutes_offset: int) -> str:
        """Return a clock string (HH:MM) for start_time + offset minutes."""
        h, m = map(int, self.owner.preferred_start_time.split(":"))
        total = h * 60 + m + minutes_offset
        return f"{(total // 60) % 24:02d}:{total % 60:02d}"
