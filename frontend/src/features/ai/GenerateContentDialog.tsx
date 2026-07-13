import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Chapter, ChapterDraft, Page, PageDraft } from "@/lib/schemas";

import { ErrorLine } from "./GenerateBookDialog";

function excerpt(html: string): string {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

type Props =
  | { scope: "chapter"; bookId: string; onDone: () => void }
  | { scope: "page"; bookId: string; chapterId: string; onDone: () => void };

/** KI-Generierung für ein einzelnes Kapitel bzw. eine einzelne Seite. */
export function GenerateContentDialog(props: Props) {
  const { scope, bookId, onDone } = props;
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("Deutsch");
  const [pageCount, setPageCount] = useState(3);
  const [draft, setDraft] = useState<ChapterDraft | PageDraft | null>(null);

  const reset = () => {
    setDraft(null);
    setPrompt("");
  };

  const generate = useMutation({
    mutationFn: (): Promise<ChapterDraft | PageDraft> =>
      scope === "chapter"
        ? api.ai.generateChapter({ prompt, language, page_count: pageCount })
        : api.ai.generatePage({ prompt, language }),
    onSuccess: setDraft,
  });

  const commit = useMutation({
    mutationFn: (d: ChapterDraft | PageDraft): Promise<Chapter | Page> =>
      scope === "chapter"
        ? api.ai.commitChapter(bookId, d as ChapterDraft)
        : api.ai.commitPage(bookId, props.chapterId, d as PageDraft),
    onSuccess: () => {
      setOpen(false);
      reset();
      onDone();
    },
  });

  const error = generate.error ?? commit.error;
  const label = scope === "chapter" ? "Kapitel" : "Seite";

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="secondary">
          <Sparkles /> KI
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{label} mit KI erstellen</DialogTitle>
        </DialogHeader>

        {!draft ? (
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Thema / Anweisung</Label>
              <Textarea
                rows={4}
                placeholder={`Worum soll ${scope === "chapter" ? "das Kapitel" : "die Seite"} gehen?`}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Sprache</Label>
                <Input value={language} onChange={(e) => setLanguage(e.target.value)} />
              </div>
              {scope === "chapter" && (
                <div className="space-y-1">
                  <Label>Seiten</Label>
                  <Input
                    type="number"
                    min={1}
                    max={50}
                    value={pageCount}
                    onChange={(e) => setPageCount(Number(e.target.value))}
                  />
                </div>
              )}
            </div>
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
            {"title" in draft && (
              <h3 className="text-lg font-semibold">{draft.title || "Ohne Titel"}</h3>
            )}
            <div className="max-h-64 space-y-2 overflow-y-auto rounded-md border p-2 text-sm">
              {("pages" in draft ? draft.pages : [draft]).map((p, i) => (
                <p key={i} className="border-b pb-2 last:border-0">
                  <span className="text-muted-foreground">{i + 1}. </span>
                  {excerpt(p.text) || "(leer)"}
                </p>
              ))}
            </div>
            {error && <ErrorLine error={error} />}
            <div className="flex justify-between">
              <Button variant="ghost" onClick={reset} disabled={commit.isPending}>
                Neu generieren
              </Button>
              <Button onClick={() => commit.mutate(draft)} disabled={commit.isPending}>
                {commit.isPending ? "Speichere…" : `${label} übernehmen`}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
