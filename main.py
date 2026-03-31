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

# ── Tasks for Mochi ────────────────────────────────────────────────────────

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
mochi.add_task(Task(
    title="Grooming",
    duration_minutes=20,
    priority="medium",
    frequency="weekly",
))

# ── Tasks for Luna ─────────────────────────────────────────────────────────

luna.add_task(Task(
    title="Litter box cleaning",
    duration_minutes=10,
    priority="high",
    frequency="daily",
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=15,
    priority="medium",
    frequency="daily",
    preferred_time_of_day="evening",
))
luna.add_task(Task(
    title="Nail trim",
    duration_minutes=10,
    priority="low",
    frequency="weekly",
))

# ── Register pets with owner ───────────────────────────────────────────────

owner.add_pet(mochi)
owner.add_pet(luna)

# ── Generate schedule ──────────────────────────────────────────────────────

scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# ── Print results ──────────────────────────────────────────────────────────

print(f"\nOwner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print(f"Budget: {owner.available_minutes} min  |  Start: {owner.preferred_start_time}\n")
print("=" * 40)
print("        Today's Schedule")
print("=" * 40)
print(plan.display())
print()
print("Summary:", plan.summary())

if plan.explanations:
    print("\nReasoning:")
    for note in plan.explanations:
        print(f"  - {note}")
