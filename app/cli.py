import argparse
import traceback
import sys
from pathlib import Path
from app.extractor.extractor import extract_text
from app.chapter_splitter.splitter import split_into_chapters
from app.cleaner.cleaner import clean_chapter_text
from app.writer.writer import write_vault

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to an Obsidian vault.")
    parser.add_argument("input_dir", help="The directory containing the PDF file.")
    parser.add_argument("output_dir", help="The root directory for the generated vault.")
    parser.add_argument("--titulo", required=True, help="The title of the book.")
    parser.add_argument("--autor", required=True, help="The author of the book.")
    parser.add_argument("--ano", required=True, help="The year of the book.")

    args = parser.parse_args()

    try:
        # Find the single PDF file in the input directory
        input_path = Path(args.input_dir)
        pdf_files = list(input_path.glob("*.pdf"))

        if not pdf_files:
            print(f"Error: No PDF files found in '{args.input_dir}'.", file=sys.stderr)
            sys.exit(1)

        if len(pdf_files) > 1:
            print(f"Error: Multiple PDF files found in '{args.input_dir}'. This tool currently supports only one PDF per run.", file=sys.stderr)
            sys.exit(1)

        pdf_path = pdf_files[0]

        print("Starting PDF processing...")

        # 1. Extract text from PDF
        print(f"Extracting text from '{pdf_path}'...")
        pages_text = extract_text(pdf_path)
        print("Text extraction complete.")

        # 2. Split text into chapters
        print("Splitting text into chapters...")
        chapters = split_into_chapters(pages_text)

        # 3. Clean each chapter's text
        print("Cleaning chapter text...")
        cleaned_chapters = []
        for i, chapter in enumerate(chapters):
            print(f"Cleaning chapter/section {i+1}/{len(chapters)}: {chapter['title']}")
            cleaned_content = clean_chapter_text(chapter["content"], pages_text)
            chapter['content'] = cleaned_content
            cleaned_chapters.append(chapter)
        print("Text cleaning complete.")

        # 4. Write the vault structure
        print("Writing Obsidian vault...")
        write_vault(
            output_path=args.output_dir,
            book_title=args.titulo,
            author=args.autor,
            year=int(args.ano),
            chapters=cleaned_chapters
        )

        print("Processing complete!")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
