import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { BookEditorPage } from "@/features/books/BookEditorPage";
import { BooksListPage } from "@/features/books/BooksListPage";

const router = createBrowserRouter([
  { path: "/", element: <BooksListPage /> },
  { path: "/books/:bookId", element: <BookEditorPage /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
