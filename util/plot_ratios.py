import pandas as pd
import plotly.express as px

def plot_green_ratio(labeled_data, color_scheme, ratios_csv_path='data/low_carbon_ratios.csv'):
    # 1) Convert dates & extract year
    df = labeled_data.copy()
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['year'] = df['published_at'].dt.year

    # 2) Count total vs green posts per company/year
    summary = (
        df
        .groupby(['company', 'year'])
        .agg(
            total_posts=('post_id', 'count'),
            green_posts=('green', 'sum')
        )
        .reset_index()
    )
    summary['pct_green'] = summary['green_posts'] / summary['total_posts']

    # 3) Load low‑carbon ratios & merge
    ratios = pd.read_csv(ratios_csv_path)
    ratios['year'] = ratios['year'].astype(int)
    merged = summary.merge(ratios, on=['company', 'year'], how='left')

    # 4) Compute ratio
    merged['green_ratio'] = merged['pct_green'] / merged['low_carbon_ratio']

    # 5) Build line‐plot and return
    fig = px.line(
        merged,
        x='year',
        y='green_ratio',
        color='company',
        markers=True,
        color_discrete_map=color_scheme,
        labels={
            'green_ratio': '(% Green Posts) ÷ Low‑Carbon Ratio',
            'year': 'Year'
        },
        title='Green‑Post to Low Carbon Investment Ratio Over Time'
    )
    fig.update_layout(legend_title_text='Company', xaxis=dict(dtick=1))
    return fig
