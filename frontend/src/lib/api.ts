import { z } from "zod";

import {
  bookSchema,
  bookSummaryListSchema,
  chapterSchema,
  mediaRefSchema,
  pageSchema,
  type Book,
  type BookSummary,
  type Chapter,
  type MediaRef,
  type Page,
} from "./schemas";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    let code = "error";
    let detail = res.statusText;
    try {
      const body = await res.json();
      code = body.code ?? code;
      detail = body.detail ?? detail;
    } catch {
      /* Antwort ohne JSON-Body */
    }
    throw new ApiError(res.status, code, detail);
  }
  const data = await res.json();
  return schema.parse(data);
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const res = await fetch(`/api${path}`, init);
  if (!res.ok) {
    throw new ApiError(res.status, "error", res.statusText);
  }
}

export const api = {
  // --- Books ---
  listBooks: (): Promise<BookSummary[]> =>
    request("/books", bookSummaryListSchema),
  getBook: (id: string): Promise<Book> => request(`/books/${id}`, bookSchema),
  createBook: (data: { title: string; description: string }): Promise<Book> =>
    request("/books", bookSchema, { method: "POST", body: JSON.stringify(data) }),
  updateBook: (
    id: string,
    data: { title: string; description: string },
  ): Promise<Book> =>
    request(`/books/${id}`, bookSchema, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteBook: (id: string): Promise<void> =>
    requestVoid(`/books/${id}`, { method: "DELETE" }),

  // --- Chapters ---
  createChapter: (bookId: string, title: string): Promise<Chapter> =>
    request(`/books/${bookId}/chapters`, chapterSchema, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  updateChapter: (bookId: string, chapterId: string, title: string): Promise<Chapter> =>
    request(`/books/${bookId}/chapters/${chapterId}`, chapterSchema, {
      method: "PUT",
      body: JSON.stringify({ title }),
    }),
  deleteChapter: (bookId: string, chapterId: string): Promise<void> =>
    requestVoid(`/books/${bookId}/chapters/${chapterId}`, { method: "DELETE" }),
  moveChapter: (bookId: string, chapterId: string, position: number): Promise<Book> =>
    request(`/books/${bookId}/chapters/${chapterId}/move`, bookSchema, {
      method: "POST",
      body: JSON.stringify({ position }),
    }),

  // --- Pages ---
  createPage: (bookId: string, chapterId: string, text = ""): Promise<Page> =>
    request(`/books/${bookId}/chapters/${chapterId}/pages`, pageSchema, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  updatePage: (
    bookId: string,
    chapterId: string,
    pageId: string,
    data: { text: string; image: MediaRef | null; audio: MediaRef | null },
  ): Promise<Page> =>
    request(`/books/${bookId}/chapters/${chapterId}/pages/${pageId}`, pageSchema, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deletePage: (bookId: string, chapterId: string, pageId: string): Promise<void> =>
    requestVoid(`/books/${bookId}/chapters/${chapterId}/pages/${pageId}`, {
      method: "DELETE",
    }),
  movePage: (
    bookId: string,
    chapterId: string,
    pageId: string,
    position: number,
    targetChapterId: string | null,
  ): Promise<Page> =>
    request(
      `/books/${bookId}/chapters/${chapterId}/pages/${pageId}/move`,
      pageSchema,
      {
        method: "POST",
        body: JSON.stringify({ position, target_chapter_id: targetChapterId }),
      },
    ),

  // --- Media ---
  uploadMedia: async (bookId: string, file: File): Promise<MediaRef> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`/api/books/${bookId}/media`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      let detail = res.statusText;
      let code = "error";
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
        code = body.code ?? code;
      } catch {
        /* kein JSON */
      }
      throw new ApiError(res.status, code, detail);
    }
    return mediaRefSchema.parse(await res.json());
  },
  mediaUrl: (bookId: string, mediaId: string): string =>
    `/api/books/${bookId}/media/${mediaId}`,

  // --- Export ---
  exportUrl: (bookId: string, format: "epub" | "pdf"): string =>
    `/api/books/${bookId}/export/${format}`,
};
