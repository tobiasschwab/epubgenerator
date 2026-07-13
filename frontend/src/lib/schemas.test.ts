import { describe, expect, it } from "vitest";

import { bookSchema, bookSummaryListSchema, pageSchema } from "./schemas";

describe("schemas", () => {
  it("validiert ein vollständiges Buch", () => {
    const book = bookSchema.parse({
      id: "b1",
      title: "T",
      description: "d",
      chapters: [
        {
          id: "c1",
          title: "K",
          pages: [{ id: "p1", text: "<p>x</p>", image: null, audio: null }],
        },
      ],
    });
    expect(book.chapters[0].pages[0].id).toBe("p1");
  });

  it("erlaubt fehlende Medienfelder", () => {
    const page = pageSchema.parse({ id: "p", text: "" });
    expect(page.image).toBeUndefined();
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
        image: { id: "m", filename: "f", mime: "x", kind: "video" },
      }),
    ).toThrow();
  });
});
