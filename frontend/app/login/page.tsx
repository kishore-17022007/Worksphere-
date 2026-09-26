"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setLoading(true);
    try { await login(email, password); router.replace("/dashboard"); }
    catch { setError("Invalid email or password."); }
    finally { setLoading(false); }
  }

  return <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
    <form onSubmit={submit} className="w-full max-w-md rounded-xl bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">WorkSphere</p>
      <h1 className="mt-2 text-2xl font-bold">Sign in</h1>
      <p className="mt-2 text-sm text-slate-500">Use your company account to continue.</p>
      <label className="mt-6 block text-sm font-medium">Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded-md border px-3 py-2" /></label>
      <label className="mt-4 block text-sm font-medium">Password<input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full rounded-md border px-3 py-2" /></label>
      {error && <p role="alert" className="mt-4 text-sm text-red-600">{error}</p>}
      <button disabled={loading} className="mt-6 w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50">{loading ? "Signing in..." : "Sign in"}</button>
      <a href="/forgot-password" className="mt-4 block text-center text-sm text-blue-700">Forgot password?</a>
    </form>
  </main>;
}
