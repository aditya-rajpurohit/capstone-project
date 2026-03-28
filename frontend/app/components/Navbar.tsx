"use client";
import Link from "next/link";

export default function Navbar() {
  return (
    <div className="flex gap-6 p-4 bg-black text-white">
      <Link href="/dashboard">Dashboard</Link>
      <Link href="/connect-db">Databases</Link>
      <Link href="/chat">Chat</Link>
    </div>
  );
}
