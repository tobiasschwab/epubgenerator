import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

/** Ob die KI serverseitig konfiguriert ist (API-Key gesetzt). */
export function useAiStatus() {
  return useQuery({
    queryKey: ["ai", "status"],
    queryFn: api.ai.status,
    staleTime: 60_000,
  });
}

/** Wählbare Modelle je Funktion (Text/Bild/Audio) inkl. Defaults. */
export function useAiModels() {
  return useQuery({
    queryKey: ["ai", "models"],
    queryFn: api.ai.models,
    staleTime: 300_000,
  });
}

/**
 * Modell-/Stimmen-Auswahl, die die letzte explizite Wahl in localStorage merkt.
 * Solange nichts gespeichert ist, übernimmt sie den Server-Default, sobald er
 * geladen ist (ohne den Default selbst zu persistieren).
 */
export function useModelPreference(key: string, serverDefault: string | undefined) {
  const storageKey = `epub.ai.${key}`;
  const [value, setValue] = useState<string>(
    () => localStorage.getItem(storageKey) ?? "",
  );
  useEffect(() => {
    if (!value && serverDefault) setValue(serverDefault);
  }, [serverDefault, value]);

  const update = useCallback(
    (next: string) => {
      setValue(next);
      localStorage.setItem(storageKey, next);
    },
    [storageKey],
  );
  return [value, update] as const;
}
