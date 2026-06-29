from backend.portfolio.context import PortfolioProject

_model = None


def _default_embed(texts: list[str]) -> list[list[float]]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts).tolist()


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def match_projects(need_text, projects, top_k=2, embed=_default_embed):
    proj_texts = [f"{p.description} {' '.join(p.pitch_for)}" for p in projects]
    vectors = embed([need_text] + proj_texts)
    need_vec, proj_vecs = vectors[0], vectors[1:]
    scored = sorted(
        zip(projects, proj_vecs),
        key=lambda pv: _cosine(need_vec, pv[1]),
        reverse=True,
    )
    return [p for p, _ in scored[:top_k]]
