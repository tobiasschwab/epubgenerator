import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError } from "@/lib/api";
import type { Book, BookDraft } from "@/lib/schemas";

import { useAiModels, useModelPreference } from "./hooks";
import { ModelSelect } from "./ModelSelect";

export function GenerateBookDialog({
  disabled,
  onCreated,
}: {
  disabled?: boolean;
  onCreated: (book: Book) => void;
}) {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("Deutsch");
  const [chapterCount, setChapterCount] = useState(3);
  const [pagesPerChapter, setPagesPerChapter] = useState(3);
  const [draft, setDraft] = useState<BookDraft | null>(null);
  const models = useAiModels();
  const [model, setModel] = useModelPreference("text", models.data?.text.default);

  const reset = () => {
    setDraft(null);
    setPrompt("");
  };

  const generate = useMutation({
    mutationFn: () =>
      api.ai.generateBook({
        prompt,
        language,
        chapter_count: chapterCount,
        pages_per_chapter: pagesPerChapter,
        model: model || undefined,
      }),
    onSuccess: setDraft,
  });

  const commit = useMutation({
    mutationFn: (d: BookDraft) => api.ai.commitBook(d),
    onSuccess: (book) => {
      setOpen(false);
      reset();
      onCreated(book);
    },
  });

  const error = generate.error ?? commit.error;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button variant="secondary" disabled={disabled}>
          <Sparkles /> Mit KI erstellen
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Buch mit KI erstellen</DialogTitle>
          <DialogDescription>
            Beschreibe das Buch — die KI legt Titel, Kapitel und Seiten an.
          </DialogDescription>
        </DialogHeader>

        {!draft ? (
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Beschreibung / Thema</Label>
              <Textarea
                rows={4}
                placeholder="z. B. Ein Kinderbuch über einen neugierigen Fuchs, der die Jahreszeiten entdeckt."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label>Sprache</Label>
                <Input value={language} onChange={(e) => setLanguage(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Kapitel</Label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={chapterCount}
                  onChange={(e) => setChapterCount(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label>Seiten/Kapitel</Label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={pagesPerChapter}
                  onChange={(e) => setPagesPerChapter(Number(e.target.value))}
                />
              </div>
            </div>
            {models.data && (
              <ModelSelect
                label="Textmodell"
                group={models.data.text}
                value={model}
                onChange={setModel}
              />
            )}
            {error && <ErrorLine error={error} />}
            <div className="flex justify-end">
              <Button
                disabled={!prompt.trim() || generate.isPending}
                onClick={() => generate.mutate()}
              >
                {generate.isPending ? "Generiere…" : "Vorschau generieren"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <h3 className="text-lg font-semibold">{draft.title || "Ohne Titel"}</h3>
              {draft.description && (
                <p className="text-sm text-muted-foreground">{draft.description}</p>
              )}
            </div>
            <ul className="space-y-2">
              {draft.chapters.map((c, i) => (
                <li key={i} className="rounded-md border p-2">
                  <p className="font-medium">
                    {i + 1}. {c.title || "Ohne Titel"}{" "}
                    <span className="text-xs text-muted-foreground">
                      ({c.pages.length} Seiten)
                    </span>
                  </p>
                </li>
              ))}
            </ul>
            {error && <ErrorLine error={error} />}
            <div className="flex justify-between">
              <Button variant="ghost" onClick={reset} disabled={commit.isPending}>
                Neu generieren
              </Button>
              <Button onClick={() => commit.mutate(draft)} disabled={commit.isPending}>
                {commit.isPending ? "Speichere…" : "Buch erstellen"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export function ErrorLine({ error }: { error: unknown }) {
  const message =
    error instanceof ApiError && error.status === 503
      ? "KI ist nicht konfiguriert (kein API-Key auf dem Server)."
      : error instanceof Error
        ? error.message
        : "Unbekannter Fehler";
  return <p className="text-sm text-destructive">{message}</p>;
}
