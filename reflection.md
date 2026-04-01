# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Core Classes:
- Owner - stores the owner's name, average time per day, and preferences
- Pet - stores pet name, species, any pet-specific needs or constraints
- Task - represents a single care task with attributes like title, duration_minutes, priority, and time_of_day preference
- Scheduler - central logic class; takes an Owner, a Pet, and a list of Task objects and produces a DailyPlan
- DailyPlan - holds the ordered list of scheduled tasks with start times and a human-readable explanation of why each task was included/ordered as it was

Relationships: Owner and Pet are associated (one owner, one-or-more pets). Scheduler depends on both and aggreagtes Task objects to compose a DailyPlan

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

- Owner.preferences - Preferences are taken account of into the scheduler based on the owner. Owner only had a preferred_start_time with no way to express other preferences.
- Scheduler has no _calculate_start_time() helper functoin. DailyPlan stores dictionary with start times, but there's no method for the logic that computes what time each task begins.
- DailyPlan is missing skipped_tasks — the README says the plan should "explain why it chose that plan," implying tasks that didn't make the cut should be reported with a reason (e.g. "not enough time remaining").

--- 

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler enforces three layered constraints in order of importance:

1. **Time budget** — `owner.available_minutes` is a hard cap. A task is only scheduled if `used + task.duration_minutes <= available_minutes`; otherwise it is skipped with a reason. This is the most critical constraint because no amount of prioritization matters if the owner simply doesn't have the time.

2. **Priority** — Tasks are sorted `high → medium → low` using `PRIORITY_ORDER`. Within the same priority level, `preferred_time_of_day` acts as a tiebreaker (`morning → afternoon → evening → unset`) via `TIME_TO_MINUTES`. Priority was chosen as the primary sort key because a missed high-priority task (e.g., feeding, medication) has real consequences for pet health, whereas a low-priority task (e.g., nail trim) can safely slip to another day.

3. **Owner preferences** — `owner.preferences` (e.g., `no_walks_after`) is stored and available for conflict detection, but treated as a soft constraint — it generates a warning rather than a hard block. This reflects real life: preferences are guidelines, not rules.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler uses a **greedy first-fit algorithm**: it works through the priority-sorted task list and slots each task as soon as it fits in the remaining time budget, never reconsidering earlier decisions. This means it can produce a suboptimal packing — for example, scheduling one 40-minute medium task might prevent two 25-minute high-priority tasks from both fitting, even though dropping the medium task would have allowed both.

This tradeoff is reasonable for a pet care context because:
- The task list is small (typically under 20 items), so the worst-case gap between greedy and optimal is minimal in practice.
- Pet owners need a schedule they can understand and trust at a glance. A greedy approach produces a predictable, explainable result — tasks appear in the order a human would naturally do them — whereas an optimal bin-packing solution might reorder tasks in ways that feel arbitrary.
- High-priority tasks are always considered first, so the greedy approach rarely sacrifices anything important. The tasks most likely to be bumped are low-priority ones, which is exactly the desired behavior.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI was used throughout the project in three main ways. First, for brainstorming — asking which edge cases mattered most for a scheduler (e.g., zero budget, exact budget fit, adjacent-but-not-overlapping tasks) surfaced tests I wouldn't have written on my own. Second, for implementation guidance — asking targeted questions like "how do I sort HH:MM strings with a lambda?" produced working, explainable code rather than just a pattern to copy. Third, for incremental feature additions — each new method (`filter_tasks`, `detect_conflicts`, recurring task logic) was added in isolation by describing exactly what it needed to do and where it should live in the existing class structure. The most effective prompts were specific about the class and method involved and named the constraint the feature had to satisfy.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When conflict detection was first suggested, the initial framing was to run it inside `generate_plan()` only. I pushed back because `generate_plan()` always schedules tasks sequentially — so it structurally can never produce overlaps on its own. Accepting the suggestion as-is would have meant the detection code could never actually fire in normal use. The fix was to also expose `detect_conflicts()` as a standalone public method that accepts any list of task dicts, so it can be called on manually constructed or externally supplied schedules. I verified this by injecting two overlapping entries in `main.py` and confirming the warning printed.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

16 tests cover five categories: core task/pet operations, priority and time-of-day sorting, recurrence logic (daily, weekly, as_needed, and the double-complete guard), conflict detection (exact overlap, partial overlap, adjacent, and sequential), and edge cases (empty pet, zero budget, exact budget fit). The recurrence and conflict tests were the most important — recurrence is stateful and easy to break with a second call, and the adjacent-task test pins down the boundary of the overlap condition (`<` vs `<=`), which is a silent bug if wrong.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

4 out of 5. The scheduling core is well-covered and all 16 tests pass consistently. The gap is in `filter_tasks` (no dedicated tests), the `no_walks_after` preference (stored but not enforced during scheduling), and the Streamlit UI layer (no automated tests at all). If I had more time I would test filtering with combined pet + status arguments, verify that the `no_walks_after` cutoff correctly skips a walk that would start too late, and add a test confirming that `DailyPlan.conflicts` is populated when `generate_plan()` is called on a schedule where two tasks genuinely overlap.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The recurrence system came together cleanly. Adding two fields (`last_completed_date`, `next_due`) to `Task` and updating a single method (`complete_task`) was enough to make daily and weekly tasks self-propagating — no changes were needed anywhere else in the system. That felt like a sign the class boundaries were drawn in the right place: `Task` owns its own state, `Scheduler` owns the logic that acts on it, and `Pet` just holds the list.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would enforce `owner.preferences` during scheduling rather than only at conflict-detection time. Right now `no_walks_after` is stored but `generate_plan()` ignores it — the constraint exists in the data model but has no effect on the output. I would also reconsider storing tasks as plain dicts inside `DailyPlan.scheduled_tasks`. Using actual `Task` objects (or a lightweight `ScheduledEntry` dataclass) would make the scheduled list type-safe and remove the need to re-look up task attributes by string key throughout the display and conflict-detection code.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The UML diagram was most useful as a forcing function at the start, not as a reference during implementation. The moment I started writing actual code, the diagram fell behind — `Pet` needed task methods, `Scheduler` needed to lose direct task ownership, `DailyPlan` needed new fields. The real lesson is that the diagram should be updated at the end of each feature, not just at the beginning and end of the project. Treating it as a living document would have made the final update much smaller and less surprising.

---

Working in separate chat sessions for each phase — design, sorting, filtering, recurrence, conflict detection, testing, UI — made it easy to stay focused because each session had a single, clear goal and a natural stopping point, which prevented scope creep and made it obvious when a phase was actually done. The most important thing I learned about being the "lead architect" alongside a powerful AI is that the AI can execute faster than you can think through consequences — so the job isn't writing code, it's knowing what to ask for, catching when a suggestion solves the wrong problem, and making the calls the AI can't make for you, like which constraints are hard rules versus soft warnings, or when a cleaner abstraction isn't worth the complexity.
