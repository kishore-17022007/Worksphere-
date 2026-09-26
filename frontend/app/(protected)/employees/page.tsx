"use client";

import { useEffect, useState } from "react";
import { apiFetch, type CurrentUser } from "@/lib/api-client";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<CurrentUser[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<CurrentUser[]>("/employees").then(setEmployees).catch(() => setError("Unable to load employees.")); }, []);
  return <section><h1 className="text-3xl font-bold">Employees</h1><p className="mt-2 text-slate-600">Manage people and organizational assignments.</p>{error && <p className="mt-4 text-red-600">{error}</p>}<div className="mt-6 overflow-hidden rounded-xl bg-white shadow-sm"><div className="grid grid-cols-3 border-b px-5 py-3 text-sm font-semibold text-slate-500"><span>Name</span><span>Email</span><span>Role</span></div>{employees.length ? employees.map((employee) => <div key={employee.id} className="grid grid-cols-3 border-b px-5 py-4 text-sm"><span>{employee.full_name}</span><span>{employee.email}</span><span>{employee.role}</span></div>) : <p className="px-5 py-8 text-sm text-slate-500">No employees found.</p>}</div></section>;
}
