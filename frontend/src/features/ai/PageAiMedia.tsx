import { useMutation } from "@tanstack/react-query";
import { AudioLines, ImagePlus } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { Chapter, MediaRef, Page } from "@/lib/schemas";

import { ErrorLine } from "./GenerateBookDialog";

function plainText(html: string): string {
  return html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

interface Props {
  bookId: string;
  chapter: Chapter;
  page: Page;
  disabled?: boolean;
  onAttach: (ref: MediaRef) => void;
}

/** KI-Buttons an einer Seite: Bild (Prompt vorbelegt) und Audio (aus Seitentext). */
export function PageAiMedia({ bookId, chapter, page, disabled, onAttach }: Props) {
  return (
    <div className="flex gap-2">
      <ImageGenDialog
        bookId={bookId}
        chapter={chapter}
        page={page}
        disabled={disabled}
        onAttach={onAttach}
      />
      <AudioGenDialog
        bookId={bookId}
        chapter={chapter}
        page={page}
        disabled={disabled}
        onAttach={onAttach}
      />
    </div>
  );
}

function ImageGenDialog({ bookId, chapter, page, disabled, onAttach }: Props) {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [ref, setRef] = useState<MediaRef | null>(null);

  const generate = useMutation({
    mutationFn: () => api.ai.generateImage(bookId, chapter.id, page.id, prompt),
    onSuccess: setRef,
  });

  const discard = () => {
    if (ref) void api.deleteMedia(bookId, ref.id);
    setRef(null);
  };

  const handleOpen = (o: boolean) => {
    if (o) setPrompt(plainText(page.text)); // Seitentext vorbelegen
    else discard();
    setOpen(o);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="secondary" disabled={disabled}>
          <ImagePlus /> Bild (KI)
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Bild mit KI generieren</DialogTitle>
          <DialogDescription>
            Der Seitentext ist als Bildbeschreibung vorbelegt — anpassbar.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label>Bildbeschreibung</Label>
            <Textarea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>
          {ref && (
            <img
              src={api.mediaUrl(bookId, ref.id)}
              alt="KI-Bild"
              className="max-h-64 w-full rounded-md border object-contain"
            />
          )}
          {generate.error && <ErrorLine error={generate.error} />}
          <div className="flex justify-between">
            <Button
              variant="secondary"
              disabled={!prompt.trim() || generate.isPending}
              onClick={() => generate.mutate()}
            >
              {generate.isPending ? "Generiere…" : ref ? "Neu generieren" : "Generieren"}
            </Button>
            <Button
              disabled={!ref}
              onClick={() => {
                if (ref) onAttach(ref);
                setRef(null);
                setOpen(false);
              }}
            >
              Übernehmen
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AudioGenDialog({ bookId, chapter, page, disabled, onAttach }: Props) {
  const [open, setOpen] = useState(false);
  const [ref, setRef] = useState<MediaRef | null>(null);

  const generate = useMutation({
    mutationFn: () => api.ai.generateAudio(bookId, chapter.id, page.id),
    onSuccess: setRef,
  });

  const discard = () => {
    if (ref) void api.deleteMedia(bookId, ref.id);
    setRef(null);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) discard();
        setOpen(o);
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="secondary" disabled={disabled}>
          <AudioLines /> Audio (KI)
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Audio mit KI generieren</DialogTitle>
          <DialogDescription>
            Sprachausgabe (TTS) aus dem aktuellen Seitentext.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {ref && (
            <audio controls src={api.mediaUrl(bookId, ref.id)} className="w-full" />
          )}
          {generate.error && <ErrorLine error={generate.error} />}
          <div className="flex justify-between">
            <Button
              variant="secondary"
              disabled={generate.isPending || !plainText(page.text)}
              onClick={() => generate.mutate()}
            >
              {generate.isPending ? "Generiere…" : ref ? "Neu generieren" : "Generieren"}
            </Button>
            <Button
              disabled={!ref}
              onClick={() => {
                if (ref) onAttach(ref);
                setRef(null);
                setOpen(false);
              }}
            >
              Übernehmen
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
