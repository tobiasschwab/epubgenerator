import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";

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

/**
 * Rendert die Server-Vorschau (identische Pipeline wie der Export) isoliert
 * in einem iframe (Style-Isolation).
 */
export function PreviewPanel({ bookId, chapterId, refreshKey }: Props) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["preview", bookId, chapterId ?? "all", refreshKey],
    queryFn: () => fetchPreview(bookId, chapterId),
  });

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Vorschau</h3>
        <Button size="sm" variant="secondary" onClick={() => refetch()}>
          Aktualisieren
        </Button>
      </div>
      {isLoading && <p className="text-muted-foreground">Lädt…</p>}
      {isError && <p className="text-destructive">Vorschau nicht verfügbar.</p>}
      {data && (
        <iframe
          title="Vorschau"
          srcDoc={data}
          className="h-[70vh] w-full rounded-md border border-border bg-white"
        />
      )}
    </div>
  );
}
