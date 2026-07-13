import Image from "@tiptap/extension-image";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { MessageSquarePlus } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { Annotation } from "./annotation-extension";

interface Props {
  value: string;
  onChange: (html: string) => void;
}

/**
 * TipTap mit reduziertem Toolset. Output ist sauberes XHTML-nahes HTML
 * (keine Inline-Styles, keine div-Suppe) — passt zur EPUB-Validierung.
 */
export function RichTextEditor({ value, onChange }: Props) {
  const [annOpen, setAnnOpen] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [anchorText, setAnchorText] = useState("");

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Image.configure({ inline: false, allowBase64: false }),
      Annotation,
    ],
    content: value,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
    editorProps: { attributes: { class: "page-editor" } },
  });

  // Externen Wertwechsel (z. B. Seitenwechsel) übernehmen.
  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editor]);

  if (!editor) return null;

  const annotationActive = editor.isActive("annotation");
  const { from, to } = editor.state.selection;
  const canAnnotate = from !== to || annotationActive;

  const openAnnotation = () => {
    const selected = editor.state.doc.textBetween(from, to, " ");
    const existing = editor.getAttributes("annotation").note as string | undefined;
    setAnchorText(selected || "(bestehende Markierung)");
    setNoteText(existing ?? "");
    setAnnOpen(true);
  };
  const applyAnnotation = () => {
    editor.chain().focus().extendMarkRange("annotation").setAnnotation(noteText).run();
    setAnnOpen(false);
  };
  const removeAnnotation = () => {
    editor.chain().focus().extendMarkRange("annotation").unsetAnnotation().run();
    setAnnOpen(false);
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        <ToolbarButton
          active={editor.isActive("heading", { level: 2 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        >
          H2
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("heading", { level: 3 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        >
          H3
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <b>B</b>
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <i>I</i>
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          • Liste
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          1. Liste
        </ToolbarButton>
        <ToolbarButton
          active={editor.isActive("blockquote")}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          „Zitat"
        </ToolbarButton>
        <ToolbarButton
          active={annotationActive}
          onClick={openAnnotation}
          disabled={!canAnnotate}
          title="Markierten Text mit einer klickbaren Erklärung versehen"
        >
          <MessageSquarePlus className="h-4 w-4" /> Erklärung
        </ToolbarButton>
      </div>
      <EditorContent editor={editor} />

      <Dialog open={annOpen} onOpenChange={setAnnOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Erklärung hinzufügen</DialogTitle>
            <DialogDescription>
              Erscheint als klickbares Popover in der Vorschau, als Fußnote in
              EPUB und PDF.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
              <span className="text-muted-foreground">Markierter Text: </span>
              {anchorText}
            </div>
            <div className="space-y-1">
              <Label>Erklärung</Label>
              <Textarea
                rows={8}
                autoFocus
                placeholder="z. B. Wort-für-Wort-Übersetzung, Grammatik, Aussprache …"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
              />
            </div>
            <div className="flex justify-between">
              {annotationActive ? (
                <Button variant="ghost" onClick={removeAnnotation}>
                  Entfernen
                </Button>
              ) : (
                <span />
              )}
              <Button onClick={applyAnnotation} disabled={!noteText.trim()}>
                Übernehmen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ToolbarButton({
  active,
  onClick,
  children,
  disabled,
  title,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  title?: string;
}) {
  return (
    <Button
      type="button"
      variant="secondary"
      size="sm"
      disabled={disabled}
      title={title}
      className={cn(active && "bg-primary text-primary-foreground")}
      onClick={onClick}
    >
      {children}
    </Button>
  );
}
