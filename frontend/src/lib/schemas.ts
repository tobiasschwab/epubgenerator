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
  image: mediaRefSchema.nullable().optional(),
  audio: mediaRefSchema.nullable().optional(),
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

export type MediaKind = z.infer<typeof mediaKindSchema>;
export type MediaRef = z.infer<typeof mediaRefSchema>;
export type Page = z.infer<typeof pageSchema>;
export type Chapter = z.infer<typeof chapterSchema>;
export type Book = z.infer<typeof bookSchema>;
export type BookSummary = z.infer<typeof bookSummarySchema>;
