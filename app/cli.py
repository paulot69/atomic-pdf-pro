import argparse
import traceback
import sys
from pathlib import Path
from app.extractor.extractor import extract_text
from app.chapter_splitter.splitter import split_into_chapters
from app.cleaner.cleaner import clean_section_text
from app.writer.writer import write_vault
from app.atomic_distiller.distiller import process_to_atomic_vault
from app.verifier.verifier import verify_links # New import

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to a structured Obsidian vault.")
    parser.add_argument("input_dir", help="The directory containing the PDF file(s).")
    parser.add_argument("output_dir", help="The root directory for the generated pre-atomic vault.")
    parser.add_argument("--atomic_output_dir", default="D:\\github\\Libros Atomicos", help="The root directory for the generated atomic vault.")
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
        print(f"Step 1/6: Extracting and cleaning text from '{pdf_path.name}'...")
        pages_structured_text = extract_text(pdf_path) # Now returns structured text
        print("Text extraction complete.")

        # 2. Split text into chapters and sections
        print("Step 2/6: Splitting text into chapters and sections...")
        chapters = split_into_chapters(pages_structured_text) # Pass structured text

        # 3. Clean each section's text
        print("Step 3/6: Cleaning section content...")
        for chapter in chapters:
            for section in chapter['sections']:
                section['content'] = clean_section_text(section['content'])
        print("Content cleaning complete.")

        # 4. Process to Atomic Vault (New Step)
        print("Step 4/6: Processing to Atomic Vault structure...")
        atomic_chapters = process_to_atomic_vault(
            chapters=chapters,
            book_title=args.titulo,
            author=args.autor,
            year=int(args.ano)
        )

        # 5. Write the Atomic Vault structure
        print("Step 5/6: Writing Atomic Obsidian vault...")
        write_vault(
            output_path=args.atomic_output_dir, # Use the new atomic output directory
            book_title=args.titulo,
            author=args.autor,
            year=int(args.ano),
            chapters=atomic_chapters # Pass the (soon-to-be) atomic chapters
        )

        print("\nProcessing complete!")
        atomic_vault_path = Path(args.atomic_output_dir) / f'{args.ano} - {args.titulo} - {args.autor}'
        print(f"Atomic Vault for '{args.titulo}' created at: {atomic_vault_path}")

        # 6. Verify Link Integrity (New Step)
        print("Step 6/6: Verifying link integrity...")
        broken_links = verify_links(atomic_vault_path)
        if broken_links:
            print("\nWARNING: Found broken links in the generated vault:")
            for link_info in broken_links:
                print(f"  - In '{link_info['source_file']}': [[{link_info['broken_link']}]]")
            sys.exit(1) # Exit with error if broken links are found
        else:
            print("  Link integrity verification complete. No broken links found.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
