import { jwtDecode } from "jwt-decode";

const TOKEN_KEY = "auth_token";

interface DecodedToken {
  sub: string;
  id: number;
  role: "employee" | "manager" | "admin";
  exp: number;
  iat: number;
}

interface User {
  id: number;
  username: string;
  role: "employee" | "manager" | "admin";
}

export async function login(
  username: string,
  password: string
): Promise<{ token: string; user: User }> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Login failed");
  }

  const data = await response.json();
  const token = data.access_token;
  const user = data.user;

  localStorage.setItem(TOKEN_KEY, token);
  return { token, user };
}

export async function register(
  username: string,
  password: string,
  role: "employee" | "manager" | "admin" = "employee"
): Promise<{ message: string }> {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Registration failed");
  }

  return response.json();
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  const token = getToken();
  if (!token) return null;

  try {
    const decoded = jwtDecode<DecodedToken>(token);

    // Check if token is expired
    if (decoded.exp * 1000 < Date.now()) {
      logout();
      return null;
    }

    return {
      id: decoded.id,
      username: decoded.sub,
      role: decoded.role,
    };
  } catch {
    logout();
    return null;
  }
}

export function logout(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function isAuthenticated(): boolean {
  return getUser() !== null;
}

export function getAuthHeader(): { Authorization: string } | {} {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
