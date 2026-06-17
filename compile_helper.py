from pathlib import Path
from bookforge.core.compiler import compile_manuscript

book_folder = Path("books/tex-cade/books-2")

# Compile to manuscript.md
compile_manuscript(book_folder, book_folder / "manuscript.md", include_title=True)

# Compile to compiled-manuscript.md
compile_manuscript(book_folder, book_folder / "compiled-manuscript.md", include_title=True)

print("Manuscript successfully compiled to both locations.")
