import { z } from "zod";

// Zod-Schemas spiegeln die API-Modelle (an Systemgrenzen validieren).

export const mediaKindSchema = z.enum(["image", "audio"]);

export const mediaRefSchema = z.object({
  id: z.string(),
  filename: z.string(),
  mime: z.string(),
  kind: mediaKindSchema,
});

export const pageSchema = z.object({
  id: z.string(),
  text: z.string(),
  // Geordnete, gemischte Medienliste (mehrere Bilder/Audio pro Seite).
  media: z.array(mediaRefSchema),
});

export const chapterSchema = z.object({
  id: z.string(),
  title: z.string(),
  pages: z.array(pageSchema),
});

export const bookSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  chapters: z.array(chapterSchema),
});

export const bookSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  chapter_count: z.number(),
});

export const bookSummaryListSchema = z.array(bookSummarySchema);

// --- KI-Drafts (Vorschau vor dem Speichern) ---
export const pageDraftSchema = z.object({
  text: z.string(),
  image_prompt: z.string(),
});

export const chapterDraftSchema = z.object({
  title: z.string(),
  pages: z.array(pageDraftSchema),
});

export const bookDraftSchema = z.object({
  title: z.string(),
  description: z.string(),
  chapters: z.array(chapterDraftSchema),
});

export const aiStatusSchema = z.object({ available: z.boolean() });

export type MediaKind = z.infer<typeof mediaKindSchema>;
export type MediaRef = z.infer<typeof mediaRefSchema>;
export type Page = z.infer<typeof pageSchema>;
export type Chapter = z.infer<typeof chapterSchema>;
export type Book = z.infer<typeof bookSchema>;
export type BookSummary = z.infer<typeof bookSummarySchema>;
export type PageDraft = z.infer<typeof pageDraftSchema>;
export type ChapterDraft = z.infer<typeof chapterDraftSchema>;
export type BookDraft = z.infer<typeof bookDraftSchema>;
