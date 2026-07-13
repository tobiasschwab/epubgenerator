import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryClient";

export function useChapterMutations(bookId: string) {
  const qc = useQueryClient();
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: queryKeys.book(bookId) });

  return {
    create: useMutation({
      mutationFn: (title: string) => api.createChapter(bookId, title),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: (v: { chapterId: string; title: string }) =>
        api.updateChapter(bookId, v.chapterId, v.title),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (chapterId: string) => api.deleteChapter(bookId, chapterId),
      onSuccess: invalidate,
    }),
    move: useMutation({
      mutationFn: (v: { chapterId: string; position: number }) =>
        api.moveChapter(bookId, v.chapterId, v.position),
      onSuccess: invalidate,
    }),
  };
}
