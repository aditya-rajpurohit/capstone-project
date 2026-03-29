import { BASE_URL } from "../lib/config";

export async function apiFetch(
  path: string,
  options: RequestInit = {}
) {
  const token = localStorage.getItem("token");

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "API Error");
  }

  return res.json();
}

// export async function createDatabase(data: {
//   name: string;
//   host: string;
//   port: number;
//   database_name: string;
//   username: string;
//   password: string;
// }) {
//   return apiFetch("/v1/datasources", {
//     method: "POST",
//     body: JSON.stringify({
//       name: data.name,
//       dialect: "postgres",
//       config: data,
//     }),
//   });
// }

// export async function getDatabases() {
//   return apiFetch("/v1/datasources");
// }


// export async function createConversation(title?: string) {
//   return apiFetch("/v1/conversations", {
//     method: "POST",
//     body: JSON.stringify({ title }),
//   });
// }

// export async function getConversations() {
//   return apiFetch("/v1/conversations");
// }

