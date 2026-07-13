import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ChapterList } from "@/features/chapters/ChapterList";
import { useChapterMutations } from "@/features/chapters/hooks";
import { PageEditor } from "@/features/pages/PageEditor";
import { PageList } from "@/features/pages/PageList";
import { usePageMutations } from "@/features/pages/hooks";
import { PreviewPanel } from "@/features/preview/PreviewPanel";
import { ExportButtons } from "@/features/export/ExportButtons";

import { useBook, useUpdateBook } from "./hooks";

export function BookEditorPage() {
  const { bookId = "" } = useParams();
  const { data: book, isLoading, isError, dataUpdatedAt } = useBook(bookId);
  const updateBook = useUpdateBook(bookId);
  const chapterMutations = useChapterMutations(bookId);
  const pageMutations = usePageMutations(bookId);

  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [meta, setMeta] = useState({ title: "", description: "" });

  useEffect(() => {
    if (book) setMeta({ title: book.title, description: book.description });
  }, [book?.id]);

  // Gültige Auswahl sicherstellen, wenn sich der Baum ändert.
  const chapter = book?.chapters.find((c) => c.id === selectedChapterId) ?? book?.chapters[0];
  useEffect(() => {
    if (book && !book.chapters.some((c) => c.id === selectedChapterId)) {
      setSelectedChapterId(book.chapters[0]?.id ?? null);
    }
  }, [book, selectedChapterId]);

  const page =
    chapter?.pages.find((p) => p.id === selectedPageId) ?? chapter?.pages[0] ?? null;

  if (isLoading) return <div className="p-6 text-muted-foreground">Lädt…</div>;
  if (isError || !book)
    return <div className="p-6 text-destructive">Buch nicht gefunden.</div>;

  const metaDirty = meta.title !== book.title || meta.description !== book.description;

  return (
    <div className="mx-auto max-w-[1400px] space-y-4 p-4">
      <div className="flex items-center justify-between">
        <Link to="/" className="text-sm text-muted-foreground hover:underline">
          ← Alle Bücher
        </Link>
        <ExportButtons bookId={bookId} />
      </div>

      <Card className="p-4">
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (meta.title.trim()) updateBook.mutate({ ...meta, title: meta.title.trim() });
          }}
        >
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs font-medium text-muted-foreground">Titel</label>
            <Input
              value={meta.title}
              onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs font-medium text-muted-foreground">Beschreibung</label>
            <Textarea
              rows={1}
              value={meta.description}
              onChange={(e) => setMeta((m) => ({ ...m, description: e.target.value }))}
            />
          </div>
          <Button type="submit" disabled={!metaDirty || !meta.title.trim()}>
            Speichern
          </Button>
        </form>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[260px_260px_1fr]">
        <Card className="p-4">
          <ChapterList
            bookId={bookId}
            chapters={book.chapters}
            selectedId={chapter?.id ?? null}
            onSelect={(id) => {
              setSelectedChapterId(id);
              setSelectedPageId(null);
            }}
            mutations={chapterMutations}
          />
        </Card>

        <Card className="p-4">
          {chapter ? (
            <PageList
              bookId={bookId}
              chapter={chapter}
              selectedPageId={page?.id ?? null}
              onSelect={setSelectedPageId}
              mutations={pageMutations}
            />
          ) : (
            <p className="text-sm text-muted-foreground">Kapitel auswählen.</p>
          )}
        </Card>

        <div className="space-y-4">
          {chapter && page ? (
            <PageEditor
              bookId={bookId}
              chapter={chapter}
              page={page}
              mutations={pageMutations}
            />
          ) : (
            <Card className="p-4 text-sm text-muted-foreground">
              Seite auswählen oder anlegen.
            </Card>
          )}
          <Card className="p-4">
            <PreviewPanel
              bookId={bookId}
              chapterId={chapter?.id}
              refreshKey={dataUpdatedAt}
            />
          </Card>
        </div>
      </div>
    </div>
  );
}
