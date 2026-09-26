"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Summary = { attendance: { present: number; leave: number; total: number }; tasks: { completed: number; pending: number }; meetings_attended: number; active_projects: number; upcoming_deadlines: number; leave_days: number };
export default function ReportsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Summary>("/intelligence/weekly-summary").then(setSummary).catch(() => setError("Unable to load reports.")); }, []);
  const cards = summary ? [["Attendance", `${summary.attendance.present}/${summary.attendance.total}`], ["Tasks completed", summary.tasks.completed], ["Tasks pending", summary.tasks.pending], ["Meetings", summary.meetings_attended], ["Active projects", summary.active_projects], ["Upcoming deadlines", summary.upcoming_deadlines], ["Leave days", summary.leave_days]] : [];
  return <section><h1 className="text-3xl font-bold">Reports</h1><p className="mt-2 text-slate-600">Structured weekly statistics for planning and coordination.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{cards.map(([label, value]) => <div key={label} className="rounded-xl bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p></div>)}</div>{!summary && !error && <p className="mt-6 text-sm text-slate-500">Loading report...</p>}</section>;
}
