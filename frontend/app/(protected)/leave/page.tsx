"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Leave = { id: string; leave_type_id: string; start_date: string; end_date: string; reason: string | null; status: string };
export default function LeavePage() {
  const [requests, setRequests] = useState<Leave[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<Leave[]>("/leave/requests").then(setRequests).catch(() => setError("Unable to load leave requests.")); }, []);
  return <section><h1 className="text-3xl font-bold">Leave</h1><p className="mt-2 text-slate-600">Submit and track your leave requests.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 rounded-xl bg-white shadow-sm"><h2 className="border-b px-5 py-4 font-semibold">My requests</h2>{requests.length ? requests.map((row) => <div key={row.id} className="grid gap-2 border-b px-5 py-4 text-sm sm:grid-cols-4"><span>{row.start_date} – {row.end_date}</span><span>{row.reason || "No reason"}</span><span>{row.status}</span><span className="text-slate-500">{row.leave_type_id}</span></div>) : <p className="px-5 py-8 text-sm text-slate-500">No leave requests.</p>}</div></section>;
}
