"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { logout, storedUser, type Role } from "@/lib/api-client";

const links: Array<{ href: string; label: string; roles: Role[] }> = [
  { href: "/dashboard", label: "Dashboard", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/employees", label: "Employees", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD"] },
  { href: "/departments", label: "Departments", roles: ["SUPER_ADMIN", "HR"] },
  { href: "/teams", label: "Teams", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/profile", label: "Profile", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/attendance", label: "Attendance", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/leave", label: "Leave", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/calendar", label: "Calendar", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/projects", label: "Projects", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/tasks", label: "Tasks", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/meetings", label: "Meetings", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/chat", label: "Chat", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/files", label: "Files", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/announcements", label: "Announcements", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/knowledge", label: "Knowledge", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/notifications", label: "Notifications", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/work-plan", label: "Work plan", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/timeline", label: "Timeline", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
  { href: "/reports", label: "Reports", roles: ["SUPER_ADMIN", "HR", "TEAM_LEAD", "EMPLOYEE"] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const user = storedUser();
  const visibleLinks = links.filter((link) => user && link.roles.includes(user.role));

  if (!user) {
    if (typeof window !== "undefined") router.replace("/login");
    return <main className="p-8">Redirecting to login...</main>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/dashboard" className="font-bold text-blue-700">WorkSphere</Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-600 sm:inline">{user.full_name} · {user.role.replace("_", " ")}</span>
            <button className="rounded-md border px-3 py-2 hover:bg-slate-50" onClick={() => { logout(); router.replace("/login"); }}>Log out</button>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6 md:flex-row">
        <nav className="flex gap-2 overflow-x-auto md:w-48 md:flex-col">
          {visibleLinks.map((link) => <Link key={link.href} href={link.href} className={`rounded-md px-3 py-2 text-sm ${pathname === link.href ? "bg-blue-600 text-white" : "text-slate-700 hover:bg-white"}`}>{link.label}</Link>)}
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
