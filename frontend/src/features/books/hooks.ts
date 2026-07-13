import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/queryClient";

export function useBooks() {
  return useQuery({ queryKey: queryKeys.books, queryFn: api.listBooks });
}

export function useBook(id: string) {
  return useQuery({ queryKey: queryKeys.book(id), queryFn: () => api.getBook(id) });
}

export function useCreateBook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; description: string }) => api.createBook(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.books }),
  });
}

export function useUpdateBook(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; description: string }) =>
      api.updateBook(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.book(id) });
      qc.invalidateQueries({ queryKey: queryKeys.books });
    },
  });
}

export function useDeleteBook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteBook(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.books }),
  });
}
