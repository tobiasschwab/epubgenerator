import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { useBooks, useCreateBook, useDeleteBook } from "./hooks";

export function BooksListPage() {
  const { data: books, isLoading, isError } = useBooks();
  const createBook = useCreateBook();
  const deleteBook = useDeleteBook();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    createBook.mutate(
      { title: title.trim(), description: description.trim() },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
        },
      },
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      <header>
        <h1 className="text-3xl font-bold">Meine Bücher</h1>
        <p className="text-muted-foreground">EPUB3-Bücher erstellen und exportieren.</p>
      </header>

      <Card className="p-4">
        <form onSubmit={submit} className="space-y-3">
          <h2 className="font-semibold">Neues Buch</h2>
          <Input
            placeholder="Titel"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Textarea
            placeholder="Beschreibung (optional)"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button type="submit" disabled={!title.trim() || createBook.isPending}>
            {createBook.isPending ? "Anlegen…" : "Buch anlegen"}
          </Button>
        </form>
      </Card>

      <section className="space-y-3">
        {isLoading && <p className="text-muted-foreground">Lädt…</p>}
        {isError && <p className="text-destructive">Bücher konnten nicht geladen werden.</p>}
        {books?.length === 0 && (
          <p className="text-muted-foreground">Noch keine Bücher vorhanden.</p>
        )}
        {books?.map((book) => (
          <Card key={book.id} className="flex items-center justify-between p-4">
            <div>
              <Link to={`/books/${book.id}`} className="text-lg font-medium hover:underline">
                {book.title || "Ohne Titel"}
              </Link>
              <p className="text-sm text-muted-foreground">
                {book.chapter_count} Kapitel
                {book.description ? ` · ${book.description}` : ""}
              </p>
            </div>
            <div className="flex gap-2">
              <Link to={`/books/${book.id}`}>
                <Button variant="secondary" size="sm">
                  Öffnen
                </Button>
              </Link>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => {
                  if (confirm(`Buch „${book.title}" wirklich löschen?`)) {
                    deleteBook.mutate(book.id);
                  }
                }}
              >
                Löschen
              </Button>
            </div>
          </Card>
        ))}
      </section>
    </div>
  );
}
