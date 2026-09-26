"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Task = { id: string; title: string; status: string; priority: string; project_id: string | null };
const columns = ["BACKLOG", "TODO", "IN_PROGRESS", "IN_REVIEW", "COMPLETED"];

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Task[]>("/work/tasks").then(setTasks).catch(() => setError("Unable to load tasks.")); }, []);
  async function move(task: Task, status: string) {
    try { const updated = await apiFetch<Task>(`/work/tasks/${task.id}/status`, { method: "POST", body: JSON.stringify({ status }) }); setTasks((current) => current.map((item) => item.id === task.id ? updated : item)); } catch { setError("Unable to update task status."); }
  }
  return <section><h1 className="text-3xl font-bold">Tasks</h1><p className="mt-2 text-slate-600">Move work through the delivery workflow.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 grid gap-4 overflow-x-auto md:grid-cols-5">{columns.map((column) => <div key={column} className="min-h-52 rounded-xl bg-slate-100 p-3"><h2 className="text-xs font-bold tracking-wide text-slate-500">{column.replace("_", " ")}</h2><div className="mt-3 space-y-3">{tasks.filter((task) => task.status === column).map((task) => <article key={task.id} draggable onDragEnd={() => move(task, column)} className="cursor-grab rounded-lg bg-white p-4 shadow-sm"><h3 className="text-sm font-medium">{task.title}</h3><p className="mt-2 text-xs text-slate-500">{task.priority}</p><select value={task.status} onChange={(event) => move(task, event.target.value)} className="mt-3 w-full rounded border px-2 py-1 text-xs"><option value={task.status}>{task.status}</option>{columns.filter((value) => value !== task.status).map((value) => <option key={value} value={value}>{value}</option>)}</select></article>)}</div></div>)}</div></section>;
}
