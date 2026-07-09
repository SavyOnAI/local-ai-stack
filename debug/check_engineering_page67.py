import pdfplumber

with pdfplumber.open("docs/Engineering_the_RAG_Stack_Architecture_&_Trust.pdf") as pdf:
    print(pdf.pages[66].extract_text()[:400])

if __name__ == "__main__":
    pass