import type { BoardData, Card } from "@/lib/kanban";

type ApiError = {
  detail?: string;
};

const jsonRequest = async <T>(path: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    credentials: "same-origin",
    ...options,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
};

const readErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = (await response.json()) as ApiError;
    if (data?.detail) {
      return data.detail;
    }
  } catch {
    // Ignore JSON parse errors and fall back to text.
  }

  try {
    return await response.text();
  } catch {
    return response.statusText;
  }
};

export const getBoard = async (): Promise<BoardData> =>
  jsonRequest<BoardData>("/api/board");

export const renameColumn = async (columnId: string, title: string) =>
  jsonRequest<{ status: string }>(`/api/columns/${columnId}/rename`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });

export const createCard = async (
  columnId: string,
  title: string,
  details: string
): Promise<Card> =>
  jsonRequest<Card>("/api/cards", {
    method: "POST",
    body: JSON.stringify({ columnId, title, details }),
  });

export const updateCard = async (
  cardId: string,
  title?: string,
  details?: string
): Promise<Card> =>
  jsonRequest<Card>(`/api/cards/${cardId}`, {
    method: "PATCH",
    body: JSON.stringify({ title, details }),
  });

export const deleteCard = async (cardId: string) =>
  jsonRequest<{ status: string }>(`/api/cards/${cardId}`, {
    method: "DELETE",
  });

export const moveCard = async (
  cardId: string,
  toColumnId: string,
  position: number
) =>
  jsonRequest<{ status: string }>(`/api/cards/${cardId}/move`, {
    method: "POST",
    body: JSON.stringify({ toColumnId, position }),
  });
