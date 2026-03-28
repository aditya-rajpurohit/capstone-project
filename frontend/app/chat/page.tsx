"use client";
import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! Ask me anything." }
  ]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input) return;

    const newMsgs = [...messages, { role: "user", content: input }];
    setMessages(newMsgs);
    setInput("");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: input })
      });

      const data = await res.json();

      setMessages([...newMsgs, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setMessages([...newMsgs, { role: "assistant", content: "Error connecting to backend" }]);
    }
  };

  return (
    <div className="flex flex-col h-[90vh] p-4">
      <div className="flex-1 overflow-y-auto mb-4">
        {messages.map((m, i) => (
          <div key={i} className={`mb-2 ${m.role === "user" ? "text-right" : ""}`}>
            <span className="inline-block bg-gray-200 p-2 rounded">
              {m.content}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 border p-2 rounded"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
        />
        <button onClick={sendMessage} className="btn">
          Send
        </button>
      </div>
    </div>
  );
}
