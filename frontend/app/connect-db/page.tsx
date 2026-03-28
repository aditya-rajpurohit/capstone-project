"use client";
import { useState } from "react";

export default function ConnectDB() {
  const [dbs, setDbs] = useState(["Postgres-1", "Mongo-Cluster"]);
  const [newDb, setNewDb] = useState("");

  const addDb = () => {
    if (!newDb) return;
    setDbs([...dbs, newDb]);
    setNewDb("");
  };

  const deleteDb = (index: number) => {
    setDbs(dbs.filter((_, i) => i !== index));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Connected Databases</h1>

      <div className="flex gap-2 my-4">
        <input
          value={newDb}
          onChange={(e) => setNewDb(e.target.value)}
          placeholder="DB name"
          className="input"
        />
        <button onClick={addDb} className="btn">Add</button>
      </div>

      <ul>
        {dbs.map((db, i) => (
          <li key={i} className="flex justify-between bg-gray-100 p-3 mb-2 rounded">
            {db}
            <button onClick={() => deleteDb(i)} className="text-red-500">
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
