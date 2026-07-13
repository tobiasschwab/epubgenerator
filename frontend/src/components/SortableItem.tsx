import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface Props {
  id: string;
  children: ReactNode;
  className?: string;
}

/** Ein per dnd-kit sortierbares Element mit dediziertem Drag-Handle (⠿). */
export function SortableItem({ id, children, className }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        "flex items-center gap-2",
        isDragging && "opacity-60",
        className,
      )}
    >
      <button
        type="button"
        className="cursor-grab select-none px-1 text-muted-foreground"
        aria-label="Verschieben"
        {...attributes}
        {...listeners}
      >
        ⠿
      </button>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
