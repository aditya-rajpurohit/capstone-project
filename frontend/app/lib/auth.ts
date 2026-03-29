import { apiFetch } from "./api";

export async function login(email: string, password: string) {
  const res = await apiFetch("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  localStorage.setItem("token", res.access_token);

  return res;
}

export async function register(email: string, password: string) {
  return apiFetch("/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
