export default function DashboardPage() {
  return <section><h1 className="text-3xl font-bold">Dashboard</h1><p className="mt-2 text-slate-600">Welcome to your WorkSphere workspace.</p><div className="mt-8 grid gap-4 sm:grid-cols-3">{["People", "Teams", "Company updates"].map((item) => <div key={item} className="rounded-xl bg-white p-5 shadow-sm"><h2 className="font-semibold">{item}</h2><p className="mt-2 text-sm text-slate-500">No updates yet.</p></div>)}</div></section>;
}
