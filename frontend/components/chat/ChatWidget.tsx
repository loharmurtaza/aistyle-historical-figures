"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

// ── Types ────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3001";

// ── ChatWidget ────────────────────────────────────────────────────────────

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionIdRef = useRef<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Generate a stable session ID once on mount.
  useEffect(() => {
    sessionIdRef.current = crypto.randomUUID();
  }, []);

  // Scroll to the latest message whenever messages change.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus the input when the panel opens.
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [open]);

  // ── Send message ────────────────────────────────────────────────────────

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setLoading(true);

    // Append user message.
    setMessages((prev) => [...prev, { role: "user", content: text }]);

    // Placeholder for streaming assistant reply.
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", streaming: true },
    ]);

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionIdRef.current }),
        signal: abort.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE lines are separated by "\n\n".
        const parts = buffer.split("\n\n");
        // Keep the last (possibly incomplete) chunk in the buffer.
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          for (const line of part.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6);
            if (raw === "[DONE]") break;
            try {
              const { token } = JSON.parse(raw) as { token: string };
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "assistant") {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + token,
                  };
                }
                return updated;
              });
            } catch {
              // malformed SSE line — skip
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant") {
          updated[updated.length - 1] = {
            ...last,
            content: "Sorry, something went wrong. Please try again.",
            streaming: false,
          };
        }
        return updated;
      });
    } finally {
      // Mark streaming as done.
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant") {
          updated[updated.length - 1] = { ...last, streaming: false };
        }
        return updated;
      });
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function handleClose() {
    abortRef.current?.abort();
    setOpen(false);
  }

  async function handleReset() {
    if (loading || messages.length === 0) return;
    abortRef.current?.abort();
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/chat/${sessionIdRef.current}/reset`,
        { method: "POST" },
      );
      if (res.ok) {
        const { new_session_id } = await res.json() as { new_session_id: string };
        sessionIdRef.current = new_session_id;
      } else {
        // Even if the backend call fails, rotate session locally.
        sessionIdRef.current = crypto.randomUUID();
      }
    } catch {
      sessionIdRef.current = crypto.randomUUID();
    }
    setMessages([]);
    setInput("");
    setLoading(false);
  }

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <>
      {/* ── Chat panel ──────────────────────────────────────────────────── */}
      <div
        aria-label="Chat with ChronoCanvas AI"
        className={`
          fixed bottom-24 right-5 z-40 flex flex-col
          w-[360px] max-w-[calc(100vw-2.5rem)]
          bg-cream border border-dark/10 shadow-2xl
          transition-all duration-300 origin-bottom-right
          ${open
            ? "opacity-100 scale-100 pointer-events-auto"
            : "opacity-0 scale-95 pointer-events-none"
          }
        `}
        style={{ height: "520px" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 bg-dark flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse" />
            <span className="font-serif text-sm text-cream">
              Chrono<span className="text-gold italic">Canvas</span> Assistant
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleReset}
              aria-label="Reset conversation"
              disabled={messages.length === 0 || loading}
              className="text-cream/50 hover:text-cream transition-colors duration-150 leading-none disabled:opacity-30 disabled:cursor-not-allowed"
              title="Start a new conversation"
            >
              <ResetIcon />
            </button>
            <button
              onClick={handleClose}
              aria-label="Close chat"
              className="text-cream/50 hover:text-cream transition-colors duration-150 leading-none"
            >
              <CloseIcon />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scroll-smooth">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-6">
              <span className="text-3xl select-none">🏛️</span>
              <p className="font-serif text-dark/70 text-sm leading-relaxed">
                Ask me anything about historical figures — who they were, their
                eras, origins, or what&apos;s in this catalog.
              </p>
            </div>
          )}

          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="bg-dark text-cream text-sm font-sans px-4 py-2.5 max-w-[80%] leading-relaxed">
                  {msg.content}
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-start">
                <div className="bg-parchment text-dark text-sm font-sans px-4 py-2.5 max-w-[85%] leading-relaxed">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
                      strong: ({ children }) => <strong className="font-semibold text-dark">{children}</strong>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mt-1">{children}</ol>,
                      ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mt-1">{children}</ul>,
                      li: ({ children }) => <li className="leading-snug">{children}</li>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                  {msg.streaming && <BlinkCursor />}
                </div>
              </div>
            )
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex-shrink-0 border-t border-dark/10 px-4 py-3 flex items-center gap-2 bg-cream">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask about a historical figure…"
            className="
              flex-1 bg-parchment text-dark text-sm font-sans
              px-3 py-2.5 outline-none placeholder:text-dark/40
              disabled:opacity-50
            "
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            aria-label="Send message"
            className="
              flex-shrink-0 bg-dark text-cream w-9 h-9 flex items-center
              justify-center hover:bg-dark/80 transition-colors duration-150
              disabled:opacity-40 disabled:cursor-not-allowed
            "
          >
            <SendIcon />
          </button>
        </div>
      </div>

      {/* ── Toggle button ───────────────────────────────────────────────── */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close chat" : "Open chat"}
        className="
          fixed bottom-5 right-5 z-50
          w-14 h-14 rounded-full bg-dark text-cream shadow-lg
          flex items-center justify-center
          hover:bg-dark/80 transition-all duration-200
          hover:shadow-xl hover:scale-105
        "
      >
        <span
          className={`absolute transition-all duration-200 ${
            open ? "opacity-100 scale-100" : "opacity-0 scale-75"
          }`}
        >
          <CloseIcon size={20} />
        </span>
        <span
          className={`absolute transition-all duration-200 ${
            open ? "opacity-0 scale-75" : "opacity-100 scale-100"
          }`}
        >
          <ChatIcon />
        </span>
      </button>
    </>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────

function BlinkCursor() {
  return (
    <span className="inline-block w-[2px] h-[0.9em] bg-gold ml-0.5 animate-pulse align-middle" />
  );
}

function ChatIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function CloseIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 .49-4.95" />
    </svg>
  );
}
