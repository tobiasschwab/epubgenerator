import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { SortableItem } from "@/components/SortableItem";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GenerateContentDialog } from "@/features/ai/GenerateContentDialog";
import { useAiStatus } from "@/features/ai/hooks";
import { queryKeys } from "@/lib/queryClient";
import { cn } from "@/lib/utils";
import type { Chapter } from "@/lib/schemas";

import { useChapterMutations } from "./hooks";

interface Props {
  bookId: string;
  chapters: Chapter[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  mutations: ReturnType<typeof useChapterMutations>;
}

export function ChapterList({ bookId, chapters, selectedId, onSelect, mutations }: Props) {
  const [newTitle, setNewTitle] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const aiStatus = useAiStatus();
  const qc = useQueryClient();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const target = chapters.findIndex((c) => c.id === over.id);
    if (target >= 0) {
      mutations.move.mutate({ chapterId: String(active.id), position: target });
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Kapitel</h2>
        {aiStatus.data?.available && (
          <GenerateContentDialog
            scope="chapter"
            bookId={bookId}
            onDone={() => qc.invalidateQueries({ queryKey: queryKeys.book(bookId) })}
          />
        )}
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
        <SortableContext
          items={chapters.map((c) => c.id)}
          strategy={verticalListSortingStrategy}
        >
          <ul className="space-y-1">
            {chapters.map((chapter) => (
              <SortableItem key={chapter.id} id={chapter.id}>
                {editingId === chapter.id ? (
                  <form
                    className="flex gap-1"
                    onSubmit={(e) => {
                      e.preventDefault();
                      mutations.update.mutate({ chapterId: chapter.id, title: editTitle });
                      setEditingId(null);
                    }}
                  >
                    <Input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="h-8"
                    />
                    <Button size="sm" type="submit">
                      OK
                    </Button>
                  </form>
                ) : (
                  <div
                    className={cn(
                      "flex items-center justify-between rounded-md px-2 py-1",
                      selectedId === chapter.id ? "bg-muted" : "hover:bg-muted/60",
                    )}
                  >
                    <button
                      className="min-w-0 flex-1 truncate text-left"
                      onClick={() => onSelect(chapter.id)}
                    >
                      {chapter.title || "Ohne Titel"}{" "}
                      <span className="text-xs text-muted-foreground">
                        ({chapter.pages.length})
                      </span>
                    </button>
                    <div className="flex shrink-0 gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEditingId(chapter.id);
                          setEditTitle(chapter.title);
                        }}
                      >
                        ✎
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm("Kapitel löschen?")) {
                            mutations.remove.mutate(chapter.id);
                          }
                        }}
                      >
                        🗑
                      </Button>
                    </div>
                  </div>
                )}
              </SortableItem>
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      <form
        className="flex gap-1"
        onSubmit={(e) => {
          e.preventDefault();
          const title = newTitle.trim() || "Neues Kapitel";
          mutations.create.mutate(title, { onSuccess: () => setNewTitle("") });
        }}
      >
        <Input
          placeholder="Neues Kapitel"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          className="h-8"
        />
        <Button size="sm" type="submit">
          +
        </Button>
      </form>
      <p className="text-xs text-muted-foreground">Buch-ID: {bookId.slice(0, 8)}…</p>
    </div>
  );
}
