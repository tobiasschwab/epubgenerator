import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryClient";
import type { MediaRef } from "@/lib/schemas";

export function usePageMutations(bookId: string) {
  const qc = useQueryClient();
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: queryKeys.book(bookId) });

  return {
    create: useMutation({
      mutationFn: (chapterId: string) => api.createPage(bookId, chapterId),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: (v: {
        chapterId: string;
        pageId: string;
        text: string;
        image: MediaRef | null;
        audio: MediaRef | null;
      }) =>
        api.updatePage(bookId, v.chapterId, v.pageId, {
          text: v.text,
          image: v.image,
          audio: v.audio,
        }),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (v: { chapterId: string; pageId: string }) =>
        api.deletePage(bookId, v.chapterId, v.pageId),
      onSuccess: invalidate,
    }),
    move: useMutation({
      mutationFn: (v: {
        chapterId: string;
        pageId: string;
        position: number;
        targetChapterId: string | null;
      }) =>
        api.movePage(bookId, v.chapterId, v.pageId, v.position, v.targetChapterId),
      onSuccess: invalidate,
    }),
    upload: useMutation({
      mutationFn: (file: File) => api.uploadMedia(bookId, file),
    }),
  };
}
