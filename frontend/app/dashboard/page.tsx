import Link from "next/link";

export default function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Agent Dashboard</h1>

      <div className="grid grid-cols-3 gap-4 mt-6">
        <Link href="/chat" className="card">Go to Chat</Link>
        <Link href="/connect-db" className="card">Manage Databases</Link>
        <div className="card">More Features Soon</div>
      </div>
    </div>
  );
}
