import pandas as pd
import plotly.graph_objects as go
import numpy as np

def plot_combined_greenwashing_scores(
    labeled_data,
    ratios_csv_path='data/low_carbon_ratios.csv'
):
    """
    Plot the greenwashing scores for each company over time, including both raw and normalized scores.
    The plot includes buttons to toggle between a raw ratio on a linear scale, raw ratio on a log scale, and normalized score on a linear scale. 
    The greenwashing score is calculated as the ratio of green posts to total climate-relevant posts (labelled as green or brown),
      divided by the low-carbon ratio (the percentage of a company's CAPEX that was spent on low-carbon projects).
    Only companies with at least 25 green and 25 fossil fuel posts are shown on the plot.
    
    Arguments:
        labeled_data (pd.DataFrame): DataFrame containing the labeled data with columns 'company', 'year', 'green_brown'.
        ratios_csv_path (str): Path to the CSV file containing low-carbon ratios for each company and year.
    
    Returns:
        fig (plotly.graph_objects.Figure): Plotly figure object containing the line plot.

    """
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    # Convert dates & extract year
    df = labeled_data.copy()

    # Count total vs green/brown posts per company/year
    summary = (
        df[df['green_brown'] != 'misc']
        .groupby(['company', 'year'])
        .agg(
            total_posts=('id', 'count'),
            green_posts=('green', 'sum'),
            brown_posts=('fossil_fuel', 'sum')
        )
        .reset_index()
    )
    # Filter for at least 25 green and 25 brown posts
    summary = summary[(summary['green_posts'] >= 25) & (summary['brown_posts'] >= 25)]
    summary['pct_green'] = summary['green_posts'] / summary['total_posts']

    # Load low‑carbon ratios & merge
    ratios = pd.read_csv(ratios_csv_path)
    ratios['year'] = ratios['year'].astype(int)
    merged = summary.merge(ratios, on=['company', 'year'], how='left')

    # Filter out rows with no ratio data
    merged = merged.dropna(subset=['low_carbon_ratio'])

    # Compute ratios
    merged['green_ratio'] = merged['pct_green'] / merged['low_carbon_ratio']
    merged['normalized_ratio'] = (
        (merged['pct_green'] + merged['low_carbon_ratio']) /
        (merged['pct_green'] - merged['low_carbon_ratio'])
    )

    max_raw = merged['green_ratio'].max()
    max_exp = np.log10(max_raw)

    # Create traces for each company: even idx = raw, odd idx = normalized
    traces = []
    companies = merged['company'].unique()
    for i, company in enumerate(companies):
        cd = merged[merged['company'] == company]
        color = colors[i % len(colors)]
        traces.append(go.Scatter(
            x=cd['year'], y=cd['green_ratio'], name=company,
            visible=True,
            hovertemplate="Raw Score: %{y:.2f}<br>Year: %{x}<extra></extra>",
            line=dict(color=color)
        ))
        traces.append(go.Scatter(
            x=cd['year'], y=cd['normalized_ratio'], name=company,
            visible=False,
            hovertemplate="Normalized Score: %{y:.2f}<br>Year: %{x}<extra></extra>",
            line=dict(color=color)
        ))

    fig = go.Figure(data=traces)

    # Define buttons for three states: raw linear, raw log, normalized linear
    buttons = [
        dict(
            label="Raw Ratio (Linear)",
            method="update",
            args=[
                {'visible': [i % 2 == 0 for i in range(len(traces))]},
                {'yaxis': {'type': 'linear'}}
            ]
        ),
        dict(
            label="Raw Ratio (Log)",
            method="update",
            args=[
                {'visible': [i % 2 == 0 for i in range(len(traces))]},
                {'yaxis': {'type': 'log'}, 'autorange': False}
            ]
        ),
        dict(
            label="Normalized Ratio",
            method="update",
            args=[
                {'visible': [i % 2 == 1 for i in range(len(traces))]},
                {'yaxis': {'type': 'linear'}}
            ]
        )
    ]

    # Add single updatemenu
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                buttons=buttons,
                x=1.05, xanchor="left",
                y=0.7, yanchor="top"
            )
        ],
        margin=dict(t=100)
    )

    # Axis titles and legend
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Greenwashing Score",
        legend_title="Company"
    )

    return fig
