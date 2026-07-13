import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// epub.js ist schwer und nur im E-Reader-Modus nötig → separat nachladen.
const EpubReader = lazy(() =>
  import("./EpubReader").then((m) => ({ default: m.EpubReader })),
);

async function fetchPreview(bookId: string, chapterId?: string): Promise<string> {
  const qs = chapterId ? `?chapterId=${chapterId}` : "";
  const res = await fetch(`/api/books/${bookId}/preview${qs}`);
  if (!res.ok) throw new Error("Vorschau fehlgeschlagen");
  return res.text();
}

interface Props {
  bookId: string;
  chapterId?: string;
  refreshKey: number;
}

type Mode = "html" | "reader";

/**
 * Zwei Vorschau-Modi:
 *  - „HTML": Server-Vorschau (identische Pipeline wie der Export), iframe-isoliert.
 *  - „E-Reader": das exportierte EPUB via epub.js, paginiert wie im E-Reader.
 */
export function PreviewPanel({ bookId, chapterId, refreshKey }: Props) {
  const [mode, setMode] = useState<Mode>("html");

  const html = useQuery({
    queryKey: ["preview", bookId, chapterId ?? "all", refreshKey],
    queryFn: () => fetchPreview(bookId, chapterId),
    enabled: mode === "html",
  });

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="inline-flex rounded-md border p-0.5">
          <ModeButton active={mode === "html"} onClick={() => setMode("html")}>
            HTML
          </ModeButton>
          <ModeButton active={mode === "reader"} onClick={() => setMode("reader")}>
            E-Reader
          </ModeButton>
        </div>
        {mode === "html" && (
          <Button size="sm" variant="secondary" onClick={() => html.refetch()}>
            Aktualisieren
          </Button>
        )}
      </div>

      {mode === "html" ? (
        <>
          {html.isLoading && <p className="text-muted-foreground">Lädt…</p>}
          {html.isError && <p className="text-destructive">Vorschau nicht verfügbar.</p>}
          {html.data && (
            <iframe
              title="Vorschau"
              srcDoc={html.data}
              className="h-[70vh] w-full rounded-md border bg-white"
            />
          )}
        </>
      ) : (
        <Suspense
          fallback={<p className="text-muted-foreground">E-Reader wird geladen…</p>}
        >
          <EpubReader bookId={bookId} refreshKey={refreshKey} />
        </Suspense>
      )}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded px-3 py-1 text-sm transition-colors",
        active ? "bg-primary text-primary-foreground" : "hover:bg-muted",
      )}
    >
      {children}
    </button>
  );
}
