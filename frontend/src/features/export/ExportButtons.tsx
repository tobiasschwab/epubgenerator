import { useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

async function downloadExport(bookId: string, format: "epub" | "pdf") {
  const res = await fetch(api.exportUrl(bookId, format), { method: "POST" });
  if (!res.ok) throw new Error(`${format.toUpperCase()}-Export fehlgeschlagen`);
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename = match?.[1] ?? `book.${format}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExportButtons({ bookId }: { bookId: string }) {
  const [busy, setBusy] = useState<"epub" | "pdf" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (format: "epub" | "pdf") => {
    setBusy(format);
    setError(null);
    try {
      await downloadExport(bookId, format);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Button size="sm" onClick={() => run("epub")} disabled={busy !== null}>
          {busy === "epub" ? "EPUB…" : "EPUB exportieren"}
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => run("pdf")}
          disabled={busy !== null}
        >
          {busy === "pdf" ? "PDF…" : "PDF exportieren"}
        </Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
