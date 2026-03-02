"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import clsx from "clsx";
import type { AiChatMessage } from "@/lib/kanbanApi";

const EMPTY_MESSAGE = "Ask the assistant to create, move, or update cards.";

type AiChatSidebarProps = {
  messages: AiChatMessage[];
  isLoading: boolean;
  error: string;
  onSend: (message: string) => Promise<void>;
};

export const AiChatSidebar = ({
  messages,
  isLoading,
  error,
  onSend,
}: AiChatSidebarProps) => {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) {
      return;
    }
    setInput("");
    await onSend(trimmed);
  };

  return (
    <aside className="flex h-full flex-col rounded-3xl border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Board Copilot
          </h2>
          <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
            {EMPTY_MESSAGE}
          </p>
        </div>
        <span
          className={clsx(
            "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]",
            isLoading
              ? "bg-[var(--accent-yellow)]/20 text-[var(--navy-dark)]"
              : "bg-[var(--surface)] text-[var(--gray-text)]"
          )}
        >
          {isLoading ? "Thinking" : "Ready"}
        </span>
      </div>

      <div className="mt-5 flex flex-1 flex-col gap-4 overflow-y-auto pr-2" aria-live="polite">
        {messages.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[var(--stroke)] bg-[var(--surface)] px-4 py-6 text-sm text-[var(--gray-text)]">
            Start with something like "Move the top backlog card to In Progress.".
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={clsx(
                "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
                message.role === "user"
                  ? "self-end bg-[var(--primary-blue)] text-white"
                  : "self-start bg-[var(--surface)] text-[var(--navy-dark)]"
              )}
            >
              {message.content}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-600">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the assistant..."
          rows={3}
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={isLoading}
          className={clsx(
            "w-full rounded-full px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white transition",
            isLoading
              ? "cursor-not-allowed bg-[var(--secondary-purple)]/60"
              : "bg-[var(--secondary-purple)] hover:brightness-110"
          )}
        >
          {isLoading ? "Sending" : "Send"}
        </button>
      </form>
    </aside>
  );
};
