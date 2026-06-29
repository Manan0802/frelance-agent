from backend.portfolio.context import load_portfolio


def test_load_portfolio():
    ctx = load_portfolio("data/portfolio_context.json")
    assert ctx.personal["name"] == "Manan"
    assert any(p.name == "SARA" for p in ctx.projects)
    sara = next(p for p in ctx.projects if p.name == "SARA")
    assert "AI agent" in sara.pitch_for
