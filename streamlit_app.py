"""HFpEF Clinical Evidence Navigator — curated, not systematic clinical evidence index.

Run locally: streamlit run streamlit_app.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.evidence import (
    csv_text,
    filter_guidelines,
    filter_studies,
    flatten_guideline,
    flatten_study,
    load_records,
    result_status,
)

st.set_page_config(
    page_title="HFpEF Clinical Evidence Navigator",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; max-width: 1300px;}
    [data-testid="stMetric"] {border: 1px solid #dae4e8; border-radius: 12px; padding: 1.0rem; background: #f6f9fa;}
    .eyebrow {color: #187779; letter-spacing: .14em; font-size: .78rem; font-weight: 700; text-transform: uppercase;}
    .subhead {color: #536775; font-size: 1.04rem; line-height: 1.55; margin: .3rem 0 1rem 0;}
    .muted {color: #667886; font-size: .86rem;}
    .trial-status {font-size: .85rem; font-weight: 650; color: #2d6571; padding-bottom: .5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=60)
def data():
    return load_records()

studies_data, guidance_data = data()
studies = studies_data["studies"]
guidance = guidance_data["guidelines"]
candidates = json.loads((Path(__file__).resolve().parent / "data" / "discovery_candidates.json").read_text(encoding="utf-8"))["candidates"]

st.markdown('<div class="eyebrow">Clinical research · Data navigator</div>', unsafe_allow_html=True)
st.title("HFpEF Clinical Evidence Navigator")
st.markdown(
    '<div class="subhead">Explore selected HFpEF and HFmrEF-spectrum trials and published guidance. '
    'Filter by research design, treatment class, outcomes, and clearly documented enrollment characteristics.</div>',
    unsafe_allow_html=True,
)
st.info(
    "**Research prototype, not clinical decision support.** This is a curated selection, not a systematic "
    "review. Abstract-level checks have been performed; independent full-text extraction, adjudication, "
    "and clinician review remain pending. Do not use the content to guide patient care."
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Studies", len(studies))
m2.metric("Guidance records", len(guidance))
m3.metric("All indexed records", len(studies) + len(guidance) + len(candidates))
m4.metric("Source check", studies_data["updated_at"])

with st.sidebar:
    st.header("Find evidence")
    keyword = st.text_input("Search studies", placeholder="e.g., empagliflozin, KCCQ, EF")
    types = st.multiselect("Study design", sorted({s.get("study_type", "Randomized trial") for s in studies}), placeholder="All study designs")
    categories = st.multiselect("Treatment category", sorted({s["treatment_category"] for s in studies}), placeholder="All treatments")
    outcome_options = sorted({tag for s in studies for tag in s.get("outcome_tags", [])})
    outcome_tags = st.multiselect("Outcome category", outcome_options, placeholder="All outcomes")
    phenotype_options = sorted({tag for s in studies for tag in s.get("phenotype_tags", [])})
    phenotype_tags = st.multiselect("Enrolled population tags", phenotype_options, placeholder="All enrolled populations",
                                  help="Tags describe enrollment characteristics, NOT evidence of a statistically proven subgroup effect.")
    statuses = st.multiselect("Primary result status", sorted({result_status(s) for s in studies}), placeholder="All results")
    years = st.slider("Publication year", min_value=min(s["year"] for s in studies), max_value=max(s["year"] for s in studies),
                      value=(min(s["year"] for s in studies), max(s["year"] for s in studies)))
    st.caption("Multiple selections within the same filter use OR; different filters use AND.")

filtered = filter_studies(
    studies,
    keyword=keyword,
    types=types,
    categories=categories,
    outcome_tags=outcome_tags,
    phenotype_tags=phenotype_tags,
    statuses=statuses,
    years=years,
)

st.caption(f"Showing **{len(filtered)} of {len(studies)}** study records · Last source-check date: {studies_data['updated_at']}")

tab_studies, tab_compare, tab_guidelines, tab_discovery, tab_audit, tab_about = st.tabs(
    ["Study explorer", "Compare studies", "Guidance documents", "Discovery queue", "Data quality", "Methods & scope"]
)

with tab_studies:
    l, r = st.columns([2, 1])
    with l:
        st.subheader("Searchable study index")
    with r:
        st.download_button(
            "Download filtered studies (CSV)",
            data="\ufeff" + csv_text([flatten_study(s) for s in filtered]),
            file_name="hfpef_filtered_studies.csv",
            mime="text/csv; charset=utf-8",
            use_container_width=True,
            disabled=not filtered,
        )
    if filtered:
        rows = [flatten_study(s) for s in filtered]
        cols = ["Study", "Year", "Study type", "Treatment category", "Sample size", "LVEF eligibility", "Primary result status"]
        st.dataframe(pd.DataFrame(rows)[cols], hide_index=True, use_container_width=True)
        st.download_button(
            "Download filtered JSON",
            data=json.dumps({"project": studies_data["project"], "schema_version": studies_data["schema_version"], "studies": filtered}, ensure_ascii=False, indent=2),
            file_name="hfpef_filtered_studies.json", mime="application/json",
        )
        st.markdown("#### Trial summaries & original sources")
        for s in filtered:
            with st.expander(f"{s['acronym']} ({s['year']}) · {s['intervention']['name']}"):
                st.markdown(f"**{s['title']}**")
                st.markdown(f"**Study design:** {s['study_type']}  ")
                st.markdown(f"**Population:** {s['population']['summary']}  ")
                st.markdown(f"**Enrolled:** {s['population']['sample_size']:,} · **LVEF criterion:** {s['population']['lvef_eligibility']}  ")
                st.markdown(f"**Treatment / comparator:** {s['intervention']['name']} vs {s['intervention']['comparator']}")
                st.markdown(f"**Primary outcomes:** {result_status(s)}")
                for o in s['primary_outcomes']:
                    st.markdown(f"- **{o['name']}** ({o['analysis']}): {o['result_text']}")
                st.markdown(f"**Interpretation:** {s['interpretation']}")
                if s['cautions']:
                    st.caption("Cautions: " + " · ".join(s['cautions']))
                st.caption("Source status: " + s['curation']['verification_status'])
                c1, c2, c3 = st.columns(3)
                c1.link_button("PubMed", s['reference']['pubmed_url'])
                c2.link_button("DOI", "https://doi.org/" + s['reference']['doi'])
                if s['reference'].get('clinicaltrials_id'):
                    c3.link_button("ClinicalTrials.gov", "https://clinicaltrials.gov/study/" + s['reference']['clinicaltrials_id'])
    else:
        st.warning("No trials match these settings. Broaden the search or clear some sidebar filters.")

with tab_compare:
    st.subheader("Side-by-side trial comparison")
    st.caption("Descriptive comparisons only: endpoints, effect measures, and patient populations differ. Do not pool these values as a meta-analysis.")
    choice = st.multiselect("Choose up to four studies", options=[s["acronym"] for s in sorted(studies, key=lambda x:x['acronym'].casefold())],
                            default=["DELIVER", "EMPEROR-Preserved"], max_selections=4)
    picked = [next(s for s in studies if s['acronym'] == name) for name in choice]
    if picked:
        cols = {}
        for s in picked:
            cols[s['acronym']] = {
                "Year": s['year'],
                "Design": s['study_type'],
                "Treatment": s['intervention']['name'],
                "Comparator": s['intervention']['comparator'],
                "Randomized sample size": f"{s['population']['sample_size']:,}",
                "LVEF criterion": s['population']['lvef_eligibility'],
                "Enrollment": s['population']['summary'],
                "Primary endpoint(s)": " / ".join(o['name'] for o in s['primary_outcomes']),
                "Primary result(s)": " / ".join(o['result_text'] for o in s['primary_outcomes']),
                "Overall status": result_status(s),
                "Source PMID": s['reference']['pmid'],
                "Review status": s['curation']['verification_status'],
            }
        st.dataframe(pd.DataFrame(cols), use_container_width=True)
        st.download_button("Download comparison CSV", "\ufeff" + pd.DataFrame(cols).to_csv(),
                           file_name="hfpef_trial_comparison.csv", mime="text/csv; charset=utf-8")
    else:
        st.caption("Select at least one study.")

with tab_guidelines:
    st.subheader("Guidance and consensus documents")
    st.caption("Three selected sources. A consensus pathway is labeled distinctly from formal graded guidelines; exact recommendations have not yet been individually extracted.")
    guidance_keyword = st.text_input("Search guidance", placeholder="e.g., diagnosis, SGLT2", key="guidance_keyword")
    guidance_topics = st.multiselect("Guidance topics", sorted({t for g in guidance for t in g["topics"]}), key="guidance_topic")
    visible_guidance = filter_guidelines(guidance, keyword=guidance_keyword, topics=guidance_topics)
    st.caption(f"{len(visible_guidance)} guidance records shown")
    for g in visible_guidance:
        with st.container(border=True):
            st.markdown(f"#### {g['short_name']}")
            st.caption(f"{g['year']} · {g['organization']} · {g['publication_type']}")
            st.write(g['summary'])
            st.caption("Topics: " + ", ".join(g['topics']))
            st.caption("Verification: " + g['verification_status'])
            st.link_button("Read indexed source", g['source_url'])
    st.download_button("Download guidance CSV", "\ufeff" + csv_text([flatten_guideline(g) for g in visible_guidance]),
                       file_name="hfpef_guidance.csv", mime="text/csv; charset=utf-8", disabled=not visible_guidance)

with tab_discovery:
    st.subheader("New HFpEF publications awaiting screening")
    st.warning("These are bibliographic candidates, not independently verified clinical trials. Protocols, follow-ups and subgroup analyses may relate to existing studies; no efficacy claims are auto-extracted.")
    query = st.text_input("Search literature candidates", placeholder="e.g., exercise, shunt, tirzepatide", key="dsearch")
    types = st.multiselect("Candidate publication type", sorted({r["publication_type"] for r in candidates}), key="dtype")
    visible = [r for r in candidates if (not query or query.casefold() in json.dumps(r).casefold())
               and (not types or r["publication_type"] in types)]
    st.caption(f"{len(visible)} of {len(candidates)} source-linked citations; clinical eligibility and outcome extraction pending")
    if visible:
        st.dataframe(pd.DataFrame(visible)[["title", "year", "publication_type", "journal", "pmid", "nct_id", "url", "discovery_status"]],
                     hide_index=True, use_container_width=True, column_config={"url": st.column_config.LinkColumn("Primary source")})
        st.download_button("Download candidates (CSV)", "\ufeff" + csv_text(visible),
                           file_name="hfpef_discovery_candidates.csv", mime="text/csv; charset=utf-8")
    st.caption("Source: PubMed and ClinicalTrials.gov metadata. The discovery queue is not a validated clinical evidence dataset; see docs/DISCOVERY_METHODS.md.")
    st.markdown("#### Title-level triage (machine-generated, not final eligibility)")
    triage_file = Path(__file__).resolve().parent / "data" / "triage_queue.csv"
    if triage_file.exists():
        triage_df = pd.read_csv(triage_file).fillna("")
        p_opts = sorted(triage_df["priority_for_abstract_review"].unique().tolist())
        priority = st.selectbox("Review priority", ["All"] + p_opts, key="triage_priority")
        if priority != "All":
            triage_df = triage_df[triage_df["priority_for_abstract_review"] == priority]
        st.caption("These are search-priority and parent-trial hints only; no automatic inclusion, exclusions, or clinical verification.")
        st.dataframe(triage_df[["title", "proposed_record_type", "title_relevance_flag", "possible_parent_trial", "url"]],
                     hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("Original source")})
        st.download_button("Download provisional triage (CSV)", triage_df.to_csv(index=False),
                           file_name="hfpef_title_triage.csv", mime="text/csv", key="triage_csv")
    else:
        st.caption("Run python scripts/triage_candidates.py to generate title-level triage.")
    st.caption("Ten separate source-linked, abstract-only extraction drafts are available in data/abstract_extraction_drafts.csv; none have independent full-text verification.")

with tab_audit:
    st.subheader("Source extraction & quality dashboard")
    st.write("This dashboard reports metadata completeness and review status. A valid DOI or PMID does **not** establish that every clinical claim has been independently verified.")
    n_original = sum(1 for s in studies if s['reference'].get('clinicaltrials_id'))
    n_numeric = sum(1 for s in studies if all(o['effect_estimate'] is not None for o in s['primary_outcomes']))
    n_second = sum(1 for s in studies if s['curation'].get('second_reviewer'))
    k1,k2,k3 = st.columns(3)
    k1.metric("Trials with NCT IDs recorded", f"{n_original}/{len(studies)}")
    k2.metric("Trials with numeric effects extracted for all primaries", f"{n_numeric}/{len(studies)}")
    k3.metric("Trials independently double-checked", f"{n_second}/{len(studies)}")
    st.warning("**Review pending:** original source bibliographic metadata and selected abstract findings were checked; independent full-text extraction, protocol reconciliation, risk-of-bias appraisal, and expert adjudication have not been completed.")
    review_rows = [
        {"Study": s['acronym'], "PMID": s['reference']['pmid'], "NCT": s['reference'].get('clinicaltrials_id') or 'Not recorded',
         "Number of primary endpoints": len(s['primary_outcomes']), "Review status": s['curation']['verification_status']}
        for s in studies
    ]
    st.dataframe(pd.DataFrame(review_rows), hide_index=True, use_container_width=True)
    st.download_button("Download full 25-record evidence index", "\ufeff" + csv_text(
        [flatten_study(s) for s in studies] + [flatten_guideline(g) for g in guidance]
    ), file_name="hfpef_evidence_index.csv", mime="text/csv; charset=utf-8")

with tab_about:
    st.subheader("Methods, scope & planned review")
    st.markdown(
        """
        **Purpose.** Provide a transparent starting point for organizing landmark HFpEF trial evidence and selected publicly indexed guidance, as proposed in the November 2026 mentor plan.\n\n
        **Selection.** The initial records were purposefully selected to span major trial eras, clinical outcomes, symptom/functional endpoints, and positive and neutral findings. **No comprehensive systematic search or PRISMA screening was conducted.**\n\n
        **Sources.** Original PubMed trial reports, ClinicalTrials.gov when a confirmed ID is available, and published guideline bibliographic records. The canonical database is `data/studies.json` plus `data/guidelines.json`, with committed CSV snapshots regenerated by `python scripts/export_csv.py`.\n\n
        **Evidence caution.** EF eligibility differs widely (>40%, ≥45%, ≥50%, or non-numeric historical criteria). Subgroups mentioned in a study are not proof of subgroup efficacy. Endpoints such as KCCQ scores, HF hospitalization, NT-proBNP, exercise capacity, and event-rate composites cannot be directly combined without a defined synthesis method.\n\n
        **Next review steps.** For every publication: compare data against full text, protocol and supplement; log exact inclusion criteria, comparator and endpoint definition; independently extract primary numerical estimates; adjudicate disagreements; document risk of bias and review dates; then seek clinician feedback.\n\n
        **Licensing and research integrity.** Public site content is original concise paraphrase with links to primary publications. Do not upload patient-level or confidential data.\n\n
        **Software.** Built in Python with Streamlit; source code and editable JSON are stored on GitHub. The earlier static HTML/JS prototype remains available independently on GitHub Pages.\n        """
    )
