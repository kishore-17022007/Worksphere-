"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
type Meeting = { id: string; title: string; description: string | null; starts_at: string; ends_at: string; location: string | null; meeting_link: string | null };
import { apiFetch } from "@/lib/api-client";
export default function MeetingPage() { const params = useParams<{ id: string }>(); const [meeting, setMeeting] = useState<Meeting | null>(null); useEffect(() => { apiFetch<Meeting>(`/work/meetings/${params.id}`).then(setMeeting).catch(() => setMeeting(null)); }, [params.id]); if (!meeting) return <p className="text-slate-500">Loading meeting...</p>; return <section><p className="text-sm font-medium text-blue-600">Meeting</p><h1 className="mt-2 text-3xl font-bold">{meeting.title}</h1><p className="mt-3 text-slate-600">{meeting.description || "No description"}</p><div className="mt-6 rounded-xl bg-white p-6 shadow-sm"><p>{new Date(meeting.starts_at).toLocaleString()} – {new Date(meeting.ends_at).toLocaleTimeString()}</p><p className="mt-2 text-sm text-slate-500">{meeting.location || meeting.meeting_link || "No location"}</p><Link href={`/meetings/${meeting.id}/mom`} className="mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm text-white">Open MOM</Link></div></section>; }
