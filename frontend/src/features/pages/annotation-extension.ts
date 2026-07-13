import { Mark, mergeAttributes } from "@tiptap/core";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    annotation: {
      /** Markierten Text mit einer klickbaren Erklärung versehen. */
      setAnnotation: (note: string) => ReturnType;
      /** Erklärung von der aktuellen Markierung entfernen. */
      unsetAnnotation: () => ReturnType;
    };
  }
}

/**
 * Inline-Mark „annotation": trägt eine Erklärung (`note`) und rendert als
 * `<span class="annotation" data-note="…">`. Die Rendering-Schicht wandelt das
 * je nach Ziel in ein Popover (Vorschau), eine EPUB-Fußnote oder eine
 * PDF-Fußnote um.
 */
export const Annotation = Mark.create({
  name: "annotation",

  addAttributes() {
    return {
      note: {
        default: "",
        parseHTML: (el) => el.getAttribute("data-note") ?? "",
        renderHTML: (attrs) => (attrs.note ? { "data-note": attrs.note } : {}),
      },
    };
  },

  parseHTML() {
    return [{ tag: "span.annotation" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes({ class: "annotation" }, HTMLAttributes), 0];
  },

  addCommands() {
    return {
      setAnnotation:
        (note: string) =>
        ({ commands }) =>
          commands.setMark(this.name, { note }),
      unsetAnnotation:
        () =>
        ({ commands }) =>
          commands.unsetMark(this.name),
    };
  },
});
