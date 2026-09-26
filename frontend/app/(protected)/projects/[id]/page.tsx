"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Project = { id: string; name: string; description: string | null; status: string; priority: string; start_date: string | null; target_date: string | null };
const tabs = ["Overview", "Team", "Tasks", "Meetings", "MOM", "Files", "Chat", "Timeline", "Reports"];

export default function ProjectWorkspacePage() {
  const params = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  useEffect(() => { apiFetch<Project>(`/work/projects/${params.id}`).then(setProject).catch(() => setProject(null)); }, [params.id]);
  if (!project) return <p className="text-slate-500">Loading project...</p>;
  return <section><p className="text-sm font-medium text-blue-600">Project workspace</p><h1 className="mt-2 text-3xl font-bold">{project.name}</h1><p className="mt-2 max-w-2xl text-slate-600">{project.description || "No description"}</p><div className="mt-8 flex flex-wrap gap-2">{tabs.map((tab) => <button key={tab} className={`rounded-md px-3 py-2 text-sm ${tab === "Overview" ? "bg-blue-600 text-white" : "bg-white text-slate-700 shadow-sm"}`}>{tab}</button>)}</div><div className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-xl bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Status</p><p className="mt-2 font-semibold">{project.status}</p></div><div className="rounded-xl bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Priority</p><p className="mt-2 font-semibold">{project.priority}</p></div><div className="rounded-xl bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Target date</p><p className="mt-2 font-semibold">{project.target_date || "Not set"}</p></div></div></section>;
}
