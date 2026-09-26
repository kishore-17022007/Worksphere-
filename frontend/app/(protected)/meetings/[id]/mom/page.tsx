"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
type MOM = { id: string; summary: string; created_at: string; action_items: Array<{ id: string; title: string; status: string }> };
export default function MOMPage() { const params = useParams<{ id: string }>(); const [mom, setMom] = useState<MOM | null>(null); useEffect(() => { apiFetch<MOM>(`/work/meetings/${params.id}/mom`).then(setMom).catch(() => setMom(null)); }, [params.id]); return <section><h1 className="text-3xl font-bold">Minutes of Meeting</h1>{mom ? <div className="mt-6 rounded-xl bg-white p-6 shadow-sm"><p className="text-slate-700">{mom.summary}</p><h2 className="mt-6 font-semibold">Action items</h2><div className="mt-3 space-y-2">{mom.action_items.map((item) => <div key={item.id} className="flex justify-between rounded border p-3 text-sm"><span>{item.title}</span><span className="text-slate-500">{item.status}</span></div>)}</div></div> : <p className="mt-4 text-slate-500">No minutes recorded yet.</p>}</section>; }
