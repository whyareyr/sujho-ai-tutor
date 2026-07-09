# NCERT PDFs

Download Class 12 Mathematics, Physics, and Chemistry PDFs from [NCERT](https://ncert.nic.in/textbook.php).

Use `manifest.json` for the required books, NCERT codes, and suggested filenames under `data/raw/`.

On the site: select Class XII, pick the subject, download the matching full book PDF.

If your solution creates derived files, document how to rebuild them.

Metadata per chunk: subject, book, part, chapter, page, source. Subject/book come from the manifest (keyed by code); part is the code's last digit; chapter and page come from the file and page index.
Chunking decision: chunk per page, so every citation gets an exact page. Tradeoff — occasional mid-idea cut at a page break, softened by overlap. Defensible and simple.
