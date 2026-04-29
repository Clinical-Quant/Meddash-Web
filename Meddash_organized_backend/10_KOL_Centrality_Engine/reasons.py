"""Human-readable centrality score reasons."""


def reason_for_row(row):
    score = row.get("authorship_centrality_score", 0) or 0
    tier = row.get("authorship_centrality_tier", "")
    reliability = row.get("reliability_score", 0) or 0
    pubs = row.get("publication_count_mapped", 0) or 0
    coauthors = row.get("coauthor_count_mapped", 0) or 0
    component = row.get("component_size", 0) or 0
    if tier == "Insufficient Data":
        return (
            f"Insufficient mapped authorship data: {pubs} mapped publications and {coauthors} mapped coauthors. "
            "Do not interpret this as low real-world influence until more of the publication network is pulled."
        )
    if reliability < 40:
        return (
            f"Mapped score is {score}/100, but reliability is low ({reliability}/100). "
            f"The KOL has {pubs} mapped publications, {coauthors} mapped coauthors, and component size {component}; score may be understated."
        )
    if score >= 85:
        return (
            f"High mapped authorship centrality: strong coauthor connectivity, PageRank, and bridging position within a component of {component} mapped KOLs."
        )
    if score >= 70:
        return (
            f"Strong mapped authorship centrality: above-average collaboration links and network position across {coauthors} mapped coauthors."
        )
    if score >= 50:
        return (
            f"Moderate mapped authorship centrality: visible in the coauthorship graph but not currently a top network anchor."
        )
    return (
        f"Lower mapped authorship centrality in current data: {pubs} mapped publications and {coauthors} mapped coauthors. "
        "Interpret with reliability and limitations."
    )


def apply_reasons(rows):
    return [{**row, "score_reason": reason_for_row(row)} for row in rows]
