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
    import math

    # tiny helper to choose black/white text based on bg color
    def _auto_font_color(bg_hex: str, default="white"):
        try:
            h = bg_hex.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            # relative luminance
            luminance = (0.2126 * (r/255) + 0.7152 * (g/255) + 0.0722 * (b/255))
            return "black" if luminance > 0.6 else "white"
        except Exception:
            return default

    total_posts = len(labeled_data)-1
    
    labeled_data['green_brown'] = labeled_data.apply(
        lambda row: 'green_brown' if row['green'] and row['fossil_fuel']
        else 'green' if row['green']
        else 'brown' if row['fossil_fuel']
        else 'misc',
        axis=1
    )
    
    label_proportions = prepare_proportions(labeled_data, codebook)
    
    green_proportions = label_proportions[label_proportions['super_category'] == 'Green']
    brown_proportions = label_proportions[label_proportions['super_category'] == 'Fossil']
    
    max_n = max(green_proportions['n'].max(), brown_proportions['n'].max())
    y_max = int(max_n * 1.1)
    
    # Build a compatible map for plot_labels (expects "Green"/"Fossil"/"Other")
    super_color_map = {
        "Green":  color_scheme.get("Green",  color_scheme.get("green",  "#45a776")),
        "Fossil": color_scheme.get("Fossil", color_scheme.get("brown",  "#8d6e63")),
        "Other":  color_scheme.get("Other",  color_scheme.get("misc",   "#9e9e9e")),
    }

    green_plot = plot_labels(green_proportions, super_color_map, y_max)
    brown_plot = plot_labels(brown_proportions, super_color_map, y_max)
    green_brown_plot = plot_green_brown(labeled_data, color_scheme)
    
    # Combine the plots using make_subplots (keep visible titles)
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Total Proportions", "All Green Posts", "All Fossil Posts"),
        column_widths=[0.33, 0.33, 0.33]
    )
    
    for trace in green_brown_plot['data']:
        fig.add_trace(trace, row=1, col=1)
    for trace in green_plot['data']:
        fig.add_trace(trace, row=1, col=2)
    for trace in brown_plot['data']:
        fig.add_trace(trace, row=1, col=3)
    
    fig.update_layout(hovermode='x unified')  # keep one tooltip
    fig.update_xaxes(showspikes=False)        # hide the vertical line
    fig.update_layout(height=600, showlegend=False, barmode='stack')
    fig.update_yaxes(range=[0, y_max], row=1, col=2)
    fig.update_yaxes(range=[0, y_max], row=1, col=3)
    fig.update_yaxes(showticklabels=False, title='', row=1, col=1)

    # ---------------- NEW: Hover tooltips for titles with scheme colors ----------------
    green_bg  = super_color_map["Green"]
    brown_bg  = super_color_map["Fossil"]
    green_txt = _auto_font_color(green_bg)
    brown_txt = _auto_font_color(brown_bg)

    title_tooltips = {
        "Total Proportions": {
            "text": "Stacked bar chart showing the fraction of posts labelled by CLAIMS as Only Green, <br> Only Fossil, Green+Fossil, or Miscellaneous.",
            "style": dict(bgcolor="white", font_size=12, font_color="black")  # keep neutral
        },
        "All Green Posts": {
            "text": "Bar chart showing the number of posts by Green subcategory, as labelled by CLAIMS: Emissions Reduction, <br> False Solutions, Other Green, Recycling/Waste Management, and Low-Carbon Technologies. <br> Posts assigned both Fossil Fuel and Green labels by CLAIMS indicate efforts to greenwash messaging <br> about fossil fuels, and are therefore included in this bar chart.",
            "style": dict(bgcolor=green_bg, font_size=12, font_color=green_txt)
        },
        "All Fossil Posts": {
            "text": "Bar chart showing the number of posts by Fossil Fuel subcategory, <br> as labelled by CLAIMS: Primary Product, Petrochemical Product, Other Fossil Fuel, <br> and Infrastructure & Production.",
            "style": dict(bgcolor=brown_bg, font_size=12, font_color=brown_txt)
        }
    }

    if hasattr(fig.layout, "annotations") and fig.layout.annotations:
        new_annotations = []
        for ann in fig.layout.annotations:
            a = ann.to_plotly_json()
            t = a.get("text")
            if t in title_tooltips:
                a["hovertext"] = title_tooltips[t]["text"]
                a["hoverlabel"] = title_tooltips[t]["style"]
                a["showarrow"] = False
            new_annotations.append(a)
        fig.update_layout(annotations=new_annotations)

    # (optional) keep unified hover on traces
    fig.update_layout(
        hovermode='x unified',
        hoverlabel=dict(bgcolor="white", font_size=13, font_color="black")
    )
    
    return fig


'''
def plot_overview(labeled_data, codebook, color_scheme):
    total_posts = len(labeled_data) - 1

    labeled_data['green_brown'] = labeled_data.apply(
        lambda row: 'green_brown' if row['green'] and row['fossil_fuel']
        else 'green' if row['green']
        else 'brown' if row['fossil_fuel']
        else 'misc',
        axis=1
    )

    label_proportions = prepare_proportions(labeled_data, codebook)

    green_proportions = label_proportions[label_proportions['super_category'] == 'Green']
    brown_proportions = label_proportions[label_proportions['super_category'] == 'Fossil']

    max_n = max(green_proportions['n'].max(), brown_proportions['n'].max())
    y_max = int(max_n * 1.1)

    green_plot = plot_labels(green_proportions, color_scheme, y_max)
    brown_plot = plot_labels(brown_proportions, color_scheme, y_max)
    green_brown_plot = plot_green_brown(labeled_data, color_scheme)

    # Keep subplot_titles as-is so they render visually
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Total Proportions", "All Green Posts", "All Fossil Posts"),
        column_widths=[0.33, 0.33, 0.33]
    )

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

    # ---- NEW: Add hover tooltips to the existing subplot titles ----
    # Map the exact title text to the hover content you want.
    title_tooltips = {
        "Total Proportions": "Overall distribution of post types across the dataset.",
        "All Green Posts": "Breakdown of subcategories within posts labeled as Green.",
        "All Fossil Posts": "Breakdown of subcategories within posts labeled as Fossil."
    }

    # Plotly creates the subplot titles as annotations. We enrich them with hovertext.
    if hasattr(fig.layout, "annotations") and fig.layout.annotations:
        new_annotations = []
        for ann in fig.layout.annotations:
            # Make a (shallow) copy to avoid mutating the original reference
            ann_dict = ann.to_plotly_json()
            text = ann_dict.get("text")
            if text in title_tooltips:
                ann_dict["hovertext"] = title_tooltips[text]
                # Optional styling for the hover bubble near the title
                ann_dict["hoverlabel"] = dict(bgcolor="white", font_size=12, font_color="black")
                # Tiny vertical nudge if you want more room above the plot area
                ann_dict["y"] = ann_dict.get("y", 1.0) + 0.02
                # Ensure no arrow cursor behavior needed
                ann_dict["showarrow"] = False
            new_annotations.append(ann_dict)
        fig.update_layout(annotations=new_annotations)

    # (Optional) keep your hover behavior across traces
    fig.update_layout(
        hovermode='x unified',
        hoverlabel=dict(bgcolor="white", font_size=13, font_color="black")
    )

    return fig
'''

'''
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
'''