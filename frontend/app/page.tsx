"use client";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <div style={styles.container}>
      <h1>Welcome</h1>

      <button onClick={() => router.push("/auth/login")}>
        Login
      </button>

      <button onClick={() => router.push("/auth/register")}>
        Register
      </button>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    justifyContent: "center",
    alignItems: "center",
    gap: "10px",
  },
};
