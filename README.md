# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## Smarter Scheduling

### Sorting by time and priority

Tasks are sorted before scheduling using a two-key lambda: first by priority (`high → medium → low`), then by `preferred_time_of_day` (`morning → afternoon → evening → unset`). This ensures high-priority morning tasks always land earliest in the day. A separate `sort_by_time()` method re-sorts any list of already-scheduled entries by their `HH:MM` start time, converting each string to total minutes for an accurate integer comparison.

### Filtering by pet and status

`Scheduler.filter_tasks(pet_name, status)` returns `(Pet, Task)` pairs narrowed by any combination of pet name and completion status (`"pending"` / `"completed"` / `None` for all). Both parameters are optional and compose together, making it easy to answer questions like "what has Luna not done yet?" without touching the raw task lists.

### Recurring tasks

`Task` now tracks `last_completed_date` and `next_due` (both `Optional[date]`). When `complete_task()` is called, it records today's date on the finished task and uses `timedelta` to compute the next occurrence — `+1 day` for `"daily"` tasks, `+7 days` for `"weekly"` tasks — then appends a fresh pending copy to the pet's task list. `"as_needed"` tasks are left alone with no follow-up created.

### Conflict detection

`detect_conflicts(scheduled_tasks)` compares every pair of scheduled entries using the standard overlap condition (`A.start < B.end and B.start < A.end`), converting `HH:MM` strings to minutes for the comparison. It returns a list of human-readable warning strings and never raises an exception. Conflicts across different pets are caught the same way as same-pet conflicts. `generate_plan()` calls this automatically and stores any warnings in `DailyPlan.conflicts`, which `display()` prints as a `*** CONFLICTS DETECTED ***` block.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
