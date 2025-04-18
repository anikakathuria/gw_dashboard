import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def extract_labels(codebook):
    labels = []
    for entry in codebook:
        for sub_category in entry.get('sub_categories', []):
            labels.append({
                'label': sub_category['label'],
                'super_category': entry['super_category'],
                'multiline_category': entry['multiline_category']
            })
    return labels

def prepare_proportions(df, codebook):
    # 1) turn your codebook into a DataFrame of label→meta
    labels_info = extract_labels(codebook)
    labels_df = pd.DataFrame(labels_info)
    labels = labels_df['label'].tolist()

    # 2) melt to long form & count positives per label
    df_long = df[['post_uid'] + labels].melt(
        id_vars='post_uid',
        value_vars=labels,
        var_name='label',
        value_name='value'
    )
    agg = (
        df_long
        .groupby('label')
        .agg(
            n=('value', 'sum'),
            total=('value', 'count')
        )
        .reset_index()
    )
    agg['not_that'] = agg['total'] - agg['n']

    # 3) bring in super_category (and multiline_category)
    agg = agg.merge(labels_df, on='label')

    # 4) compute share *within* each super_category
    agg['share'] = (
        agg
        .groupby('super_category')['n']
        .transform(lambda x: x / x.sum())
    )

    # 5) (optional) a human‐readable percent column
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
        'green': 'Green',
        'brown': 'Brown',
        'misc': 'Miscellaneous',
        'green_brown': 'Green+Brown'
    }
    green_brown_counts['green_brown'] = green_brown_counts['green_brown'].map(category_labels)
    green_brown_counts['label'] = green_brown_counts['green_brown'] + ' (' + (green_brown_counts['share'] * 100).round().astype(int).astype(str) + '%)'

    # Set the same x value for all rows (to get one bar)
    green_brown_counts['category'] = 'All Posts'

    # Map to custom colors
    color_discrete_map = {
        'Green': color_scheme['green'],
        'Brown': color_scheme['brown'],
        'Miscellaneous': color_scheme['misc'],
        'Green+Brown': color_scheme['green_brown']
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
        hovertemplate='%{customdata[0]}: %{y:.0%}<extra></extra>'
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
    fig = make_subplots(rows=1, cols=3, subplot_titles=("Total Proportions", "Green Posts", "Brown Posts"), column_widths=[0.33, 0.33,0.33])
    
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