import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state bootstrap ────────────────────────────────────────────────
# Objects are created once on the first run and survive every rerun after.

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

# ── Owner setup ────────────────────────────────────────────────────────────

st.subheader("Owner Info")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name or "Jordan")
with col2:
    available_minutes = st.number_input(
        "Available minutes today", min_value=10, max_value=480,
        value=st.session_state.owner.available_minutes,
    )
with col3:
    preferred_start = st.text_input(
        "Start time (HH:MM)", value=st.session_state.owner.preferred_start_time
    )

# Write widget values back into the persisted owner object
st.session_state.owner.name = owner_name
st.session_state.owner.available_minutes = available_minutes
st.session_state.owner.preferred_start_time = preferred_start

st.divider()

# ── Add a pet ──────────────────────────────────────────────────────────────

st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

notes = st.text_input("Notes (optional)", value="")

if st.button("Add pet"):
    existing_names = [p.name for p in st.session_state.owner.pets]
    if pet_name.strip() == "":
        st.warning("Pet name cannot be empty.")
    elif pet_name in existing_names:
        st.warning(f"'{pet_name}' is already on the roster.")
    else:
        new_pet = Pet(name=pet_name, species=species, notes=notes)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"Added {pet_name} the {species}!")

if st.session_state.owner.pets:
    st.write("**Current pets:**", ", ".join(p.name for p in st.session_state.owner.pets))

st.divider()

# ── Add a task ─────────────────────────────────────────────────────────────

st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    pet_options = [p.name for p in st.session_state.owner.pets]
    col1, col2 = st.columns(2)
    with col1:
        selected_pet = st.selectbox("Assign to pet", pet_options)
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col2:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
    with col4:
        time_of_day = st.selectbox(
            "Preferred time", ["(none)", "morning", "afternoon", "evening"]
        )

    if st.button("Add task"):
        pet = st.session_state.owner.get_pet(selected_pet)
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            preferred_time_of_day=None if time_of_day == "(none)" else time_of_day,
        )
        pet.add_task(new_task)
        st.success(f"Added '{task_title}' to {selected_pet}.")

    # Show all tasks grouped by pet
    all_pairs = st.session_state.owner.get_all_tasks()
    if all_pairs:
        st.write("**All tasks:**")
        rows = [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Done": task.completed,
            }
            for pet, task in all_pairs
        ]
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Generate schedule ──────────────────────────────────────────────────────

st.subheader("Generate Today's Schedule")

col1, col2 = st.columns(2)
with col1:
    if st.button("Generate schedule"):
        plan = st.session_state.scheduler.generate_plan()
        st.session_state.plan = plan

with col2:
    if st.button("Reset all tasks"):
        st.session_state.scheduler.reset_all_tasks()
        st.session_state.pop("plan", None)
        st.success("All tasks reset for a new day.")

if "plan" in st.session_state:
    plan     = st.session_state.plan
    scheduler = st.session_state.scheduler

    # ── Summary banner ─────────────────────────────────────────────────────
    if plan.scheduled_tasks:
        st.success(f"Schedule ready — {plan.summary()}")
    else:
        st.info("No tasks could be scheduled. Add tasks or increase your time budget.")

    # ── Conflict warnings ──────────────────────────────────────────────────
    if plan.conflicts:
        for warning in plan.conflicts:
            st.warning(f"Time conflict: {warning}")

    # ── Scheduled tasks (sorted by start time) ─────────────────────────────
    if plan.scheduled_tasks:
        st.subheader("Scheduled tasks")
        sorted_entries = scheduler.sort_by_time(plan.scheduled_tasks)
        st.table([
            {
                "Start":    e["start_time"],
                "Pet":      e["pet"],
                "Task":     e["task"],
                "Duration": f"{e['duration_minutes']} min",
                "Priority": e["priority"].capitalize(),
                "Frequency": e["frequency"],
            }
            for e in sorted_entries
        ])

    # ── Filter view ────────────────────────────────────────────────────────
    if st.session_state.owner.pets:
        st.subheader("Filter tasks")
        col1, col2 = st.columns(2)
        with col1:
            pet_options  = ["All pets"] + [p.name for p in st.session_state.owner.pets]
            filter_pet   = st.selectbox("Pet", pet_options, key="filter_pet")
        with col2:
            filter_status = st.selectbox("Status", ["All", "Pending", "Completed"], key="filter_status")

        pet_arg    = None if filter_pet == "All pets" else filter_pet
        status_arg = None if filter_status == "All" else filter_status.lower()

        filtered = scheduler.filter_tasks(pet_name=pet_arg, status=status_arg)

        if filtered:
            st.table([
                {
                    "Pet":      pet.name,
                    "Task":     task.title,
                    "Priority": task.priority.capitalize(),
                    "Frequency": task.frequency,
                    "Status":   "Done" if task.completed else "Pending",
                    "Next due": str(task.next_due) if task.next_due else "—",
                }
                for pet, task in filtered
            ])
        else:
            st.info("No tasks match the selected filters.")

    # ── Mark a task complete ───────────────────────────────────────────────
    st.subheader("Mark a task complete")
    pending_pairs = st.session_state.scheduler.filter_tasks(status="pending")
    if pending_pairs:
        col1, col2 = st.columns(2)
        with col1:
            complete_pet = st.selectbox(
                "Pet",
                options=list({pet.name for pet, _ in pending_pairs}),
                key="complete_pet",
            )
        with col2:
            pet_pending = [
                task.title
                for pet, task in pending_pairs
                if pet.name == complete_pet
            ]
            complete_task_title = st.selectbox("Task", options=pet_pending, key="complete_task")

        if st.button("Mark complete"):
            marked = st.session_state.scheduler.complete_task(complete_pet, complete_task_title)
            if marked:
                # Find the task to read next_due
                completed_task = next(
                    (t for p in st.session_state.owner.pets
                     if p.name == complete_pet
                     for t in p.tasks
                     if t.title == complete_task_title and t.completed),
                    None,
                )
                if completed_task and completed_task.next_due:
                    st.success(
                        f"'{complete_task_title}' marked done! "
                        f"Next {completed_task.frequency} occurrence due: **{completed_task.next_due}**"
                    )
                else:
                    st.success(f"'{complete_task_title}' marked done!")
                # Regenerate the plan so the schedule reflects the updated state
                st.session_state.plan = st.session_state.scheduler.generate_plan()
                st.rerun()
    else:
        st.info("All tasks are already complete. Use Reset to start a new day.")

    # ── Recurring task due dates ───────────────────────────────────────────
    recurring_with_due = [
        (pet, task)
        for pet, task in st.session_state.owner.get_all_tasks()
        if task.next_due is not None
    ]
    if recurring_with_due:
        with st.expander("Upcoming recurring tasks"):
            st.table([
                {
                    "Pet":       pet.name,
                    "Task":      task.title,
                    "Frequency": task.frequency,
                    "Next due":  str(task.next_due),
                    "Status":    "Done" if task.completed else "Pending",
                }
                for pet, task in sorted(recurring_with_due, key=lambda pair: pair[1].next_due)
            ])

    # ── Skipped tasks ──────────────────────────────────────────────────────
    if plan.skipped_tasks:
        with st.expander(f"Skipped tasks ({len(plan.skipped_tasks)})"):
            for s in plan.skipped_tasks:
                st.warning(f"[{s['pet']}] **{s['task']}** — {s['reason']}")

    # ── Reasoning ─────────────────────────────────────────────────────────
    if plan.explanations:
        with st.expander("Scheduling reasoning"):
            for note in plan.explanations:
                st.markdown(f"- {note}")
