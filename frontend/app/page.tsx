export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <section className="mx-auto max-w-5xl rounded-xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">WorkSphere</p>
        <h1 className="mt-3 text-4xl font-bold">Your connected workplace.</h1>
        <p className="mt-4 max-w-2xl text-slate-600">The platform foundation is ready. Product modules will be introduced in subsequent phases.</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {["People", "Work", "Knowledge"].map((item) => <div key={item} className="rounded-lg border p-4"><h2 className="font-semibold">{item}</h2><p className="mt-1 text-sm text-slate-500">Coming soon</p></div>)}
        </div>
      </section>
    </main>
  );
}

