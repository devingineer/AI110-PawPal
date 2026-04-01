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

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
