import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_scheduler(available_minutes=120, start_time="08:00"):
    owner = Owner(name="Jordan", available_minutes=available_minutes,
                  preferred_start_time=start_time)
    return owner, Scheduler(owner)


# ---------------------------------------------------------------------------
# Original tests
# ---------------------------------------------------------------------------

def test_task_completion():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_task_addition():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time should reorder entries from earliest to latest start time."""
    _, scheduler = make_scheduler()
    entries = [
        {"start_time": "10:30", "pet": "Mochi", "task": "Grooming",      "duration_minutes": 20, "priority": "medium"},
        {"start_time": "08:00", "pet": "Mochi", "task": "Morning walk",   "duration_minutes": 30, "priority": "high"},
        {"start_time": "09:15", "pet": "Luna",  "task": "Litter box",     "duration_minutes": 10, "priority": "high"},
    ]
    result = scheduler.sort_by_time(entries)
    start_times = [e["start_time"] for e in result]
    assert start_times == ["08:00", "09:15", "10:30"]


def test_generate_plan_schedules_high_priority_first():
    """High-priority tasks must appear before lower-priority ones in the plan."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Nail trim",     duration_minutes=10, priority="low"))
    pet.add_task(Task(title="Morning walk",  duration_minutes=30, priority="high"))
    pet.add_task(Task(title="Grooming",      duration_minutes=20, priority="medium"))
    owner.add_pet(pet)

    plan = scheduler.generate_plan()
    priorities = [e["priority"] for e in plan.scheduled_tasks]
    assert priorities[0] == "high"
    assert priorities[-1] == "low"


def test_sort_by_priority_breaks_ties_by_time_of_day():
    """Among tasks with equal priority, morning tasks must sort before evening tasks."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Evening walk", duration_minutes=20, priority="high",
                      preferred_time_of_day="evening"))
    pet.add_task(Task(title="Morning walk", duration_minutes=30, priority="high",
                      preferred_time_of_day="morning"))
    owner.add_pet(pet)

    plan = scheduler.generate_plan()
    assert plan.scheduled_tasks[0]["task"] == "Morning walk"
    assert plan.scheduled_tasks[1]["task"] == "Evening walk"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_copy():
    """Completing a daily task should append a new pending task due tomorrow."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high", frequency="daily"))
    owner.add_pet(pet)

    scheduler.complete_task("Mochi", "Feeding")

    tasks = pet.tasks
    assert len(tasks) == 2                                          # original + new copy
    original = tasks[0]
    new_copy  = tasks[1]
    assert original.completed is True
    assert original.next_due == date.today() + timedelta(days=1)
    assert new_copy.completed is False
    assert new_copy.next_due  == date.today() + timedelta(days=1)


def test_complete_weekly_task_creates_next_week_copy():
    """Completing a weekly task should append a new pending task due in 7 days."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Grooming", duration_minutes=20, priority="medium", frequency="weekly"))
    owner.add_pet(pet)

    scheduler.complete_task("Mochi", "Grooming")

    tasks = pet.tasks
    assert len(tasks) == 2
    assert tasks[0].next_due == date.today() + timedelta(weeks=1)
    assert tasks[1].completed is False


def test_complete_as_needed_task_does_not_spawn_copy():
    """Completing an as_needed task must NOT create a follow-up task."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task(title="Vet visit", duration_minutes=60, priority="high", frequency="as_needed"))
    owner.add_pet(pet)

    scheduler.complete_task("Luna", "Vet visit")

    assert len(pet.tasks) == 1                                      # no new copy
    assert pet.tasks[0].completed is True


def test_complete_task_twice_does_not_duplicate_recurrence():
    """Calling complete_task a second time on an already-done task must be a no-op."""
    owner, scheduler = make_scheduler()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high", frequency="daily"))
    owner.add_pet(pet)

    scheduler.complete_task("Mochi", "Feeding")   # first call — spawns copy
    scheduler.complete_task("Mochi", "Feeding")   # second call — should complete the new copy only

    completed_count = sum(1 for t in pet.tasks if t.completed)
    assert completed_count == 2                                     # both the original and its copy
    assert len(pet.tasks) == 3                                      # original + first copy + second copy


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_exact_same_start_time():
    """Two tasks starting at the same time must be detected as a conflict."""
    _, scheduler = make_scheduler()
    entries = [
        {"start_time": "08:00", "pet": "Mochi", "task": "Bath time",    "duration_minutes": 30, "priority": "medium"},
        {"start_time": "08:00", "pet": "Luna",  "task": "Vet check",    "duration_minutes": 20, "priority": "high"},
    ]
    warnings = scheduler.detect_conflicts(entries)
    assert len(warnings) == 1
    assert "Bath time" in warnings[0]
    assert "Vet check" in warnings[0]


def test_detect_conflicts_flags_partial_overlap():
    """A task that starts mid-way through another task must be flagged."""
    _, scheduler = make_scheduler()
    entries = [
        {"start_time": "08:10", "pet": "Mochi", "task": "Bath time",  "duration_minutes": 30, "priority": "medium"},
        {"start_time": "08:20", "pet": "Luna",  "task": "Vet check",  "duration_minutes": 20, "priority": "high"},
    ]
    warnings = scheduler.detect_conflicts(entries)
    assert len(warnings) == 1


def test_detect_conflicts_no_warning_for_adjacent_tasks():
    """Tasks that end exactly when the next begins must NOT be flagged as a conflict."""
    _, scheduler = make_scheduler()
    entries = [
        {"start_time": "08:00", "pet": "Mochi", "task": "Morning walk", "duration_minutes": 30, "priority": "high"},
        {"start_time": "08:30", "pet": "Mochi", "task": "Feeding",      "duration_minutes": 10, "priority": "high"},
    ]
    warnings = scheduler.detect_conflicts(entries)
    assert warnings == []


def test_detect_conflicts_no_warning_for_sequential_tasks():
    """A clean sequential schedule with gaps must produce zero conflict warnings."""
    _, scheduler = make_scheduler()
    entries = [
        {"start_time": "08:00", "pet": "Mochi", "task": "Morning walk",   "duration_minutes": 30, "priority": "high"},
        {"start_time": "09:00", "pet": "Luna",  "task": "Litter box",     "duration_minutes": 10, "priority": "high"},
        {"start_time": "10:00", "pet": "Mochi", "task": "Grooming",       "duration_minutes": 20, "priority": "medium"},
    ]
    assert scheduler.detect_conflicts(entries) == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_produces_empty_plan():
    """An owner whose pet has zero tasks should get an empty plan, not an error."""
    owner, scheduler = make_scheduler()
    owner.add_pet(Pet(name="Mochi", species="dog"))

    plan = scheduler.generate_plan()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks   == []
    assert plan.total_minutes_used == 0


def test_zero_available_minutes_skips_all_tasks():
    """With no time budget every task must land in skipped_tasks."""
    owner, scheduler = make_scheduler(available_minutes=0)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    plan = scheduler.generate_plan()
    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 1


def test_task_that_exactly_fills_budget_is_scheduled():
    """A single task whose duration equals available_minutes must be scheduled, not skipped."""
    owner, scheduler = make_scheduler(available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Morning walk", duration_minutes=30, priority="high"))
    owner.add_pet(pet)

    plan = scheduler.generate_plan()
    assert len(plan.scheduled_tasks) == 1
    assert plan.skipped_tasks        == []
