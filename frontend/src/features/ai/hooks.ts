import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

/** Ob die KI serverseitig konfiguriert ist (API-Key gesetzt). */
export function useAiStatus() {
  return useQuery({
    queryKey: ["ai", "status"],
    queryFn: api.ai.status,
    staleTime: 60_000,
  });
}
