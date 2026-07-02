def _default_scrape(**kwargs) -> list[dict]:
    from jobspy import scrape_jobs

    df = scrape_jobs(**kwargs)
    return df.to_dict("records") if df is not None else []


def fetch_jobspy(term: str, results: int = 20, scrape=_default_scrape) -> list[dict]:
    rows = scrape(
        site_name=["indeed", "linkedin"],
        search_term=term,
        results_wanted=results,
        hours_old=72,
    )
    out = []
    for row in rows:
        budget = row.get("min_amount") or row.get("max_amount")
        out.append(
            {
                "source": "jobspy",
                "title": row.get("title", ""),
                "description": row.get("description", "") or "",
                "url": row.get("job_url", ""),
                "budget": str(budget) if budget else None,
            }
        )
    return out
