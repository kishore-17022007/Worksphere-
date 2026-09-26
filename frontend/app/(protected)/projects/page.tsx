"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Project = { id: string; name: string; description: string | null; status: string; priority: string };

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Project[]>("/work/projects").then(setProjects).catch(() => setError("Unable to load projects.")); }, []);
  return <section><div className="flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-3xl font-bold">Projects</h1><p className="mt-2 text-slate-600">Plan and deliver work with your teams.</p></div></div>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 grid gap-4 md:grid-cols-2">{projects.length ? projects.map((project) => <Link key={project.id} href={`/projects/${project.id}`} className="rounded-xl bg-white p-6 shadow-sm transition hover:shadow-md"><div className="flex items-start justify-between gap-4"><h2 className="font-semibold">{project.name}</h2><span className="rounded-full bg-blue-50 px-2 py-1 text-xs text-blue-700">{project.status}</span></div><p className="mt-2 text-sm text-slate-500">{project.description || "No description"}</p><p className="mt-5 text-xs font-medium uppercase tracking-wide text-slate-400">{project.priority} priority</p></Link>) : <div className="rounded-xl bg-white p-8 text-sm text-slate-500 shadow-sm">No projects found.</div>}</div></section>;
}
