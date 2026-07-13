import { describe, expect, it } from "vitest";

import { bookSchema, bookSummaryListSchema, pageSchema } from "./schemas";

describe("schemas", () => {
  it("validiert ein vollständiges Buch mit gemischten Medien", () => {
    const book = bookSchema.parse({
      id: "b1",
      title: "T",
      description: "d",
      chapters: [
        {
          id: "c1",
          title: "K",
          pages: [
            {
              id: "p1",
              text: "<p>x</p>",
              media: [
                { id: "m1", filename: "a.png", mime: "image/png", kind: "image" },
                { id: "m2", filename: "a.mp3", mime: "audio/mpeg", kind: "audio" },
              ],
            },
          ],
        },
      ],
    });
    expect(book.chapters[0].pages[0].media).toHaveLength(2);
  });

  it("akzeptiert eine leere Medienliste", () => {
    const page = pageSchema.parse({ id: "p", text: "", media: [] });
    expect(page.media).toEqual([]);
  });

  it("validiert die Bücherliste", () => {
    const list = bookSummaryListSchema.parse([
      { id: "b", title: "t", description: "", chapter_count: 2 },
    ]);
    expect(list[0].chapter_count).toBe(2);
  });

  it("weist ungültige MediaKind ab", () => {
    expect(() =>
      pageSchema.parse({
        id: "p",
        text: "",
        media: [{ id: "m", filename: "f", mime: "x", kind: "video" }],
      }),
    ).toThrow();
  });
});
