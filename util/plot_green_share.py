import pandas as pd

import plotly.express as px

def plot_green_share(labeled_data):
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

    # 3) Build line‐plot and return
    fig = px.line(
        summary,
        x='year',
        y='pct_green',
        color='company',
        markers=True,
        labels={
            'pct_green': 'Share of Green Posts (%)',
            'year': 'Year'
        },
        color_discrete_sequence=colors
    )
    fig.update_layout(legend_title_text='Company', xaxis=dict(dtick=1))
    return fig