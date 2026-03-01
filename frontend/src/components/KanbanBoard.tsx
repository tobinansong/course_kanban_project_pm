"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { AiChatSidebar } from "@/components/AiChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { moveCard, type BoardData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  getBoard,
  moveCard as moveCardApi,
  renameColumn,
  sendStructuredChat,
  type AiChatMessage,
} from "@/lib/kanbanApi";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [isBoardLoading, setIsBoardLoading] = useState(true);
  const [boardError, setBoardError] = useState("");
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<AiChatMessage[]>([]);
  const [chatError, setChatError] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  const refreshBoard = async () => {
    try {
      setIsBoardLoading(true);
      setBoardError("");
      const nextBoard = await getBoard();
      setBoard(nextBoard);
    } catch (error) {
      setBoardError(error instanceof Error ? error.message : "Failed to load board");
    } finally {
      setIsBoardLoading(false);
    }
  };

  useEffect(() => {
    void refreshBoard();
  }, []);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board) {
      return;
    }

    const nextColumns = moveCard(
      board.columns,
      active.id as string,
      over.id as string
    );
    const nextLocation = findCardLocation(nextColumns, active.id as string);

    setBoard((prev) =>
      prev
        ? {
            ...prev,
            columns: nextColumns,
          }
        : prev
    );

    if (!nextLocation) {
      return;
    }

    void moveCardApi(
      active.id as string,
      nextLocation.columnId,
      nextLocation.position
    ).catch(() => {
      void refreshBoard();
    });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            columns: prev.columns.map((column) =>
              column.id === columnId ? { ...column, title } : column
            ),
          }
        : prev
    );
    void renameColumn(columnId, title).catch(() => {
      void refreshBoard();
    });
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    void createCard(columnId, title, details).then((card) => {
      setBoard((prev) =>
        prev
          ? {
              ...prev,
              cards: {
                ...prev.cards,
                [card.id]: card,
              },
              columns: prev.columns.map((column) =>
                column.id === columnId
                  ? { ...column, cardIds: [...column.cardIds, card.id] }
                  : column
              ),
            }
          : prev
      );
    }).catch(() => {
      void refreshBoard();
    });
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setBoard((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
    void deleteCard(cardId).catch(() => {
      void refreshBoard();
    });
  };

  const handleChatSend = async (message: string) => {
    const historySnapshot = chatHistory;
    setChatError("");
    setIsChatLoading(true);
    setChatHistory((prev) => [...prev, { role: "user", content: message }]);

    try {
      const response = await sendStructuredChat(message, historySnapshot);
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: response.message },
      ]);
      await refreshBoard();
    } catch (error) {
      setChatError(
        error instanceof Error ? error.message : "AI request failed"
      );
    } finally {
      setIsChatLoading(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (isBoardLoading && !board) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] text-sm font-semibold text-[var(--gray-text)]">
        Loading board...
      </div>
    );
  }

  if (!board) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] text-sm font-semibold text-[var(--gray-text)]">
        {boardError || "Board unavailable"}
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        {boardError ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600">
            {boardError}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section className="grid gap-6 lg:grid-cols-5">
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId])}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <AiChatSidebar
            messages={chatHistory}
            isLoading={isChatLoading}
            error={chatError}
            onSend={handleChatSend}
          />
        </div>
      </main>
    </div>
  );
};

const findCardLocation = (columns: BoardData["columns"], cardId: string) => {
  for (const column of columns) {
    const position = column.cardIds.indexOf(cardId);
    if (position >= 0) {
      return { columnId: column.id, position };
    }
  }
  return null;
};
