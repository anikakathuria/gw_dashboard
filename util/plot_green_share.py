import pandas as pd

import plotly.express as px

def plot_green_share(labeled_data, color_scheme):
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    # 1) Convert dates & extract year
    df = labeled_data.copy()
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['year'] = df['published_at'].dt.year

    # 2) Count total vs green posts per company/year
    summary = (
        df[df['green_brown'] != 'misc']
        .groupby(['company', 'year'])
        .agg(
            total_posts=('post_id', 'count'),
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