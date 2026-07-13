import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Chapter, MediaRef, Page } from "@/lib/schemas";

import { usePageMutations } from "./hooks";
import { RichTextEditor } from "./RichTextEditor";

interface Props {
  bookId: string;
  chapter: Chapter;
  page: Page;
  mutations: ReturnType<typeof usePageMutations>;
}

export function PageEditor({ bookId, chapter, page, mutations }: Props) {
  const [text, setText] = useState(page.text);
  const [error, setError] = useState<string | null>(null);
  const imageInput = useRef<HTMLInputElement>(null);
  const audioInput = useRef<HTMLInputElement>(null);

  // Bei Seitenwechsel lokalen Textzustand zurücksetzen.
  useEffect(() => setText(page.text), [page.id, page.text]);

  const dirty = text !== page.text;

  const save = (overrides?: { image?: MediaRef | null; audio?: MediaRef | null }) =>
    mutations.update.mutate({
      chapterId: chapter.id,
      pageId: page.id,
      text,
      image: overrides?.image !== undefined ? overrides.image : page.image ?? null,
      audio: overrides?.audio !== undefined ? overrides.audio : page.audio ?? null,
    });

  const handleUpload = async (
    file: File | undefined,
    kind: "image" | "audio",
  ) => {
    if (!file) return;
    setError(null);
    try {
      const ref = await mutations.upload.mutateAsync(file);
      if (ref.kind !== kind) {
        setError(`Erwartet ${kind}, erhalten ${ref.kind}.`);
        return;
      }
      save(kind === "image" ? { image: ref } : { audio: ref });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    }
  };

  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Seite bearbeiten</h3>
        <Button size="sm" disabled={!dirty || mutations.update.isPending} onClick={() => save()}>
          {mutations.update.isPending ? "Speichern…" : dirty ? "Speichern" : "Gespeichert"}
        </Button>
      </div>

      <RichTextEditor value={text} onChange={setText} />

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        <MediaSlot
          label="Bild"
          accept="image/*"
          inputRef={imageInput}
          onSelect={(f) => handleUpload(f, "image")}
          current={page.image ?? null}
          preview={
            page.image ? (
              <img
                src={api.mediaUrl(bookId, page.image.id)}
                alt={page.image.filename}
                className="max-h-40 rounded border border-border"
              />
            ) : null
          }
          onRemove={() => save({ image: null })}
        />
        <MediaSlot
          label="Audio"
          accept="audio/*"
          inputRef={audioInput}
          onSelect={(f) => handleUpload(f, "audio")}
          current={page.audio ?? null}
          preview={
            page.audio ? (
              <audio
                controls
                src={api.mediaUrl(bookId, page.audio.id)}
                className="w-full"
              />
            ) : null
          }
          onRemove={() => save({ audio: null })}
        />
      </div>
    </Card>
  );
}

function MediaSlot({
  label,
  accept,
  inputRef,
  onSelect,
  current,
  preview,
  onRemove,
}: {
  label: string;
  accept: string;
  inputRef: React.RefObject<HTMLInputElement>;
  onSelect: (file: File | undefined) => void;
  current: MediaRef | null;
  preview: React.ReactNode;
  onRemove: () => void;
}) {
  return (
    <div className="space-y-2 rounded-md border border-border p-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => inputRef.current?.click()}>
            {current ? "Ersetzen" : "Hochladen"}
          </Button>
          {current && (
            <Button size="sm" variant="ghost" onClick={onRemove}>
              Entfernen
            </Button>
          )}
        </div>
      </div>
      {preview}
      {current && <p className="text-xs text-muted-foreground">{current.filename}</p>}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          onSelect(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}
