import fitz
import json

def analyze_titles(path):
    doc = fitz.open(path)
    results = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        blocks = page.get_text("blocks")
        # Clean blocks
        clean_blocks = []
        for b in blocks:
            text = b[4].strip()
            if text and not "watch the entire video here" in text.lower():
                clean_blocks.append(text)
        
        results.append({
            "page": i + 1,
            "blocks": clean_blocks
        })
    doc.close()
    return results

if __name__ == "__main__":
    analysis = analyze_titles("GRE Math flashcards - GreenlightTestPrep_1.pdf")
    with open("analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
