import {
  closestCenter,
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { arrayMove, SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { ImagePlus, Music } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { SortableItem } from "@/components/SortableItem";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  const [media, setMedia] = useState<MediaRef[]>(page.media);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // Bei Seitenwechsel lokalen Zustand zurücksetzen.
  useEffect(() => {
    setText(page.text);
    setMedia(page.media);
  }, [page.id]);

  const sensors = useSensors(useSensor(PointerSensor));
  const textDirty = text !== page.text;

  const persist = (nextText: string, nextMedia: MediaRef[]) =>
    mutations.update.mutate({
      chapterId: chapter.id,
      pageId: page.id,
      text: nextText,
      media: nextMedia,
    });

  const setAndPersistMedia = (nextMedia: MediaRef[]) => {
    setMedia(nextMedia);
    persist(text, nextMedia);
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);
    try {
      const uploaded = await Promise.all(
        Array.from(files).map((file) => mutations.upload.mutateAsync(file)),
      );
      setAndPersistMedia([...media, ...uploaded]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    }
  };

  const removeMedia = (id: string) =>
    setAndPersistMedia(media.filter((m) => m.id !== id));

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const from = media.findIndex((m) => m.id === active.id);
    const to = media.findIndex((m) => m.id === over.id);
    if (from >= 0 && to >= 0) setAndPersistMedia(arrayMove(media, from, to));
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Seite bearbeiten</CardTitle>
        <Button
          size="sm"
          disabled={!textDirty || mutations.update.isPending}
          onClick={() => persist(text, media)}
        >
          {mutations.update.isPending
            ? "Speichern…"
            : textDirty
              ? "Text speichern"
              : "Gespeichert"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <RichTextEditor value={text} onChange={setText} />

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              Medien{" "}
              <span className="text-muted-foreground">({media.length})</span>
            </span>
            <Button
              size="sm"
              variant="secondary"
              disabled={mutations.upload.isPending}
              onClick={() => fileInput.current?.click()}
            >
              <ImagePlus /> Medien hinzufügen
            </Button>
            <input
              ref={fileInput}
              type="file"
              accept="image/*,audio/*"
              multiple
              className="hidden"
              onChange={(e) => {
                void handleFiles(e.target.files);
                e.target.value = "";
              }}
            />
          </div>

          {media.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Noch keine Medien. Bilder und Audio lassen sich mischen und per
              Ziehen sortieren.
            </p>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={onDragEnd}
            >
              <SortableContext
                items={media.map((m) => m.id)}
                strategy={verticalListSortingStrategy}
              >
                <ul className="space-y-2">
                  {media.map((ref) => (
                    <SortableItem key={ref.id} id={ref.id}>
                      <MediaCard
                        bookId={bookId}
                        media={ref}
                        onRemove={() => removeMedia(ref.id)}
                      />
                    </SortableItem>
                  ))}
                </ul>
              </SortableContext>
            </DndContext>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function MediaCard({
  bookId,
  media,
  onRemove,
}: {
  bookId: string;
  media: MediaRef;
  onRemove: () => void;
}) {
  const url = api.mediaUrl(bookId, media.id);
  return (
    <div className="flex items-center gap-3 rounded-md border p-2">
      <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded bg-muted">
        {media.kind === "image" ? (
          <img src={url} alt={media.filename} className="h-full w-full object-cover" />
        ) : (
          <Music className="h-6 w-6 text-muted-foreground" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{media.filename}</p>
        <p className="text-xs text-muted-foreground">{media.kind}</p>
        {media.kind === "audio" && (
          <audio controls src={url} className="mt-1 h-8 w-full" />
        )}
      </div>
      <Button size="sm" variant="ghost" onClick={onRemove}>
        Entfernen
      </Button>
    </div>
  );
}
