from pypdf import PdfReader

reader = PdfReader("manuals/dell_manual.pdf")
print(f"Number of pages: {len(reader.pages)}")

for page_num in [0, 4, 9, 19, 49]:
    text = reader.pages[page_num].extract_text()
    print(f"--- Page {page_num} ({len(text)} characters) ---")
    print(text[:300])
    print()