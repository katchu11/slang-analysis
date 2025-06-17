#!/usr/bin/env python3
"""
Slang Analyzer Dashboard
Interactive Streamlit dashboard for analyzing slang terms.
"""

import streamlit as st
import asyncio
from collections import Counter
from typing import Dict, Any
import plotly.express as px

from slang_analyzer import get_api_key, analyze_with_haiku, parse_with_sonnet
import anthropic


st.set_page_config(
    page_title="WTAC - What's That Acronym, Claude?", page_icon="🤔", layout="wide"
)


def main():
    st.title("🤔 WTAC - What's That Acronym, Claude?")
    st.markdown("Discover what slang acronyms could stand for using Claude AI models")

    # Sidebar for inputs
    with st.sidebar:
        st.header("Analysis Settings")

        slang_term = (
            st.text_input(
                "Enter slang term:", value="YOLO", placeholder="e.g., YOLO, FOMO, SMH"
            )
            .upper()
            .strip()
        )

        sample_size = st.slider(
            "Sample size:",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Number of times to run the analysis (each run = 1 Haiku generation + 1 Sonnet parsing)",
        )

        analyze_button = st.button("🚀 Analyze", type="primary")

    # Main content
    if not slang_term:
        st.info("👆 Enter a slang term in the sidebar to get started!")
        return

    # Check if we have results in session state
    results_key = f"results_{slang_term}_{sample_size}"

    if analyze_button or results_key not in st.session_state:
        if analyze_button:
            # Clear previous results
            for key in list(st.session_state.keys()):
                if key.startswith("results_"):
                    del st.session_state[key]

            # Run analysis
            with st.spinner("Setting up analysis..."):
                try:
                    api_key = get_api_key()
                except Exception as e:
                    st.error(f"Error getting API key: {e}")
                    st.info("Please set your ANTHROPIC_API_KEY environment variable")
                    return

            # Run async analysis with progress
            results = run_analysis_with_progress(slang_term, sample_size, api_key)
            if results:
                st.session_state[results_key] = results
            else:
                st.error("Analysis failed. Please try again.")
                return

    # Display results if we have them
    if results_key in st.session_state:
        display_results(slang_term, st.session_state[results_key])


def run_analysis_with_progress(slang_term: str, sample_size: int, api_key: str):
    """Run the analysis with Streamlit progress bars."""

    # Create progress containers
    haiku_progress = st.progress(0)
    haiku_status = st.empty()

    sonnet_progress = st.progress(0)
    sonnet_status = st.empty()

    async def run_with_progress():
        client = anthropic.AsyncAnthropic(api_key=api_key)

        try:
            # Step 1: Haiku analysis
            haiku_status.text(
                "🎭 Claude 3.5 Haiku generating creative interpretations..."
            )
            haiku_progress.progress(0.1)

            haiku_results = await analyze_with_haiku(client, slang_term, sample_size)
            haiku_progress.progress(1.0)

            # Step 2: Sonnet parsing
            sonnet_status.text(
                "🧠 Claude 4 Sonnet parsing interpretations into structured data..."
            )
            sonnet_progress.progress(0.1)

            parsed_results = await parse_with_sonnet(client, haiku_results, slang_term)
            sonnet_progress.progress(1.0)

            return {"haiku_results": haiku_results, "parsed_results": parsed_results}

        finally:
            await client.close()

    # Run the async function
    try:
        results = asyncio.run(run_with_progress())
        haiku_status.text("✅ Haiku generation complete!")
        sonnet_status.text("✅ Sonnet parsing complete!")
        return results
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        return None


def display_results(slang_term: str, results: Dict[str, Any]):
    """Display the analysis results with interactive visualizations."""

    parsed_results = results["parsed_results"]

    # Filter valid results
    valid_results = [
        r for r in parsed_results if r.get("primary_meaning") and "error" not in r
    ]

    if not valid_results:
        st.error("No valid results to display")
        return

    # Aggregate data
    all_meanings = [r.get("primary_meaning", "") for r in valid_results]
    meaning_counts = Counter(all_meanings)

    # Letter breakdown aggregation
    letter_aggregation = {}
    for result in valid_results:
        breakdown = result.get("letter_breakdown", {})
        for letter, meaning in breakdown.items():
            if letter not in letter_aggregation:
                letter_aggregation[letter] = []
            letter_aggregation[letter].append(meaning)

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Term", slang_term)
    with col2:
        st.metric("Valid Results", len(valid_results))
    with col3:
        st.metric("Unique Interpretations", len(meaning_counts))
    with col4:
        most_common = meaning_counts.most_common(1)[0][0] if meaning_counts else "N/A"
        st.metric("Top Interpretation", "📊")
        st.caption(most_common[:30] + "..." if len(most_common) > 30 else most_common)

    st.divider()

    # Main visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🥧 Top Interpretations")

        # Create pie chart for top interpretations
        top_meanings = meaning_counts.most_common(8)  # Top 8 to avoid clutter

        if len(top_meanings) > 6:
            # Group smaller ones into "Others"
            displayed = top_meanings[:5]
            others_count = sum(count for _, count in top_meanings[5:])
            if others_count > 0:
                displayed.append(("Others", others_count))
        else:
            displayed = top_meanings

        if displayed:
            labels, values = zip(*displayed)

            fig = px.pie(
                values=values,
                names=labels,
                title=f"Distribution of {slang_term} Interpretations",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🔤 Letter Analysis")

        # Letter selector with session state key
        letters = list(slang_term.lower())
        selected_letter = st.selectbox(
            "Select letter to analyze:",
            letters,
            format_func=lambda x: f"{x.upper()} (position {letters.index(x) + 1})",
            key=f"letter_selector_{slang_term}",
        )

        if selected_letter in letter_aggregation:
            letter_meanings = letter_aggregation[selected_letter]
            letter_counts = Counter(letter_meanings)

            # Create pie chart for selected letter
            if letter_counts:
                top_letter_meanings = letter_counts.most_common(6)

                if len(top_letter_meanings) > 5:
                    displayed = top_letter_meanings[:4]
                    others_count = sum(count for _, count in top_letter_meanings[4:])
                    if others_count > 0:
                        displayed.append(("Others", others_count))
                else:
                    displayed = top_letter_meanings

                labels, values = zip(*displayed)

                fig = px.pie(
                    values=values,
                    names=labels,
                    title=f"What '{selected_letter.upper()}' stands for",
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No data available for letter '{selected_letter.upper()}'")


if __name__ == "__main__":
    main()
