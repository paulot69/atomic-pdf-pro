import argparse
import traceback
from app.extractor.extractor import extract_text
from app.chapter_splitter.splitter import split_into_chapters
from app.cleaner.cleaner import clean_chapter_text
from app.writer.writer import write_vault

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to an Obsidian vault.")
    parser.add_argument("pdf_path", help="The path to the PDF file.")
    parser.add_argument("output_path", help="The path to the output directory.")
    parser.add_argument("--titulo", required=True, help="The title of the book.")
    parser.add_argument("--autor", required=True, help="The author of the book.")
    parser.add_argument("--ano", required=True, help="The year of the book.")

    args = parser.parse_args()

    try:
        print("Starting PDF processing...")

        # 1. Extract text from PDF
        print(f"Extracting text from '{args.pdf_path}'...")
        pages_text = extract_text(args.pdf_path)
        print("Text extraction complete.")

        # 2. Split text into chapters
        print("Splitting text into chapters...")
        chapters = split_into_chapters(pages_text)
        print(f"Found {len(chapters)} chapter(s).")

        # 3. Clean each chapter's text
        print("Cleaning chapter text...")
        cleaned_chapters = []
        for i, chapter in enumerate(chapters):
            print(f"Cleaning chapter {i+1}/{len(chapters)}...")
            cleaned_content = clean_chapter_text(chapter["content"], pages_text)
            cleaned_chapters.append({
                "number": chapter["number"],
                "title": chapter["title"],
                "content": cleaned_content
            })
        print("Text cleaning complete.")

        # 4. Write the vault structure
        print("Writing Obsidian vault...")
        write_vault(
            output_path=args.output_path,
            book_title=args.titulo,
            author=args.autor,
            year=int(args.ano),
            chapters=cleaned_chapters
        )

        print("Processing complete!")
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
