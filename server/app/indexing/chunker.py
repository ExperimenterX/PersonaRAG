from typing import Iterable

def chunk_text(text: str, size: int, overlap: int) -> Iterable[str]:
    words = text.split()
    step = max(1, size - overlap)
    for i in range(0, len(words), step):
        yield " ".join(words[i:i+size])
