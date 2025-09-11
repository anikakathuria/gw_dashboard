import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

def plot_green_share(labeled_data, min_years = 5):
    """
    Plot the share of green posts out of posts labelled green or fossil fuel over time for each company.
    Only companies with at least 25 green and 25 fossil posts are shown on the plot.
    
    Arguments:
        labeled_data (pd.DataFrame): DataFrame containing the labeled data with columns 'company', 'published_at', 'green_brown'.
    
    Returns:
        fig (plotly.graph_objects.Figure): Plotly figure object containing the line plot.
    """
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    df = labeled_data.copy()

    # 2) Count total vs green posts per company/year
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
    summary = summary[(summary['green_posts'] >= 25) & (summary['brown_posts'] >= 25)]
    summary['pct_green'] = (summary['green_posts'] / summary['total_posts'])*100

    # Determine which companies have >= min_years of data
    company_year_counts = summary.groupby("company")["year"].nunique()
    long_history_companies = company_year_counts[company_year_counts >= min_years].index.tolist()


    # Build traces
    traces = []
    palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    companies = summary['company'].unique()

    # Add long-history companies first
    for i, company in enumerate([c for c in companies if c in long_history_companies]):
        cd = summary[summary['company'] == company]
        color = palette[i % len(palette)]
        traces.append(go.Scatter(
            x=cd['year'],
            y=cd['pct_green'],
            mode="lines+markers",
            name=company,
            line=dict(color=color),
            visible=True,
            hovertemplate="Company: %{text}<br>Year: %{x}<br>Green Share: %{y:.2f}%<extra></extra>",
            text=[company] * len(cd),
        ))

    # Then add short-history companies
    for i, company in enumerate([c for c in companies if c not in long_history_companies]):
        cd = summary[summary['company'] == company]
        traces.append(go.Scatter(
            x=cd['year'],
            y=cd['pct_green'],
            mode="lines+markers",
            name=company,
            line=dict(color="lightgrey"),
            visible="legendonly",
            hovertemplate="Company: %{text}<br>Year: %{x}<br>Green Share: %{y:.2f}%<extra></extra>",
            text=[company] * len(cd),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        legend=dict(
            traceorder="normal",   # keep in code order
            title="Company"
        ),
        xaxis_title="Year",
        yaxis_title="Share of Green Posts (%)",
        xaxis=dict(dtick=1)
    )
    return fig