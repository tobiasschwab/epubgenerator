import { z } from "zod";

import {
  aiStatusSchema,
  bookDraftSchema,
  explanationSchema,
  bookSchema,
  bookSummaryListSchema,
  chapterDraftSchema,
  chapterSchema,
  mediaRefSchema,
  modelsInfoSchema,
  pageDraftSchema,
  pageSchema,
  type Book,
  type BookDraft,
  type BookSummary,
  type Chapter,
  type ChapterDraft,
  type MediaRef,
  type ModelsInfo,
  type Page,
  type PageDraft,
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
    data: { text: string; media: MediaRef[] },
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
  deleteMedia: (bookId: string, mediaId: string): Promise<void> =>
    requestVoid(`/books/${bookId}/media/${mediaId}`, { method: "DELETE" }),

  // --- Export ---
  exportUrl: (bookId: string, format: "epub" | "pdf"): string =>
    `/api/books/${bookId}/export/${format}`,

  // --- KI (Google Gemini) ---
  ai: {
    status: (): Promise<{ available: boolean }> =>
      request("/ai/status", aiStatusSchema),
    models: (): Promise<ModelsInfo> => request("/ai/models", modelsInfoSchema),
    explain: (data: {
      text: string;
      language: string;
      model?: string | null;
    }): Promise<{ note: string }> =>
      request("/ai/explain", explanationSchema, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    generateBook: (data: {
      prompt: string;
      language: string;
      chapter_count?: number | null;
      pages_per_chapter?: number | null;
      model?: string | null;
    }): Promise<BookDraft> =>
      request("/ai/generate/book", bookDraftSchema, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    generateChapter: (data: {
      prompt: string;
      language: string;
      page_count?: number | null;
      model?: string | null;
    }): Promise<ChapterDraft> =>
      request("/ai/generate/chapter", chapterDraftSchema, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    generatePage: (data: {
      prompt: string;
      language: string;
      model?: string | null;
    }): Promise<PageDraft> =>
      request("/ai/generate/page", pageDraftSchema, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    commitBook: (draft: BookDraft): Promise<Book> =>
      request("/ai/books", bookSchema, {
        method: "POST",
        body: JSON.stringify(draft),
      }),
    commitChapter: (bookId: string, draft: ChapterDraft): Promise<Chapter> =>
      request(`/ai/books/${bookId}/chapters`, chapterSchema, {
        method: "POST",
        body: JSON.stringify(draft),
      }),
    commitPage: (bookId: string, chapterId: string, draft: PageDraft): Promise<Page> =>
      request(`/ai/books/${bookId}/chapters/${chapterId}/pages`, pageSchema, {
        method: "POST",
        body: JSON.stringify(draft),
      }),
    generateImage: (
      bookId: string,
      chapterId: string,
      pageId: string,
      prompt: string,
      model?: string | null,
    ): Promise<MediaRef> =>
      request(
        `/ai/books/${bookId}/chapters/${chapterId}/pages/${pageId}/image`,
        mediaRefSchema,
        { method: "POST", body: JSON.stringify({ prompt, model: model ?? null }) },
      ),
    generateAudio: (
      bookId: string,
      chapterId: string,
      pageId: string,
      voice?: string | null,
      model?: string | null,
    ): Promise<MediaRef> =>
      request(
        `/ai/books/${bookId}/chapters/${chapterId}/pages/${pageId}/audio`,
        mediaRefSchema,
        {
          method: "POST",
          body: JSON.stringify({ voice: voice ?? null, model: model ?? null }),
        },
      ),
  },
};
