"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Notification = { id: string; title: string; body: string; is_read: boolean; created_at: string };
export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  useEffect(() => { apiFetch<Notification[]>("/notifications").then(setItems).catch(() => setItems([])); }, []);
  async function markRead(id: string) { await apiFetch(`/notifications/${id}/read`, { method: "POST" }); setItems((current) => current.map((item) => item.id === id ? { ...item, is_read: true } : item)); }
  return <section><h1 className="text-3xl font-bold">Notifications</h1><p className="mt-2 text-slate-600">Stay up to date with your work.</p><div className="mt-6 rounded-xl bg-white shadow-sm">{items.length ? items.map((item) => <button key={item.id} onClick={() => markRead(item.id)} className={`block w-full border-b px-5 py-4 text-left ${item.is_read ? "" : "bg-blue-50"}`}><div className="flex justify-between"><span className="font-medium">{item.title}</span><span className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</span></div><p className="mt-1 text-sm text-slate-600">{item.body}</p></button>) : <p className="px-5 py-8 text-sm text-slate-500">No notifications.</p>}</div></section>;
}
