# Sunbeams AI Multi-Level Worksheet Generator

Streamlit app that generates leveled, bilingual (Urdu/English) practice
worksheets grounded in Sunbeams' actual syllabus PDFs.

## Project structure

```
sunbeams-worksheet-generator/
├── app.py                  # Main Streamlit app (run this)
├── colab_setup.py          # Helper to launch the app from Google Colab
├── requirements.txt
├── utils/
│   ├── pdf_indexer.py      # Scans dataset-sunbeams/ and builds grade->term->subject index
│   ├── pdf_extractor.py    # Extracts + caches text from syllabus PDFs
│   ├── ai_generator.py     # Builds the prompt and calls Claude to generate the worksheet
│   └── pdf_exporter.py     # Renders the worksheet JSON into a printable PDF
├── fonts/
│   └── NotoNastaliqUrdu.ttf   # <-- YOU MUST ADD THIS (see below)
└── dataset-sunbeams/       # Your syllabus PDFs (PA / PB / PC folders)
```

## Setup steps

1. **Add the dataset.** Place your `dataset-sunbeams/` folder (with `PA`,
   `PB`, `PC` subfolders) either next to `app.py`, or point the
   `DATASET_ROOT` environment variable at it (e.g. a Google Drive path
   in Colab).

2. **Add a Urdu-capable font.** Download **Noto Nastaliq Urdu** (free,
   Google Fonts) and save it as `fonts/NotoNastaliqUrdu.ttf`. Without
   this, the on-screen worksheet still works, but exported PDFs won't
   render Urdu correctly.

3. **Set your API key.** This project uses **Groq** for the AI calls
   (free tier, no credit card, generous daily request limit — a good
   fit for a free tool used across 200+ schools). Get a key at
   https://console.groq.com/keys.
   - Locally: `export GROQ_API_KEY=gsk_...`
   - Colab: store it in Colab Secrets (the key icon in the left
     sidebar) as `GROQ_API_KEY`, then load it with `userdata.get()`
     (see `colab_setup.py` docstring for the exact cell sequence).

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run:**
   - Locally: `streamlit run app.py`
   - In Colab: see the cell sequence at the top of `colab_setup.py`,
     then call `launch_app()` to get a public tunnel URL.

## Notes on the dataset

Filenames in the real dataset are inconsistent (`"salybas"`,
`"syllabas"`, `"midterm"` vs `"Mid Line"`, etc). `pdf_indexer.py`
handles this with fuzzy matching (`rapidfuzz`) against known term and
subject aliases -- you don't need to rename any files. If a new file
doesn't match well, it will still show up in the app under whatever
name was extracted from the filename, so nothing gets silently
dropped.

## Next steps once this is working

- Deploy to **Streamlit Community Cloud** (free) so teachers can use
  it via a link, no installs needed.
- Move the dataset to a shared Google Drive / cloud storage location
  rather than bundling it in the repo.
- Consider adding a simple teacher login/PIN if you don't want the
  tool fully public once deployed.
