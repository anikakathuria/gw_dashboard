import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def _shorten_and_wrap(raw_label: str, max_line_len: int = 14) -> str:
    """
    Take something like 'Green (Sub-Label) - Decreasing Emissions'
    → 'Decreasing Emissions', then insert '\n' to softly wrap.
    """
    if not raw_label:
        return ""
    # Take the part after the last ' - ' if present
    parts = [p.strip() for p in raw_label.split(' - ')]
    core = parts[-1] if parts else raw_label.strip()

    # Soft wrap to ~max_line_len per line
    words = core.split()
    lines, cur = [], []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_line_len:
            cur.append(w)
            cur_len += len(w) + (1 if cur_len else 0)
        else:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return '\n'.join(lines)


def _map_super_category(cat_id: str) -> str:
    """
    Map new primary IDs to legacy super-category labels for plotting/colors.
    """
    mapping = {
        "green_messaging": "Green",
        "fossil_fuel_messaging": "Fossil",
        "other_messaging": "Other",
    }
    return mapping.get(cat_id, cat_id or "Other")


def extract_labels(codebook: dict):
    """
    NEW adapter for the new codebook structure.
    Builds the same records your plotting pipeline expects:
    [{'label': <df_col>, 'super_category': 'Green'|'Fossil'|'Other',
      'multiline_category': <wrapped short label>}]
    """
    records = []
    for cat in codebook.get("categories", []):  # top-level categories
        super_cat = _map_super_category(cat.get("id", ""))
        for sub in cat.get("subcategories", []):
            df_col = sub.get("id")  # machine-friendly: becomes DataFrame column name
            display = sub.get("label")  # human-friendly: long text
            if not df_col:
                continue
            records.append({
                "label": df_col,
                "super_category": super_cat,
                "multiline_category": _shorten_and_wrap(display),
            })
    return records

def prepare_proportions(df, codebook):
    labels_info = extract_labels(codebook)
    labels_df = pd.DataFrame(labels_info)

    # Only keep labels that actually exist in df
    available = [c for c in labels_df["label"].tolist() if c in df.columns]
    labels_df = labels_df[labels_df["label"].isin(available)]

    df_long = df[['id'] + available].melt(
        id_vars='id', value_vars=available, var_name='label', value_name='value'
    )
    agg = (
        df_long.groupby('label')
        .agg(n=('value', 'sum'), total=('value', 'count'))
        .reset_index()
    )
    agg['not_that'] = agg['total'] - agg['n']
    agg = agg.merge(labels_df, on='label')

    # Within-super share
    group_totals = agg.groupby('super_category')['n'].transform('sum')
    agg['share'] = agg['n'] / group_totals.replace(0, np.nan)
    agg['share'] = agg['share'].fillna(0)

    agg['percent_label'] = (agg['share'] * 100).round(1).astype(str) + '%'
    return agg


def plot_labels(proportions, color_scheme, y_max):
    # work on a copy
    df = proportions.copy()
    super_cat = df['super_category'].iat[0]

    fig = px.bar(
        df,
        x='multiline_category',
        y='n',
        color='super_category',
        color_discrete_map=color_scheme
    )
    fig.update_layout(
        barmode='stack',
        xaxis={'categoryorder': 'total ascending'}
    )
    fig.update_yaxes(range=[0, y_max])

    # truncate long labels
    max_label_length = 10
    fig.update_xaxes(
        tickvals=df['multiline_category'],
        ticktext=[
            lbl if len(lbl) <= max_label_length else lbl[:max_label_length] + '...'
            for lbl in df['multiline_category']
        ]
    )

    # inject only the within‐super share (0–1) and format as percent
    fig.update_traces(
        customdata=df['share'].values.reshape(-1, 1),
        hovertemplate=(
            "%{y} posts<br>"
            "%{customdata[0]:.1%} of " + super_cat + " Posts<extra></extra>"
        )
    )

    return fig


def plot_green_brown(df, color_scheme):
    import plotly.express as px

    # Prepare the data
    green_brown_counts = df['green_brown'].value_counts().reset_index()
    green_brown_counts.columns = ['green_brown', 'n']
    green_brown_counts['share'] = green_brown_counts['n'] / green_brown_counts['n'].sum()
    # Map categories to nice labels
    category_labels = {
        'green': 'Only Green',
        'brown': 'Only Fossil',
        'misc': 'Miscellaneous',
        'green_brown': 'Green+Fossil'
    }
    green_brown_counts['green_brown'] = green_brown_counts['green_brown'].map(category_labels)
    green_brown_counts['label'] = green_brown_counts['green_brown'] + ' (' + (green_brown_counts['share'] * 100).round().astype(int).astype(str) + '%)'

    # Set the same x value for all rows (to get one bar)
    green_brown_counts['category'] = 'All Posts'

    # Map to custom colors
    color_discrete_map = {
        'Only Green': color_scheme['green'],
        'Only Fossil': color_scheme['brown'],
        'Miscellaneous': color_scheme['misc'],
        'Green+Fossil': color_scheme['green_brown']
    }

    # Plot single stacked bar
    fig = px.bar(
        green_brown_counts,
        x='category',
        y='share',
        color='green_brown',
        text='label',
        color_discrete_map=color_discrete_map,
        custom_data=['green_brown']
    )

    fig.update_layout(
        barmode='stack',
        yaxis=dict(
            title='Proportion',
            tickformat='.0%',
            range=[0, 1]
        ),
        xaxis_title='',
        title='Totals',
        showlegend=True
    )

    fig.update_traces(
        textposition='inside',
        hovertemplate='%{customdata[0]}: %{y:.0%}<extra></extra>',
    )

    return fig


def plot_overview(labeled_data, codebook, color_scheme):
    total_posts = len(labeled_data)-1
    
    labeled_data['green_brown'] = labeled_data.apply(lambda row: 'green_brown' if row['green'] and row['fossil_fuel'] else 'green' if row['green'] else 'brown' if row['fossil_fuel'] else 'misc', axis=1)
    
    label_proportions = prepare_proportions(labeled_data, codebook)
    
    green_proportions = label_proportions[label_proportions['super_category'] == 'Green']
    brown_proportions = label_proportions[label_proportions['super_category'] == 'Fossil']
    
    max_n = max(green_proportions['n'].max(), brown_proportions['n'].max())
    y_max = int(max_n * 1.1)
    
    green_plot = plot_labels(green_proportions, color_scheme, y_max)
    brown_plot = plot_labels(brown_proportions, color_scheme, y_max)
    green_brown_plot = plot_green_brown(labeled_data, color_scheme)
    
    # Combine the plots using make_subplots
    fig = make_subplots(rows=1, cols=3, subplot_titles=("Total Proportions", "All Green Posts", "All Fossil Posts"), column_widths=[0.33, 0.33,0.33])
    
    for trace in green_brown_plot['data']:
        fig.add_trace(trace, row=1, col=1)
    
    for trace in green_plot['data']:
        fig.add_trace(trace, row=1, col=2)
    
    for trace in brown_plot['data']:
        fig.add_trace(trace, row=1, col=3)
    
    fig.update_layout(height=600, showlegend=False, barmode='stack')
    fig.update_yaxes(range=[0, y_max], row=1, col=2)
    fig.update_yaxes(range=[0, y_max], row=1, col=3)
    fig.update_yaxes(showticklabels=False, title='', row=1, col=1)
    
    return fig