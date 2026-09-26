"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Meeting = { id: string; title: string; description: string | null; starts_at: string; ends_at: string };
export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  useEffect(() => { apiFetch<Meeting[]>("/work/meetings").then(setMeetings).catch(() => setMeetings([])); }, []);
  return <section><h1 className="text-3xl font-bold">Meetings</h1><p className="mt-2 text-slate-600">Meetings, agendas, decisions, and action items.</p><div className="mt-6 space-y-3">{meetings.length ? meetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}`} className="block rounded-xl bg-white p-5 shadow-sm hover:shadow-md"><h2 className="font-semibold">{meeting.title}</h2><p className="mt-1 text-sm text-slate-500">{new Date(meeting.starts_at).toLocaleString()}</p></Link>) : <div className="rounded-xl bg-white p-8 text-sm text-slate-500 shadow-sm">No meetings found.</div>}</div></section>;
}
