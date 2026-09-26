"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Event = { id: string; event_type: string; entity_type: string; occurred_at: string; payload: Record<string, string> | null };
export default function TimelinePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Event[]>("/intelligence/activity-events").then(setEvents).catch(() => setError("Unable to load timeline.")); }, []);
  return <section><h1 className="text-3xl font-bold">Work timeline</h1><p className="mt-2 text-slate-600">A chronological record of your workplace activity.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 space-y-3">{events.length ? events.map((event) => <div key={event.id} className="rounded-xl bg-white p-5 shadow-sm"><div className="flex justify-between"><p className="font-medium">{event.event_type.replaceAll("_", " ")}</p><time className="text-xs text-slate-500">{new Date(event.occurred_at).toLocaleString()}</time></div><p className="mt-1 text-sm text-slate-500">{event.entity_type}</p></div>) : <div className="rounded-xl bg-white p-8 text-sm text-slate-500 shadow-sm">No activity recorded.</div>}</div></section>;
}
