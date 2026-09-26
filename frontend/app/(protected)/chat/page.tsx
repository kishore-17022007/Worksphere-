"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Conversation = { id: string; title: string; conversation_type: string; unread_count?: number };
type Message = { id: string; body: string; sender_id: string; created_at: string; reply_to_id?: string | null };

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [body, setBody] = useState("");
  const [search, setSearch] = useState("");
  const socket = useRef<WebSocket | null>(null);
  useEffect(() => { apiFetch<Conversation[]>("/chat/conversations").then(setConversations).catch(() => setConversations([])); }, []);
  useEffect(() => {
    if (!selected) return;
    apiFetch<Message[]>(`/chat/conversations/${selected}/messages`).then(setMessages).catch(() => setMessages([]));
    const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/^http/, "ws").replace(/\/api\/v1$/, "");
    socket.current = new WebSocket(`${base}/api/v1/ws/conversations/${selected}`);
    socket.current.onmessage = (event) => { const message = JSON.parse(event.data) as Message; setMessages((current) => [...current, message]); };
    return () => socket.current?.close();
  }, [selected]);
  const visible = useMemo(() => conversations.filter((item) => item.title.toLowerCase().includes(search.toLowerCase())), [conversations, search]);
  async function send() {
    if (!selected || !body.trim()) return;
    if (socket.current?.readyState === WebSocket.OPEN) socket.current.send(JSON.stringify({ body }));
    else await apiFetch(`/conversations/${selected}/messages`, { method: "POST", body: JSON.stringify({ body }) });
    setBody("");
  }
  return <section className="h-[calc(100vh-9rem)]"><h1 className="text-3xl font-bold">Chat</h1><div className="mt-6 grid h-[calc(100%-4rem)] overflow-hidden rounded-xl bg-white shadow-sm md:grid-cols-[18rem_1fr]"><aside className="border-r"><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search conversations" className="m-3 w-[calc(100%-1.5rem)] rounded-md border px-3 py-2 text-sm" /><div>{visible.map((conversation) => <button key={conversation.id} onClick={() => setSelected(conversation.id)} className={`flex w-full items-center justify-between border-b px-4 py-3 text-left text-sm ${selected === conversation.id ? "bg-blue-50" : "hover:bg-slate-50"}`}><span>{conversation.title}</span>{conversation.unread_count ? <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs text-white">{conversation.unread_count}</span> : null}</button>)}</div></aside><div className="flex min-h-0 flex-col"><div className="flex-1 overflow-y-auto p-5">{selected ? messages.map((message) => <div key={message.id} className="mb-3 max-w-xl rounded-lg bg-slate-100 p-3 text-sm"><p>{message.body}</p><p className="mt-1 text-xs text-slate-500">{new Date(message.created_at).toLocaleString()}</p></div>) : <p className="text-sm text-slate-500">Select a conversation.</p>}</div><div className="flex gap-2 border-t p-3"><input value={body} onChange={(event) => setBody(event.target.value)} onKeyDown={(event) => event.key === "Enter" && send()} placeholder="Write a message..." className="flex-1 rounded-md border px-3 py-2 text-sm" /><button onClick={send} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white">Send</button></div></div></div></section>;
}
