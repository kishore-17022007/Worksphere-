"""Transparent, deterministic workplace intelligence calculations."""
from datetime import date, datetime, timedelta

PRIORITY_WEIGHT = {"URGENT": 40, "HIGH": 30, "MEDIUM": 20, "LOW": 10}
DONE = {"COMPLETED", "DONE", "CANCELLED"}


def _value(obj, name, default=None):
    return getattr(obj, name, default) if not isinstance(obj, dict) else obj.get(name, default)


def rank_tasks(tasks, today=None):
    today = today or date.today()
    def score(task):
        due = _value(task, "due_at")
        due_date = due.date() if isinstance(due, datetime) else due
        urgency = 30 if due_date and due_date < today else (20 if due_date == today else 0)
        return -(PRIORITY_WEIGHT.get(str(_value(task, "priority", "MEDIUM")).upper(), 20) + urgency)
    return sorted((t for t in tasks if str(_value(t, "status", "")).upper() not in DONE), key=score)


def calculate_daily_plan(tasks, meetings=(), plan_date=None, available_minutes=480, on_leave=False):
    """Return plain dictionaries so rules are easy to test and audit."""
    plan_date = plan_date or date.today()
    if on_leave:
        return []
    items = []
    used = 0
    for meeting in sorted(meetings, key=lambda m: _value(m, "starts_at")):
        start, end = _value(meeting, "starts_at"), _value(meeting, "ends_at")
        minutes = max(1, int((end - start).total_seconds() / 60))
        items.append({"item_type": "meeting", "meeting_id": _value(meeting, "id"), "title": _value(meeting, "title"), "duration_minutes": minutes,
                      "start_minute": int(start.hour * 60 + start.minute), "rationale": "scheduled meeting"})
        used += minutes
    for task in rank_tasks(tasks, plan_date):
        effort = int(_value(task, "estimated_minutes", 60) or 60)
        duration = min(effort, max(0, available_minutes - used))
        if duration <= 0:
            break
        due = _value(task, "due_at")
        reason = f"{str(_value(task, 'priority', 'MEDIUM')).upper()} priority"
        if due and (due.date() if isinstance(due, datetime) else due) <= plan_date:
            reason += "; deadline due"
        items.append({"item_type": "task", "task_id": _value(task, "id"), "title": _value(task, "title"),
                      "duration_minutes": duration, "start_minute": None, "rationale": reason})
        used += duration
    return items


def aggregate_workload(tasks, projects=(), today=None):
    today = today or date.today()
    result = {"active": 0, "overdue": 0, "upcoming": 0, "effort_minutes": 0, "project_workload": {}}
    for task in tasks:
        if str(_value(task, "status", "")).upper() in DONE:
            continue
        result["active"] += 1
        due = _value(task, "due_at")
        due_date = due.date() if isinstance(due, datetime) else due
        if due_date and due_date < today: result["overdue"] += 1
        elif due_date: result["upcoming"] += 1
        effort = int(_value(task, "estimated_minutes", 60) or 60)
        result["effort_minutes"] += effort
        project = str(_value(task, "project_id", "unassigned"))
        result["project_workload"][project] = result["project_workload"].get(project, 0) + effort
    return result


def weekly_summary(attendance, tasks, meetings, projects, leave, start=None):
    start = start or (date.today() - timedelta(days=date.today().weekday()))
    return {"start_date": start, "attendance_days": len(attendance), "completed_tasks": sum(str(_value(t, "status", "")).upper() in DONE for t in tasks),
            "pending_tasks": sum(str(_value(t, "status", "")).upper() not in DONE for t in tasks),
            "meetings_attended": len(meetings), "active_projects": sum(str(_value(p, "status", "")).upper() == "ACTIVE" for p in projects),
            "deadlines": sum(1 for t in tasks if _value(t, "due_at")), "leave_days": len(leave)}
