import {
  closestCenter,
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";

import { useQueryClient } from "@tanstack/react-query";

import { SortableItem } from "@/components/SortableItem";
import { Button } from "@/components/ui/button";
import { GenerateContentDialog } from "@/features/ai/GenerateContentDialog";
import { useAiStatus } from "@/features/ai/hooks";
import { queryKeys } from "@/lib/queryClient";
import { cn } from "@/lib/utils";
import type { Chapter } from "@/lib/schemas";

import { usePageMutations } from "./hooks";

interface Props {
  bookId: string;
  chapter: Chapter;
  selectedPageId: string | null;
  onSelect: (id: string) => void;
  mutations: ReturnType<typeof usePageMutations>;
}

/** Kurzer Textauszug (HTML entfernt) für die Seiten-Liste. */
function excerpt(html: string): string {
  const text = html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  return text.slice(0, 40) || "(leer)";
}

export function PageList({ bookId, chapter, selectedPageId, onSelect, mutations }: Props) {
  const sensors = useSensors(useSensor(PointerSensor));
  const aiStatus = useAiStatus();
  const qc = useQueryClient();

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const target = chapter.pages.findIndex((p) => p.id === over.id);
    if (target >= 0) {
      mutations.move.mutate({
        chapterId: chapter.id,
        pageId: String(active.id),
        position: target,
        targetChapterId: null,
      });
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Seiten</h3>
        <div className="flex gap-2">
          {aiStatus.data?.available && (
            <GenerateContentDialog
              scope="page"
              bookId={bookId}
              chapterId={chapter.id}
              onDone={() => qc.invalidateQueries({ queryKey: queryKeys.book(bookId) })}
            />
          )}
          <Button
            size="sm"
            onClick={() =>
              mutations.create.mutate(chapter.id, {
                onSuccess: (page) => onSelect(page.id),
              })
            }
          >
            + Seite
          </Button>
        </div>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
        <SortableContext
          items={chapter.pages.map((p) => p.id)}
          strategy={verticalListSortingStrategy}
        >
          <ul className="space-y-1">
            {chapter.pages.map((page, index) => (
              <SortableItem key={page.id} id={page.id}>
                <div
                  className={cn(
                    "flex items-center justify-between rounded-md px-2 py-1",
                    selectedPageId === page.id ? "bg-muted" : "hover:bg-muted/60",
                  )}
                >
                  <button
                    className="min-w-0 flex-1 truncate text-left text-sm"
                    onClick={() => onSelect(page.id)}
                  >
                    <span className="text-muted-foreground">{index + 1}.</span>{" "}
                    {excerpt(page.text)}
                    {page.media.some((m) => m.kind === "image") && " 🖼"}
                    {page.media.some((m) => m.kind === "audio") && " 🔊"}
                  </button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm("Seite löschen?")) {
                        mutations.remove.mutate({ chapterId: chapter.id, pageId: page.id });
                      }
                    }}
                  >
                    🗑
                  </Button>
                </div>
              </SortableItem>
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      {chapter.pages.length === 0 && (
        <p className="text-sm text-muted-foreground">Noch keine Seiten.</p>
      )}
    </div>
  );
}
