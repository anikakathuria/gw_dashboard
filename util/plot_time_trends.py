import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_time_trends(labeled_data, codebook, color_scheme):
    # Convert 'published_at' to datetime

    # Determine year range for plotting
    min_year = labeled_data['attributes.published_at'].dt.year.min()
    max_year = labeled_data['attributes.published_at'].dt.year.max()
    plot_range = (min_year - 0.5, max_year + 0.5)
    year_breaks = list(range(min_year, max_year + 1))

    # Prepare data with common transformations
    df = labeled_data.copy()

    # Time trends plot
    time_green_brown = (
        df.groupby(['year', 'green_brown'])['green_brown'].count()
        .unstack(fill_value=0)
        .reset_index()
        .melt(id_vars='year', value_vars=['green', 'brown', 'misc'], var_name='green_brown', value_name='n')
        .groupby('year')
        .apply(lambda x: x.assign(total=x['n'].sum()))
        .reset_index(drop=True)
        .assign(share=lambda x: x['n'] / x['total'])
    )

    # Rename categories for the legend
    category_rename = {
        'green': 'Green',
        'brown': 'Brown',
        'misc': 'Miscellaneous',
    }
    time_green_brown['green_brown'] = time_green_brown['green_brown'].map(category_rename)

    # Update color scheme to match renamed categories
    updated_color_scheme = {
        'Green': color_scheme['green'],
        'Brown': color_scheme['brown'],
        'Miscellaneous': color_scheme['misc'],
    }

    fig_time_trends = px.bar(time_green_brown, x='year', y='share', color='green_brown', barmode='group', color_discrete_map=updated_color_scheme)
    fig_time_trends.update_layout(xaxis=dict(tickmode='array', tickvals=year_breaks), xaxis_title='Year', yaxis_title='Share')

    # Data for ratio plot and calculation of ratio
    ratio_data = (
        df.groupby(['year', 'green_brown'])['green_brown'].count()
        .unstack(fill_value=0)
        .fillna(0)
        .assign(green=lambda x: (x['green'] - x['brown']) / (x['green'] + x['brown']))
    )


    # Yearly ratio line plot
    fig_yearly_ratios = go.Figure()
    fig_yearly_ratios.add_trace(go.Scatter(
        x=ratio_data.index,
        y=ratio_data['green'],
        mode='lines+markers',
        marker=dict(color=color_scheme['green']),
        name='Yearly Green - Brown Ratio'
    ))
    fig_yearly_ratios.update_layout(xaxis=dict(tickmode='array', tickvals=year_breaks), xaxis_title='Year', yaxis_title='Green - Brown Ratio', yaxis_range=[-1, 1])

    # Combine the plots using make_subplots
    fig_combined = make_subplots(rows=2, cols=1, subplot_titles=("Time Trends", "Green - Brown Ratio"))

    for trace in fig_time_trends['data']:
        fig_combined.add_trace(trace, row=1, col=1)

    for trace in fig_yearly_ratios['data']:
        trace.showlegend = False
        fig_combined.add_trace(trace, row=2, col=1)

    fig_combined.update_layout(height=900, showlegend=True)
    fig_combined.update_yaxes(range=[-1, 1], row=2, col=1)
    
    fig_combined.add_shape(
        type='rect',
        xref='x2 domain',  # Use the second subplot's domain coordinates
        yref='y2 domain',
        x0=1,  x1=1.10,  # These values are now fractions of the subplot width (0 to 1)
        y0=0.5,   y1=1,  # These are fractions of the subplot height (0 to 1)
        fillcolor='green',
        opacity=0.5,
        layer='below',
        line_width=0
    )

    fig_combined.add_annotation(
        xref='x2 domain',  # Use the second subplot's domain coordinates
        yref='y2 domain',
        x=1.11, y=0.75,  # Just to the right of the green box
        text='More green than brown',
        showarrow=False,
        xanchor='left',
        yanchor='middle'
    )
    # 3) Add a brown box (below the green one)
    fig_combined.add_shape(
        type='rect',
        xref='x2 domain',  # Use the second subplot's domain coordinates
        yref='y2 domain',
        x0=1, x1=1.10,
        y0=0,  y1=0.5,
        fillcolor='brown',
        opacity=0.5,
        layer='above',
        line_width=0
    )

    # 4) Add annotation for the brown box
    fig_combined.add_annotation(
        xref='x2 domain',  # Use the second subplot's domain coordinates
        yref='y2 domain',
        x=1.11, y=0.25,
        text='More brown than green',
        showarrow=False,
        xanchor='left',
        yanchor='middle'
    )
    fig_combined.update_layout(
        margin=dict(r=250),  # Increase the right margin
    )

    return fig_combined