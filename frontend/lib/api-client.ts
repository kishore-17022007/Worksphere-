const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("worksphere_access_token") : null;
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const health = () => apiFetch<{ status: string }>("/health");

export type Role = "SUPER_ADMIN" | "HR" | "TEAM_LEAD" | "EMPLOYEE";
export type CurrentUser = { id: string; email: string; full_name: string; role: Role; is_active: boolean };
export type AuthResponse = { access_token: string; refresh_token: string; token_type: "bearer"; user: CurrentUser };

export async function login(email: string, password: string): Promise<AuthResponse> {
  const result = await apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  window.localStorage.setItem("worksphere_access_token", result.access_token);
  window.localStorage.setItem("worksphere_user", JSON.stringify(result.user));
  return result;
}

export function logout(): void {
  window.localStorage.removeItem("worksphere_access_token");
  window.localStorage.removeItem("worksphere_user");
}

export function storedUser(): CurrentUser | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem("worksphere_user");
  return value ? (JSON.parse(value) as CurrentUser) : null;
}
