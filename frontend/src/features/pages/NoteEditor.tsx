import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  value: string;
  onChange: (html: string) => void;
}

/** Kompakter Rich-Text-Editor für Erklärungen (fett, kursiv, Listen). */
export function NoteEditor({ value, onChange }: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        codeBlock: false,
        blockquote: false,
        horizontalRule: false,
      }),
    ],
    content: value,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
    editorProps: { attributes: { class: "note-editor" } },
  });

  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value || "", false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editor]);

  if (!editor) return null;

  const btn = (active: boolean, onClick: () => void, label: React.ReactNode) => (
    <Button
      type="button"
      size="sm"
      variant="secondary"
      className={cn("h-7 px-2", active && "bg-primary text-primary-foreground")}
      onClick={onClick}
    >
      {label}
    </Button>
  );

  return (
    <div className="space-y-1">
      <div className="flex flex-wrap gap-1">
        {btn(editor.isActive("bold"), () => editor.chain().focus().toggleBold().run(), <b>B</b>)}
        {btn(editor.isActive("italic"), () => editor.chain().focus().toggleItalic().run(), <i>I</i>)}
        {btn(
          editor.isActive("bulletList"),
          () => editor.chain().focus().toggleBulletList().run(),
          "• Liste",
        )}
        {btn(
          editor.isActive("orderedList"),
          () => editor.chain().focus().toggleOrderedList().run(),
          "1. Liste",
        )}
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
