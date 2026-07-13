import ePub, { type Rendition } from "epubjs";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface Props {
  bookId: string;
  refreshKey: number;
}

/**
 * Rendert das exportierte EPUB mit epub.js als echten E-Reader
 * (paginierte Ansicht wie in einem E-Reader-Programm).
 */
export function EpubReader({ bookId, refreshKey }: Props) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    const container = viewerRef.current;
    if (!container) return;

    setStatus("loading");
    container.innerHTML = "";

    (async () => {
      try {
        const res = await fetch(api.exportUrl(bookId, "epub"), { method: "POST" });
        if (!res.ok) throw new Error("EPUB-Export fehlgeschlagen");
        const buffer = await res.arrayBuffer();
        if (cancelled) return;

        const book = ePub(buffer);
        const rendition = book.renderTo(container, {
          width: "100%",
          height: "100%",
          spread: "none",
        });
        renditionRef.current = rendition;
        await rendition.display();
        if (!cancelled) setStatus("ready");
      } catch {
        if (!cancelled) setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      renditionRef.current?.destroy();
      renditionRef.current = null;
    };
  }, [bookId, refreshKey]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => renditionRef.current?.prev()}
          disabled={status !== "ready"}
        >
          <ChevronLeft /> Zurück
        </Button>
        <span className="text-xs text-muted-foreground">
          {status === "loading" && "EPUB wird erzeugt…"}
          {status === "error" && "E-Reader-Vorschau nicht verfügbar"}
          {status === "ready" && "epub.js"}
        </span>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => renditionRef.current?.next()}
          disabled={status !== "ready"}
        >
          Weiter <ChevronRight />
        </Button>
      </div>
      <div
        ref={viewerRef}
        className="h-[70vh] w-full rounded-md border bg-white"
      />
    </div>
  );
}
