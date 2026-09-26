"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type DocumentRecord = { id: string; title: string; summary: string | null; category_id: string; updated_at: string };
export default function KnowledgePage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => { apiFetch<DocumentRecord[]>("/knowledge/documents").then(setDocuments).catch(() => setDocuments([])); }, []);
  const filtered = documents.filter((document) => `${document.title} ${document.summary || ""}`.toLowerCase().includes(query.toLowerCase()));
  return <section><h1 className="text-3xl font-bold">Knowledge base</h1><p className="mt-2 text-slate-600">Permission-aware company knowledge and policies.</p><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search documents" className="mt-6 w-full rounded-md border bg-white px-3 py-2 text-sm" /><div className="mt-4 grid gap-4 md:grid-cols-2">{filtered.length ? filtered.map((document) => <article key={document.id} className="rounded-xl bg-white p-5 shadow-sm"><h2 className="font-semibold">{document.title}</h2><p className="mt-2 text-sm text-slate-600">{document.summary || "No summary"}</p><p className="mt-4 text-xs text-slate-400">Updated {new Date(document.updated_at).toLocaleDateString()}</p></article>) : <div className="rounded-xl bg-white p-8 text-sm text-slate-500 shadow-sm">No documents found.</div>}</div></section>;
}
