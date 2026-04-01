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
    plan = st.session_state.plan
    st.success(plan.summary())

    if plan.scheduled_tasks:
        st.write("**Scheduled:**")
        st.table(plan.scheduled_tasks)

    if plan.skipped_tasks:
        st.write("**Skipped:**")
        st.table(plan.skipped_tasks)

    if plan.explanations:
        with st.expander("Reasoning"):
            for note in plan.explanations:
                st.markdown(f"- {note}")
