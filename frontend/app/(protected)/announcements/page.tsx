"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Announcement = { id: string; title: string; body: string; published_at: string | null; requires_acknowledgement: boolean; read?: boolean };
export default function AnnouncementsPage() {
  const [items, setItems] = useState<Announcement[]>([]);
  useEffect(() => { apiFetch<Announcement[]>("/announcements").then(setItems).catch(() => setItems([])); }, []);
  async function acknowledge(id: string) { await apiFetch(`/announcements/${id}/ack`, { method: "POST" }); setItems((current) => current.map((item) => item.id === id ? { ...item, read: true } : item)); }
  return <section><h1 className="text-3xl font-bold">Announcements</h1><p className="mt-2 text-slate-600">Important updates from your company.</p><div className="mt-6 space-y-4">{items.length ? items.map((item) => <article key={item.id} className="rounded-xl bg-white p-6 shadow-sm"><div className="flex justify-between gap-4"><h2 className="font-semibold">{item.title}</h2>{item.read && <span className="text-xs text-green-600">Read</span>}</div><p className="mt-3 text-sm text-slate-600">{item.body}</p>{item.requires_acknowledgement && !item.read && <button onClick={() => acknowledge(item.id)} className="mt-4 rounded-md bg-blue-600 px-3 py-2 text-sm text-white">Acknowledge</button>}</article>) : <div className="rounded-xl bg-white p-8 text-sm text-slate-500 shadow-sm">No announcements.</div>}</div></section>;
}
