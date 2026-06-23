import { Bot, Send, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";

/**
 * Render structured tool-result data as a table or summary card.
 * `data` shape: { tool: string, rows: array }
 */
function DataPayload({ data }) {
  if (!data || !data.rows || data.rows.length === 0) return null;

  const rows = data.rows;
  const keys = Object.keys(rows[0] || {});

  // Label map for friendlier column headers
  const LABELS = {
    sku_id: "SKU",
    lens_type: "Lens Type",
    power: "Power",
    quantity: "Qty",
    reorder_level: "Reorder Level",
    order_id: "Order #",
    customer_name: "Customer",
    store_location: "Store",
    status: "Status",
    risk_level: "Risk",
    breach_probability_pct: "Breach %",
    current_stock: "Stock",
    avg_daily_consumption: "Avg/Day",
    predicted_stockout_date: "Stockout Date",
    days_remaining: "Days Left",
    total: "Total Orders",
    estimated_revenue_inr: "Est. Revenue (₹)",
    average_order_value_inr: "Avg Order (₹)",
  };

  const label = (k) => LABELS[k] || k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  // Special render: order summary (by_status is nested object)
  if (data.tool === "get_order_summary" && rows[0]?.by_status) {
    const summary = rows[0];
    return (
      <div className="mt-2 rounded-lg border border-line bg-slate-50 p-3 text-sm">
        <p className="mb-2 font-semibold text-ink">Order Summary</p>
        <p className="text-slate-500">Total: <span className="font-semibold text-ink">{summary.total}</span></p>
        <div className="mt-2 grid grid-cols-2 gap-1">
          {Object.entries(summary.by_status || {}).map(([status, count]) => (
            <div key={status} className="flex items-center justify-between rounded bg-white border border-line px-2 py-1">
              <span className="text-slate-600">{status}</span>
              <span className="font-semibold text-ink">{count}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Generic table for list results
  if (rows.length > 0 && typeof rows[0] === "object" && !Array.isArray(rows[0])) {
    const visibleKeys = keys.filter((k) => k !== "note" && k !== "date_range");
    return (
      <div className="mt-2 overflow-x-auto rounded-lg border border-line">
        <table className="min-w-full text-xs">
          <thead className="bg-slate-50 border-b border-line">
            <tr>
              {visibleKeys.map((k) => (
                <th key={k} className="px-3 py-2 text-left font-semibold text-slate-500 uppercase tracking-wide">
                  {label(k)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-white">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50">
                {visibleKeys.map((k) => {
                  const val = row[k];
                  const isRisk = k === "risk_level";
                  const riskColors = { High: "text-danger font-semibold", Medium: "text-warning font-semibold", Low: "text-signal font-semibold" };
                  return (
                    <td key={k} className={`px-3 py-2 ${isRisk ? (riskColors[val] || "") : "text-slate-700"}`}>
                      {val === null || val === undefined ? "—" : String(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {rows[0]?.note && (
          <p className="px-3 py-1 text-xs text-slate-400 bg-slate-50 border-t border-line">{rows[0].note}</p>
        )}
      </div>
    );
  }

  return null;
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
          isUser ? "border-signal bg-teal-50 text-signal" : "border-line bg-white text-slate-500"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={`max-w-[80%] space-y-2 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-signal text-white rounded-tr-none"
              : "bg-white border border-line text-slate-700 rounded-tl-none"
          }`}
        >
          {msg.content}
        </div>
        {msg.data && <DataPayload data={msg.data} />}
        <span className="text-xs text-slate-400">
          {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}

const SUGGESTED_PROMPTS = [
  "Which items are running low on stock?",
  "Show me all high-risk orders right now",
  "How many orders were placed this month?",
  "Which SKUs are likely to run out next week?",
  "What's the estimated revenue for this month?",
];

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your Eluno operations copilot. Ask me anything about your orders, inventory, SLA risk, or revenue.",
      data: null,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function sendMessage(text) {
    const userText = (text || input).trim();
    if (!userText || isLoading) return;

    setInput("");
    setError("");

    const userMsg = { role: "user", content: userText, data: null, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.chat(userText, conversationId);
      if (!conversationId) setConversationId(response.conversation_id);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.reply,
          data: response.data,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I couldn't process that request. Please try again.",
          data: null,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <section className="flex h-[calc(100vh-10rem)] flex-col gap-4">
      {/* Header */}
      <div className="flex items-center gap-3 rounded-xl border border-line bg-white p-4 shadow-sm">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-50 border border-teal-200">
          <Bot className="h-5 w-5 text-signal" />
        </div>
        <div>
          <h2 className="font-semibold text-ink">Eluno Operations Copilot</h2>
          <p className="text-xs text-slate-500">Powered by Gemini · Queries live database</p>
        </div>
        {conversationId && (
          <span className="ml-auto text-xs text-slate-400 font-mono">
            {conversationId.slice(0, 8)}…
          </span>
        )}
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-line bg-white p-4 space-y-4">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line bg-white text-slate-500">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-xl rounded-tl-none border border-line bg-white px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce [animation-delay:0ms]" />
                <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested prompts */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              className="btn-secondary text-xs py-1.5 px-3"
              onClick={() => sendMessage(prompt)}
              disabled={isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>
      )}

      {/* Input bar */}
      <div className="flex gap-2 rounded-xl border border-line bg-white p-2 shadow-sm">
        <textarea
          ref={inputRef}
          className="flex-1 resize-none rounded-lg border-0 bg-transparent px-3 py-2 text-sm text-ink placeholder-slate-400 outline-none"
          placeholder="Ask about orders, inventory, SLA risk, revenue…"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <button
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-signal text-white transition hover:bg-teal-800 disabled:opacity-50"
          onClick={() => sendMessage()}
          disabled={isLoading || !input.trim()}
          title="Send"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </section>
  );
}
