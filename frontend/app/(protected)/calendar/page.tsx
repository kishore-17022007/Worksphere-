"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type CalendarEvent = { id: string; title: string; event_type: string; starts_at: string; ends_at: string; visibility: string };
export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10);
    apiFetch<CalendarEvent[]>(`/calendar/events?start=${start}&end=${end}`).then(setEvents).catch(() => setError("Unable to load calendar."));
  }, []);
  return <section><h1 className="text-3xl font-bold">Calendar</h1><p className="mt-2 text-slate-600">Company events, holidays, approved leave, and deadlines.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 rounded-xl bg-white shadow-sm"><h2 className="border-b px-5 py-4 font-semibold">Upcoming events</h2>{events.length ? events.map((event) => <div key={event.id} className="border-b px-5 py-4"><p className="font-medium">{event.title}</p><p className="mt-1 text-sm text-slate-500">{new Date(event.starts_at).toLocaleString()} · {event.event_type}</p></div>) : <p className="px-5 py-8 text-sm text-slate-500">No upcoming events.</p>}</div></section>;
}
