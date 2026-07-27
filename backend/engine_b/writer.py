from backend.llm.gemini import generate
from backend.engine_b.humanize import ai_tells, HUMAN_RULES

RULES = """Rules: start with the client's problem (never "Hi I am Manan"); reference one
specific detail; mention one relevant past project; name the tech you'd use — use ONLY tech
listed in that project's stack above, never invent a tool or framework that isn't listed;
under 120 words; end with one question; do NOT commit a price; confident peer tone, not
sycophantic.

""" + HUMAN_RULES

NO_PROJECT_RULES = """Rules: start with the client's problem (never "Hi I am Manan"); reference one
specific detail; DO NOT mention any past project and DO NOT NAME ANY SPECIFIC TECH, framework or
tool — you have been given none, and naming one you can't back up loses the client; under 120
words; end with one question; do NOT commit a price; confident peer tone, not sycophantic.

""" + HUMAN_RULES


def rules_for(projects) -> str:
    """The tech/citation rules only make sense when a project was actually
    matched. Left in unconditionally, "name the tech you'd use" is the LAST and
    most direct instruction the model sees, and it overrides any earlier "don't"
    — a live run still emitted "Using Next.js" with no project cited. Removing
    the clause works where negating it did not."""
    return RULES if projects else NO_PROJECT_RULES

WRITE_PROMPT = """Write a cold outreach message to {name}, a {category} in {location}.
Their situation: {summary}
Their likely pain: {pain}
Relevant past work you can cite: {projects}
{grounding}{rules}{stricter}"""

NO_WEBSITE_ANGLE = """
ANGLE — this business appears to have NO WEBSITE. You searched and could not find one. That
absence is the ONE thing you actually verified, so it opens the message — but read it as EVIDENCE,
not as the product: a business with no web presence is almost certainly running enquiries,
bookings and follow-ups MANUALLY, by phone and on paper.

Pitch the outcome that fixes, drawn from your past work above — an AI assistant that answers
enquiries, automated booking or intake, a system that stops missed calls turning into lost
customers, whatever your cited work actually supports. A website may be part of how you deliver
it, but do NOT make "I'll build you a website" the offer: that is the cheapest thing you sell and
it anchors the whole relationship at that price.

Do NOT invent or assert anything else about them (what they sell, their customers, their history,
their current setup) — you know none of it, and a believable-sounding guess that turns out wrong
loses the client.
"""

RESEARCHED_ANGLE = """
ANGLE — this business ALREADY HAS A WEBSITE, and the notes above come from actually reading it.
Do NOT offer to build them a website. Pitch from what you genuinely observed, reaching for the
highest-value thing your cited past work supports — an AI assistant, workflow or data automation,
a custom tool or app, ML/prediction, a dashboard — not cosmetic site tweaks. Lead with what it
does for their business, not with the technology.
"""

OFFER_SCORE_PROMPT = """Score this cold outreach message 0-10 on how strong and concrete its
OFFER is. This message goes to a business with no website, so do NOT judge it on
business-specific insight — there is none to be had, and inventing some would be worse.

Lowers the score:
- vague benefit language ("grow your business", "boost your presence") with nothing concrete
- claiming to know things about the business it cannot know
- leading with a commodity deliverable ("I'll build you a website") rather than an outcome
- no clear next step

Raises the score:
- a concrete OUTCOME for the business — work it stops doing by hand, time or customers it saves
- a specific, named thing that would be built to achieve it
- credible proof (a real past project) and a clear, low-friction ask

0-3 = vague, no real offer. 4-6 = an offer, but woolly.
7-8 = clear concrete deliverable and ask. 9-10 = that, plus credible proof and a sharp hook.

Reply with ONLY a number.

Message:
{msg}"""

SCORE_PROMPT = """Score this cold outreach message 0-10 on how specifically it is tailored to
THIS business. Judge tailoring only — not how well written or persuasive it is.

Does NOT count as personalization:
- restating facts the sender already knew (the business name, its city, its category)
- generic claims any competitor could receive ("no online presence", "missing out on sales")
- flattery

Does count:
- a concrete detail that could only come from actually looking at this business
- a problem tied to how THIS business specifically operates

0-3 = generic template, could be sent to any business of this type.
4-6 = lightly tailored, but no real insight about them.
7-8 = one genuine specific observation about this business.
9-10 = multiple specific observations, tied to a concrete proposed fix.

Reply with ONLY a number.

Message:
{msg}"""


NO_MATCH_NOTE = (
    "(NO PAST PROJECT is a close enough match to this need. Do not cite past work, "
    "and do NOT invent a project or claim experience you weren't given. This also "
    "overrides the tech rule below: DO NOT NAME ANY SPECIFIC TECH, framework or "
    "tool, since none has been given to you here. Make the offer on its own merits "
    "and keep it brief.)"
)


def format_projects(projects) -> str:
    """Include each project's real stack — without it the LLM has no grounding
    for the "name the tech you'd use" rule and invents one. An empty list means
    the relevance floor rejected everything, which must be said explicitly or the
    model fabricates a citation to satisfy the "cite a project" rule."""
    if not projects:
        return NO_MATCH_NOTE
    return "; ".join(
        f"{p.name} [built with: {', '.join(p.tech)}]: {p.description}" if p.tech
        else f"{p.name}: {p.description}"
        for p in projects
    )


def _draft(target, research, projects, llm, stricter=""):
    proj_str = format_projects(projects)
    return llm(
        WRITE_PROMPT.format(
            name=target.name,
            category=target.category or "business",
            location=target.location or "",
            summary=research.get("research_summary", ""),
            pain=research.get("pain_points", ""),
            projects=proj_str,
            grounding=RESEARCHED_ANGLE if research.get("has_source") else NO_WEBSITE_ANGLE,
            rules=rules_for(projects),
            stricter=stricter,
        )
    )


def _score(msg, llm, has_source=True) -> float:
    """No-website pitches are judged on offer strength, researched ones on
    tailoring — scoring both on tailoring floors the former at ~4/10 and makes
    the regen loop chase specifics that don't exist."""
    template = SCORE_PROMPT if has_source else OFFER_SCORE_PROMPT
    raw = llm(template.format(msg=msg))
    try:
        return float("".join(c for c in raw if c.isdigit() or c == ".")[:4])
    except ValueError:
        return 0.0


def write_message(target, research, projects, llm=generate) -> dict:
    has_source = bool(research.get("has_source"))
    draft = _draft(target, research, projects, llm)

    # A draft that reads like marketing copy gets deleted on sight. Naming the
    # specific tell matters: "sound more human" without it returns the same text.
    tells = ai_tells(draft)
    if tells:
        draft = _draft(
            target, research, projects, llm,
            stricter="\nYour previous draft read like AI marketing copy. It used: "
                     + "; ".join(tells)
                     + ". Rewrite it plainly, as one person emailing another.",
        )

    score = _score(draft, llm, has_source)
    if score < 7:
        draft = _draft(
            target,
            research,
            projects,
            llm,
            stricter=(
                "\nBe stricter: cite a concrete detail unique to this business."
                if has_source
                else "\nBe stricter: make the deliverable and the next step more concrete."
            ),
        )
        score = _score(draft, llm, has_source)
    return {
        "draft_text": draft,
        "personalization_score": score,
        "portfolio_used": [p.name for p in projects],
    }
