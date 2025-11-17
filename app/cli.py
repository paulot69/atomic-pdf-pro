import argparse
import traceback
import sys
from pathlib import Path
from app.extractor.extractor import extract_text
from app.chapter_splitter.splitter import split_into_chapters
from app.cleaner.cleaner import clean_section_text
from app.writer.writer import write_vault

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to a structured Obsidian vault.")
    parser.add_argument("input_dir", help="The directory containing the PDF file(s).")
    parser.add_argument("output_dir", help="The root directory for the generated vault.")
    parser.add_argument("--titulo", required=True, help="The title of the book.")
    parser.add_argument("--autor", required=True, help="The author of the book.")
    parser.add_argument("--ano", required=True, help="The year of the book.")

    args = parser.parse_args()

    try:
        input_path = Path(args.input_dir)
        pdf_files = sorted(list(input_path.glob("*.pdf")))

        if not pdf_files:
            print(f"Error: No PDF files found in '{args.input_dir}'.", file=sys.stderr)
            sys.exit(1)

        # TODO: Implement processing for all PDFs. For now, process only the first one.
        if len(pdf_files) > 1:
            print(f"Warning: Multiple PDF files found. Processing the first one: '{pdf_files[0].name}'")

        pdf_path = pdf_files[0]

        print(f"Processing book: {args.titulo}...")

        # 1. Extract text from PDF
        print(f"Step 1/4: Extracting and cleaning text from '{pdf_path.name}'...")
        pages_text = extract_text(pdf_path)
        print("Text extraction complete.")

        # 2. Split text into chapters and sections
        print("Step 2/4: Splitting text into chapters and sections...")
        chapters = split_into_chapters(pages_text)

        # 3. Clean each section's text
        print("Step 3/4: Cleaning section content...")
        for chapter in chapters:
            for section in chapter['sections']:
                section['content'] = clean_section_text(section['content'])
        print("Content cleaning complete.")

        # 4. Write the vault structure
        print("Step 4/4: Writing Obsidian vault...")
        write_vault(
            output_path=args.output_dir,
            book_title=args.titulo,
            author=args.autor,
            year=int(args.ano),
            chapters=chapters
        )

        print("\nProcessing complete!")
        print(f"Vault for '{args.titulo}' created at: {Path(args.output_dir) / args.titulo}")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
