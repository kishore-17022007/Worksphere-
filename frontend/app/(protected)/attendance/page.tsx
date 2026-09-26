"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Attendance = { id: string; date: string; check_in: string | null; check_out: string | null; working_duration_minutes: number | null; status: string };

export default function AttendancePage() {
  const [today, setToday] = useState<Attendance | null>(null);
  const [history, setHistory] = useState<Attendance[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try { setToday(await apiFetch<Attendance>("/attendance/today")); setHistory(await apiFetch<Attendance[]>("/attendance/history")); }
    catch { setError("Unable to load attendance."); }
  }
  useEffect(() => { load(); }, []);
  async function action(path: string) {
    setBusy(true); setError("");
    try { await apiFetch(path, { method: "POST" }); await load(); } catch { setError("Attendance action could not be completed."); } finally { setBusy(false); }
  }
  return <section><h1 className="text-3xl font-bold">Attendance</h1><p className="mt-2 text-slate-600">Official attendance times are recorded by the server.</p>
    <div className="mt-6 rounded-xl bg-white p-6 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-sm text-slate-500">Today</p><p className="mt-1 text-xl font-semibold">{today?.status ?? "Not checked in"}</p></div><div className="flex gap-2"><button disabled={busy || !!today?.check_in} onClick={() => action("/attendance/check-in")} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50">Check in</button><button disabled={busy || !today?.check_in || !!today?.check_out} onClick={() => action("/attendance/check-out")} className="rounded-md border px-4 py-2 text-sm disabled:opacity-50">Check out</button></div></div>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}</div>
    <div className="mt-6 rounded-xl bg-white shadow-sm"><h2 className="border-b px-5 py-4 font-semibold">History</h2>{history.length ? history.map((row) => <div key={row.id} className="grid grid-cols-2 border-b px-5 py-4 text-sm sm:grid-cols-4"><span>{row.date}</span><span>{row.check_in ? new Date(row.check_in).toLocaleTimeString() : "—"}</span><span>{row.check_out ? new Date(row.check_out).toLocaleTimeString() : "—"}</span><span>{row.status}</span></div>) : <p className="px-5 py-8 text-sm text-slate-500">No attendance records.</p>}</div>
  </section>;
}
