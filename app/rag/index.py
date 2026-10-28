"""Local RAG index using TF-IDF retrieval; no external vector service is required."""
from pathlib import Path
import hashlib, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings
from app.core.db import engine, init_db
from sqlalchemy import text

class PolicyIndex:
    def __init__(self, docs_dir=None):
        self.docs_dir = Path(docs_dir or settings.policy_docs_dir)
        self.chunks = []
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=25000)
        self.matrix = None

    @staticmethod
    def _split(text_value, max_chars=1100, overlap=160):
        # Paragraph-aware chunking keeps related policy context together.
        paras = [p.strip() for p in re.split(r"\n\s*\n", text_value) if p.strip()]
        chunks, buf = [], ""
        for para in paras:
            if len(buf) + len(para) > max_chars and buf:
                chunks.append(buf); buf = buf[-overlap:] + "\n" + para
            else: buf = (buf + "\n\n" + para).strip()
        if buf: chunks.append(buf)
        return chunks

    def build(self):
        init_db(); self.chunks = []
        for path in sorted(self.docs_dir.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            title = next((x.lstrip('# ').strip() for x in raw.splitlines() if x.startswith('# ')), path.stem)
            source = next((x.split('**Source:**',1)[1].strip() for x in raw.splitlines() if '**Source:**' in x), '')
            topic = next((x.split('**Topic:**',1)[1].strip() for x in raw.splitlines() if '**Topic:**' in x), 'general')
            for i, chunk in enumerate(self._split(raw)):
                digest = hashlib.sha256((path.name+str(i)+chunk).encode()).hexdigest()
                self.chunks.append({"chunk_id":digest[:24],"source_file":path.name,"title":title,"topic":topic,
                                    "source_url":source,"text":chunk,"content_hash":digest})
        self.matrix = self.vectorizer.fit_transform([c['text'] for c in self.chunks]) if self.chunks else None
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM retrieved_chunks"))
            for c in self.chunks:
                conn.execute(text("""INSERT INTO retrieved_chunks(chunk_id,source_file,title,topic,source_url,text,content_hash)
                  VALUES(:chunk_id,:source_file,:title,:topic,:source_url,:text,:content_hash)"""), c)
        return len(self.chunks)

    def search(self, query, top_k=4):
        if self.matrix is None: self.build()
        if not self.chunks: return []
        qv = self.vectorizer.transform([query]); scores = cosine_similarity(qv, self.matrix).ravel()
        ids = scores.argsort()[::-1][:top_k]
        return [{**self.chunks[i],"score":float(scores[i])} for i in ids if scores[i] > 0]

_index = None
def get_index():
    global _index
    if _index is None:
        _index = PolicyIndex(); _index.build()
    return _index
