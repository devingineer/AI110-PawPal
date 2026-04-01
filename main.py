from pawpal_system import Owner, Pet, Task, Scheduler

# ── Setup ──────────────────────────────────────────────────────────────────

owner = Owner(
    name="Jordan",
    available_minutes=90,
    preferred_start_time="08:00",
    preferences={"no_walks_after": "20:00"},
)

mochi = Pet(name="Mochi", species="dog", notes="Loves morning walks")
luna  = Pet(name="Luna",  species="cat", notes="Indoor only")

# ── Tasks added intentionally OUT OF ORDER ─────────────────────────────────
# (mixed priorities and time-of-day to demonstrate sorting)

mochi.add_task(Task(
    title="Grooming",
    duration_minutes=20,
    priority="medium",
    frequency="weekly",
))
mochi.add_task(Task(
    title="Evening walk",
    duration_minutes=20,
    priority="high",
    frequency="daily",
    preferred_time_of_day="evening",
))
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    preferred_time_of_day="morning",
))
mochi.add_task(Task(
    title="Feeding",
    duration_minutes=10,
    priority="high",
    frequency="daily",
    preferred_time_of_day="morning",
))

luna.add_task(Task(
    title="Nail trim",
    duration_minutes=10,
    priority="low",
    frequency="weekly",
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=15,
    priority="medium",
    frequency="daily",
    preferred_time_of_day="evening",
))
luna.add_task(Task(
    title="Litter box cleaning",
    duration_minutes=10,
    priority="high",
    frequency="daily",
))

# ── Register pets with owner ───────────────────────────────────────────────

owner.add_pet(mochi)
owner.add_pet(luna)

# ── Generate schedule ──────────────────────────────────────────────────────

scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# ── Print base schedule ────────────────────────────────────────────────────

print(f"\nOwner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print(f"Budget: {owner.available_minutes} min  |  Start: {owner.preferred_start_time}\n")
print("=" * 40)
print("        Today's Schedule (priority + time-of-day sorted)")
print("=" * 40)
print(plan.display())
print("\nSummary:", plan.summary())

# ── Sort scheduled entries by clock time ──────────────────────────────────

sorted_by_time = scheduler.sort_by_time(plan.scheduled_tasks)

print("\n" + "=" * 40)
print("        Re-sorted by Start Time (HH:MM)")
print("=" * 40)
for entry in sorted_by_time:
    print(f"  {entry['start_time']}  [{entry['pet']}]  {entry['task']}  ({entry['duration_minutes']}min, {entry['priority']})")

# ── Filtering demos ────────────────────────────────────────────────────────

# Mark a couple of tasks complete so filtering by status is interesting
scheduler.complete_task("Mochi", "Morning walk")
scheduler.complete_task("Luna", "Litter box cleaning")

print("\n" + "=" * 40)
print("        Filter: all pending tasks (all pets)")
print("=" * 40)
for pet, task in scheduler.filter_tasks(status="pending"):
    print(f"  [{pet.name}]  {task}")

print("\n" + "=" * 40)
print("        Filter: Mochi's tasks only (any status)")
print("=" * 40)
for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
    print(f"  [{pet.name}]  {task}")

print("\n" + "=" * 40)
print("        Filter: completed tasks (all pets)")
print("=" * 40)
for pet, task in scheduler.filter_tasks(status="completed"):
    print(f"  [{pet.name}]  {task}")

print("\n" + "=" * 40)
print("        Filter: Luna's pending tasks only")
print("=" * 40)
for pet, task in scheduler.filter_tasks(pet_name="Luna", status="pending"):
    print(f"  [{pet.name}]  {task}")

# ── Conflict detection demo ────────────────────────────────────────────────
# Manually inject two tasks that overlap in time to verify the detector works.
# Mochi's "Bath time" starts at 08:10 (10 min in) and runs 30 min → ends 08:40.
# Luna's "Vet check"  starts at 08:20 (20 min in) and runs 20 min → ends 08:40.
# Both overlap the window 08:20–08:40.

conflicting_tasks = [
    {
        "start_time": "08:10",
        "pet": "Mochi",
        "task": "Bath time",
        "duration_minutes": 30,
        "priority": "medium",
        "frequency": "weekly",
    },
    {
        "start_time": "08:20",
        "pet": "Luna",
        "task": "Vet check",
        "duration_minutes": 20,
        "priority": "high",
        "frequency": "as_needed",
    },
]

print("\n" + "=" * 40)
print("        Conflict Detection Demo")
print("=" * 40)
print("Injected tasks:")
for t in conflicting_tasks:
    end_min = int(t["start_time"][:2]) * 60 + int(t["start_time"][3:]) + t["duration_minutes"]
    end_str = f"{end_min // 60:02d}:{end_min % 60:02d}"
    print(f"  [{t['pet']}] '{t['task']}'  {t['start_time']} → {end_str}  ({t['duration_minutes']}min)")

warnings = scheduler.detect_conflicts(conflicting_tasks)
if warnings:
    for w in warnings:
        print(f"\n  *** WARNING: {w}")
