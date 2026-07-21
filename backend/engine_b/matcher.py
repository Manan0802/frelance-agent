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


# Measured against the real portfolio with all-MiniLM-L6-v2: genuine matches
# scored 0.38-0.74, while a stretch (image-optimisation -> ShopLens, a visual
# *search* project) scored 0.189 — below even an unrelated legal query at 0.187.
# The floor sits in the empty band between those groups. RE-MEASURE THIS if the
# embedding model ever changes; cosine distributions are not comparable across
# models.
MIN_SIMILARITY = 0.30


def match_projects(need_text, projects, top_k=2, embed=_default_embed,
                   min_similarity=MIN_SIMILARITY):
    """Top-k projects above a relevance floor. Returns fewer than top_k — possibly
    none — rather than padding with weak matches the writer would have to stretch."""
    proj_texts = [f"{p.description} {' '.join(p.pitch_for)}" for p in projects]
    vectors = embed([need_text] + proj_texts)
    need_vec, proj_vecs = vectors[0], vectors[1:]
    scored = sorted(
        ((p, _cosine(need_vec, v)) for p, v in zip(projects, proj_vecs)),
        key=lambda pv: pv[1],
        reverse=True,
    )
    return [p for p, sim in scored[:top_k] if sim >= min_similarity]
