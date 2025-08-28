from app import app, db, Book
from docx import Document
from datetime import datetime

def import_books_from_docx(file_path):
    with app.app_context():
        # Load the Word file
        try:
            doc = Document(file_path)
        except Exception as e:
            print(f"Error opening file: {e}")
            return

        imported_count = 0
        skipped_count = 0

        for table_idx, table in enumerate(doc.tables, start=1):
            for i, row in enumerate(table.rows):
                if i == 0:
                    continue  # Skip header row

                cells = row.cells
                try:
                    title = cells[1].text.strip() if len(cells) > 1 else ""
                    author = cells[2].text.strip() if len(cells) > 2 else ""
                    classification_no = cells[3].text.strip() if len(cells) > 3 else ""
                    cutter_no = cells[4].text.strip() if len(cells) > 4 else ""
                    publisher_name = cells[5].text.strip() if len(cells) > 5 else ""
                    price_text = cells[6].text.strip() if len(cells) > 6 else ""
                except Exception as e:
                    print(f"⚠️ Error reading row {i} in table {table_idx}: {e}")
                    skipped_count += 1
                    continue

                # Try parsing price
                price = 0.0
                if price_text:
                    try:
                        # Remove common symbols before converting
                        clean_price = (
                            price_text.replace("$", "")
                            .replace("₹", "")
                            .replace(",", "")
                            .strip()
                        )
                        price = float(clean_price)
                    except ValueError:
                        print(f"⚠️ Invalid price '{price_text}' at row {i}, using 0.0")
                        price = 0.0

                # Always insert the row, even if title/author missing
                book = Book(
                    title=title or "Untitled",
                    author=author or "Unknown",
                    classification_no=classification_no,
                    cutter_no=cutter_no,
                    publisher_name=publisher_name,
                    quantity=1,
                    price=price,
                    date_of_purchase=datetime.now()
                )

                db.session.add(book)
                imported_count += 1

        db.session.commit()
        print(f"✅ Import completed! {imported_count} books added, {skipped_count} skipped due to errors.")


if __name__ == "__main__":
    file_path = "books.docx"  # Replace with your actual file path
    import_books_from_docx(file_path)
