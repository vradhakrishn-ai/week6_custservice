from pathlib import Path

root = Path(__file__).resolve().parent.parent
output = root / "data" / "knowledge_base" / "sample_corpus.txt"
output.write_text("SecureBank charges a small fee for NEFT transfers after the free quota.\n", encoding="utf-8")
print(output)
