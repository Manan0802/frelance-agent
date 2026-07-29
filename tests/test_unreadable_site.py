"""Couldn't read their site != they don't have one.

Second false claim from the live Austin run, and the mirror image of the first.
Once block pages stopped counting as content, FastMed Urgent Care — which has a
working website that simply 403'd our fetcher — got the no-website angle and was
told "You don't have a website, so you're likely handling enquiries manually."

There are three states, not two, and the prospecting reference names them:
no site at all, a site we couldn't read, and a site we read. Only the first
supports claiming an absence, because only there is the absence a fact.
"""

from backend.engine_b.writer import write_message
from backend.portfolio.context import PortfolioProject


def _target(website):
    return type("T", (), {"name": "FastMed", "category": "clinic",
                          "location": "Austin, USA", "website": website})()


def _capture(store):
    def llm(prompt):
        if "ONLY the subject line" in prompt:
            return "front desk"
        if "Score" in prompt or "score" in prompt:
            return "9"
        store.append(prompt)
        return "draft body"
    return llm


PROJECTS = [PortfolioProject(name="Site", type="web", description="a thing", tech=["Python"])]


def test_an_unreadable_site_is_never_called_an_absence():
    prompts = []
    write_message(_target("https://fastmed.com"),
                  {"research_summary": "", "pain_points": "p", "has_source": False},
                  PROJECTS, llm=_capture(prompts))

    body = prompts[0]
    assert "NO WEBSITE" not in body
    assert "could not find" not in body
    assert "COULD NOT BE READ" in body


def test_no_website_at_all_still_gets_the_absence_angle():
    """That absence is verified, and it is the strongest hook we have."""
    prompts = []
    write_message(_target(""),
                  {"research_summary": "", "pain_points": "p", "has_source": False},
                  PROJECTS, llm=_capture(prompts))

    assert "NO WEBSITE" in prompts[0]


def test_a_social_page_still_counts_as_no_website():
    """A Facebook page is not a site, so the absence claim stays true."""
    prompts = []
    write_message(_target("https://facebook.com/fastmed"),
                  {"research_summary": "", "pain_points": "p", "has_source": False},
                  PROJECTS, llm=_capture(prompts))

    assert "NO WEBSITE" in prompts[0]


def test_a_site_we_read_gets_the_researched_angle():
    prompts = []
    write_message(_target("https://fastmed.com"),
                  {"research_summary": "they do walk-ins", "pain_points": "p", "has_source": True},
                  PROJECTS, llm=_capture(prompts))

    assert "ALREADY HAS A WEBSITE" in prompts[0]
