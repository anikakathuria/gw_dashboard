import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import json
from datetime import datetime
from util.plot_overview import plot_overview
from util.plot_time_trends import plot_time_trends
from util.plot_ratios import plot_green_ratio

# Load data
codebook_path = "data/1_codebook.json"
data_path = "data/4_17_25_all_organic_posts.csv"
channel_mapping_path = "data/channel_mapping.csv"

# Load channel mapping
channel_mapping = pd.read_csv(channel_mapping_path)

green_brown_colors = {
    "Green": "#5a8c5a",
    "green": "#5a8c5a",
    "Fossil": "#8b5b4b",
    "brown": "#8b5b4b",
    "green_brown": "#a7caa0",
    "misc": "#4DBBD5",
    "More brown\n than green": "#A0522D",
    "More green\nthan brown": "#4E9F3D"
}

classification_labels = {
    "green": "Green",
    "brown": "Brown",
    "green_brown": "Green + Brown",
    "misc": "Miscellaneous"
}

with open(codebook_path, "r") as f:
    codebook = json.load(f)

# Load and preprocess data
data = pd.read_csv(data_path)

# Remove duplicates in channel_mapping to avoid Cartesian product during merge
channel_mapping = channel_mapping.drop_duplicates(subset=['channel_name'])

# Merge with channel mapping to get company information
data = data.merge(channel_mapping[['channel_name', 'entity']], on='channel_name', how='left')
data = data.rename(columns={'entity': 'company'})


# Split the "y_pred" column into individual binary fields
fields = ["fossil_fuel", "primary_product", "petrochemical_product", "ff_infrastructure_production", 
          "green", "renewable_energy", "emissions_reduction", "false_solutions", "recycling"]

# Create new columns for each field
y_pred_split = data["y_pred"].str.split(",", expand=True)
for i, field in enumerate(fields):
    data[field] = y_pred_split[i].astype(int)

# Add "misc" field
data["misc"] = (data[fields].sum(axis=1) == 0).astype(int)

# Add "green_message" field
data["green_message"] = ((data["green"] == 1) & 
                         (data[["renewable_energy", "emissions_reduction", "false_solutions", "recycling"]].sum(axis=1) == 0)).astype(int)
data['published_at'] = pd.to_datetime(data['published_at'])
data["title"] = pd.NA
print(f"Length before removing duplicates: {len(data)}")
data = data.drop_duplicates(subset=["post_body_text"])
print(f"Length after removing duplicates: {len(data)}")
data["engagement"] = pd.NA
print(data.columns)

def classify_greenwashing(row):
    if row['green'] and row['fossil_fuel']:
        return "green_brown"
    elif row['green']:
        return "green"
    elif row['fossil_fuel']:
        return "brown"
    else:
        return "misc"

data["green_brown"] = data.apply(classify_greenwashing, axis=1)
data["year"] = pd.to_datetime(data["published_at"]).dt.year

# Initialize Dash app with custom styles
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
    ]
)

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Inter', sans-serif;
                margin: 0;
                background-color: #f0f2f5;
                padding-top: 64px;
            }
            .banner {
                background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
                color: white;
                padding: 16px 24px;
                text-align: center;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                height: 64px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-sizing: border-box;
            }
            .sidebar {
                width: 300px;
                position: fixed;
                height: calc(100vh - 64px);
                padding: 24px;
                background-color: white;
                border-right: 1px solid #eee;
                left: 0;
                top: 64px;
                box-sizing: border-box;
                overflow-y: auto;
                z-index: 900;
            }
            .main-content {
                margin-left: 300px;
                padding: 24px;
            }
            .posts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 16px;
                padding: 16px;
            }
            .social-post {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                overflow: hidden;
                transition: transform 0.2s;
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .social-post:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .post-header {
                padding: 12px 16px;
                border-bottom: 1px solid #eee;
                background-color: #000000;
            }
            .post-date {
                font-size: 12px;
                color: #666;
                margin-top: 4px;
            }
            .post-content {
                padding: 16px;
                flex-grow: 1;
            }
            .post-text {
                max-height: 100px;
                position: relative;
            }
            .tooltip-wrapper {
                position: relative;
                display: inline-block;
            }
            .simple-tooltip {
                visibility: hidden;
                opacity: 0;
                position: absolute;
                top: 100%;
                left: 0;
                background: #333;
                color: #fff;
                padding: 10px;
                border-radius: 4px;
                width: 300px;
                overflow-y: auto;
                white-space: pre-wrap;
                z-index: 1000;
                transition: opacity 0.3s ease;
            }
            .comparison-title {
                background: white;
                border-radius: 8px;
                padding: 8px 16px;
                margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                font-size: 18px;
                font-weight: 600;
                color: #1a237e;
                text-align: center;
                border: 2px solid #e0e0e0;
            }
            .post-count {
                background: white;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                font-size: 14px;
                color: #666;
                display: inline-block;
            }
            .post-count strong {
                color: #1a237e;
                font-weight: 600;
            }
            .tooltip-wrapper:hover .simple-tooltip {
                visibility: visible;
                opacity: 1;
            }
            .post-footer {
                padding: 12px 16px;
                background: #fafafa;
                border-top: 1px solid #eee;
            }
            .engagement-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                background: #e3f2fd;
                color: #1976d2;
            }
            .platform-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                background: #f3e5f5;
                color: #7b1fa2;
                margin-left: 8px;
            }
            .classification-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 8px;
            }
            .classification-green { background: #5a8c5a; color: #000000; }
            .classification-brown { background: #8b5b4b; color: #000000; }
            .classification-green_brown { background: #a7caa0; color: #000000; }
            .classification-misc { background: #4DBBD5; color: #000000; }
            .pagination-button {
                background: white;
                border: 1px solid #ddd;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 0 4px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .pagination-button:hover:not(:disabled) {
                background: #f5f5f5;
            }
            .pagination-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .analytics-container {
                padding: 24px;
            }
            .analytics-section {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                margin-bottom: 24px;
                padding: 20px;
            }
            .analytics-header {
                color: #1a237e;
                font-weight: 600;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #eee;
            }
            .analytics-description {
                color: #666;
                margin-bottom: 20px;
                font-size: 14px;
                line-height: 1.6;
            }
            .DateRangePickerInput {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 100%;
            }
            .DateInput {
                width: 50%;
            }
            .DateInput_input {
                font-size: 14px;
                padding: 8px;
                border: none;
            }
            .DateRangePickerInput_arrow {
                padding: 0 8px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Banner
banner = html.Div("Climate Discourse Observatory", className="banner")

# Sidebar (filters, independent of tabs)
sidebar = html.Div(id="dynamic_sidebar", className="sidebar")

# Main content layout
content_layout = html.Div([
    dcc.Tabs(
        id="tabs",
        value="social_media",
        children=[
            dcc.Tab(
                label="Post Feed",
                value="social_media",
                style={
                    "padding": "12px 24px",
                    "font-weight": "500"
                }
            ),
            dcc.Tab(
                label="Analytics",
                value="analytics",
                style={
                    "padding": "12px 24px",
                    "font-weight": "500"
                }
            )
        ],
        style={
            "margin-bottom": "24px"
        }
    ),
    html.Div(id='content')
])

app.layout = html.Div([
    banner,
    sidebar,
    html.Div([content_layout], className="main-content"),
    dcc.Store(id='current_page', data=0)
])

def format_date(date_str):
    date = pd.to_datetime(date_str)
    return date.strftime("%B %d, %Y")

def create_post_component(row):
    classification_class = f"classification-{row['green_brown']}"
    border_color = green_brown_colors.get(row['green_brown'], "#ddd")
    return html.Div([
        html.Div([
            html.H4(row['channel_name'], style={
                "margin": "0",
                "font-size": "16px",
                "font-weight": "600",
                "color": "#1a237e",
            }),
            html.Div(format_date(row['published_at']), className="post-date")
        ], className="post-header", style={"background-color": f"{border_color}"}), 
        html.Div([
            html.H5(row['title'] if pd.notna(row['title']) else "", style={
                "margin": "0 0 12px 0",
                "font-size": "16px",
                "font-weight": "500",
            }),
            html.Div([
                html.P(
                    (row['post_body_text'][:200]) if pd.notna(row['post_body_text']) else "",
                    className="post-preview"
                ),
                html.Div(
                    row['post_body_text'] if pd.notna(row['post_body_text']) else "",
                    className="simple-tooltip"
                )
            ], className="tooltip-wrapper", style={"position": "relative", "cursor": "pointer"}),
            html.Img(
                src=row['post_media_urls'],
                style={
                    "width": "100%",
                    "height": "200px",
                    "object-fit": "cover",
                    "border-radius": "8px",
                    "margin-bottom": "16px"
                }
            ) if pd.notna(row['post_media_urls']) else None,
        ], className="post-content"),
        html.Div([
            html.Span(f"👥 {row['engagement']:,}", className="engagement-badge"),
            html.Span(row['platform'], className="platform-badge"),
            html.Span(
                row['green_brown'].replace("_", "+").title(),
                className=f"classification-badge {classification_class}"
            )
        ], className="post-footer")
    ], className="social-post", style={"border": f"2px solid {border_color}"})

@app.callback(
    Output("dynamic_sidebar", "children"),
    [Input("tabs", "value")]
)
def update_sidebar(selected_tab):
    # Get unique companies and their channels
    companies = sorted(data['company'].unique())
    company_channels = {company: sorted(data[data['company'] == company]['channel_name'].unique()) 
                       for company in companies}

    if selected_tab == "social_media":
        return html.Div([
            html.H3("Filters", style={
                "margin-bottom": "14px",
                "color": "#1a237e",
                "font-weight": "600"
            }),
            html.Label("View", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.RadioItems(
                id="view_toggle",
                options=[
                    {"label": "Comparison View", "value": "compare_posts"},
                    {"label": "All Posts", "value": "all_posts"},
                ],
                value="compare_posts", 
                style={"margin-bottom": "20px"}
            ),
            html.Div(id="comparison_subtoggle", children=[
                html.Label("Classification 1", style={"font-weight": "300", "margin-bottom": "8px"}),
                dcc.Dropdown(
                    id="left_view",
                    options=[
                        {"label": "Green", "value": "green"},
                        {"label": "Brown", "value": "brown"},
                        {"label": "Green + Brown", "value": "green_brown"},
                        {"label": "Miscellaneous", "value": "misc"}
                    ],
                    value="green",
                    style={"margin-bottom": "20px"}
                ),
                html.Label("Classification 2", style={"font-weight": "300", "margin-bottom": "8px"}),
                dcc.Dropdown(
                    id="right_view",
                    options=[
                        {"label": "Green", "value": "green"},
                        {"label": "Brown", "value": "brown"},
                        {"label": "Green + Brown", "value": "green_brown"},
                        {"label": "Miscellaneous", "value": "misc"}
                    ],
                    value="brown",
                    style={"margin-bottom": "20px"}
                )
            ]),
            html.Label("Date Range", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.DatePickerRange(
                id='date_range',
                start_date=data['published_at'].min(),
                end_date=data['published_at'].max(),
                display_format='YYYY-MM-DD',
                style={"margin-bottom": "20px", "width": "100%"}
            ),
            html.Label("Companies", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="company_filter",
                options=[{"label": company, "value": company} for company in companies],
                multi=True,
                value=companies,  # Select all companies by default
                placeholder="Select companies",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Channels", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="entity_filter",
                options=[{"label": channel, "value": channel} 
                        for company in companies 
                        for channel in company_channels[company]],
                multi=True,
                value=[channel for channels in company_channels.values() for channel in channels],
                placeholder="Select channels",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Platforms", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="platform_filter",
                options=[{"label": platform, "value": platform} 
                        for platform in sorted(data['platform'].unique())],
                multi=True,
                value=[platform for platform in sorted(data['platform'].unique())],
                placeholder="Select platforms",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Classification", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="classification_filter",
                options=[
                    {"label": "Green", "value": "green"},
                    {"label": "Brown", "value": "brown"},
                    {"label": "Green + Brown", "value": "green_brown"},
                    {"label": "Miscellaneous", "value": "misc"}
                ],
                multi=True,
                value=["green", "brown", "green_brown", "misc"],
                placeholder="Select classifications",
                style={"margin-bottom": "20px"}
            )
        ])
    elif selected_tab == "analytics":
        return html.Div([
            html.H3("Analytics Filters", style={
                "margin-bottom": "14px",
                "color": "#1a237e",
                "font-weight": "600"
            }),
            html.Label("Date Range", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.DatePickerRange(
                id='analytics_date_range',
                start_date=data['published_at'].min(),
                end_date=data['published_at'].max(),
                display_format='YYYY-MM-DD',
                style={"margin-bottom": "20px", "width": "100%"}
            ),
            html.Label("Companies", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="analytics_company_filter",
                options=[{"label": company, "value": company} for company in companies],
                multi=True,
                value=companies,
                placeholder="Select companies",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Channels", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="analytics_entity_filter",
                options=[{"label": channel, "value": channel} 
                        for company in companies 
                        for channel in company_channels[company]],
                multi=True,
                value=[channel for channels in company_channels.values() for channel in channels],
                placeholder="Select channels",
                style={"margin-bottom": "20px"}
            ),
            html.Label("Platforms", style={"font-weight": "500", "margin-bottom": "8px"}),
            dcc.Dropdown(
                id="analytics_platform_filter",
                options=[{"label": platform, "value": platform} 
                        for platform in sorted(data['platform'].unique())],
                multi=True,
                value=[platform for platform in sorted(data['platform'].unique())],
                placeholder="Select platforms",
                style={"margin-bottom": "20px"}
            )
        ])

@app.callback(
    [Output("entity_filter", "options"),
     Output("entity_filter", "value")],
    [Input("company_filter", "value")]
)
def update_channels(selected_companies):
    if not selected_companies:
        return [], []
    
    channels = []
    for company in selected_companies:
        company_channels = data[data['company'] == company]['channel_name'].unique()
        channels.extend(company_channels)
    
    channels = sorted(channels)
    options = [{"label": channel, "value": channel} for channel in channels]
    return options, channels

@app.callback(
    [Output("analytics_entity_filter", "options"),
     Output("analytics_entity_filter", "value")],
    [Input("analytics_company_filter", "value")]
)
def update_analytics_channels(selected_companies):
    if not selected_companies:
        return [], []
    
    channels = []
    for company in selected_companies:
        company_channels = data[data['company'] == company]['channel_name'].unique()
        channels.extend(company_channels)
    
    channels = sorted(channels)
    options = [{"label": channel, "value": channel} for channel in channels]
    return options, channels

@app.callback(
    Output("content", "children"),
    [Input("tabs", "value"),
     Input('current_page', 'data'),
     Input('date_range', 'start_date'),
     Input('date_range', 'end_date'),
     Input('company_filter', 'value'),
     Input('entity_filter', 'value'),
     Input('platform_filter', 'value'),
     Input('classification_filter', 'value'),
     Input('view_toggle', 'value'),
     Input('left_view', 'value'),
     Input('right_view', 'value')]
)
def render_tab(tab_name, current_page, start_date, end_date, companies, entities, platforms, 
               classifications, view_toggle, left_view, right_view):
    filtered_data = data.copy()
    
    # Apply date filter
    if start_date and end_date:
        filtered_data = filtered_data[
            (filtered_data['published_at'] >= start_date) & 
            (filtered_data['published_at'] <= end_date)
        ]
    
    # Apply company filter
    if companies:
        filtered_data = filtered_data[filtered_data['company'].isin(companies)]
    
    # Apply entity filter
    if entities:
        filtered_data = filtered_data[filtered_data['channel_name'].isin(entities)]
    
    # Apply platform filter
    if platforms:
        filtered_data = filtered_data[filtered_data['platform'].isin(platforms)]
    
    # Apply classification filter
    if classifications:
        filtered_data = filtered_data[filtered_data['green_brown'].isin(classifications)]
    
    if tab_name == "social_media":
        posts_per_page = 12
        
        if view_toggle == "all_posts":
            # All Posts View
            start = current_page * posts_per_page
            end = start + posts_per_page
            
            posts = [create_post_component(row) for _, row in filtered_data.iloc[start:end].iterrows()]
            
            pagination_buttons = html.Div([
                html.Button(
                    '← Previous',
                    id='prev_page',
                    n_clicks=0,
                    disabled=current_page == 0,
                    className="pagination-button"
                ),
                html.Button(
                    'Next →',
                    id='next_page',
                    n_clicks=0,
                    disabled=end >= len(filtered_data),
                    className="pagination-button"
                )
            ], style={
                "text-align": "center",
                "margin-top": "32px",
                "padding-bottom": "32px"
            })
            
            post_count = html.Div([
                "Showing ",
                html.Strong(f"{min(end, len(filtered_data)) - start} of {len(filtered_data)}"),
                " total posts"
            ], className="post-count")
            
            return html.Div([
                post_count,
                html.Div(posts, className="posts-grid"),
                pagination_buttons
            ])
        
        elif view_toggle == "compare_posts":
            # Comparison View with pagination
            left_data = filtered_data[filtered_data['green_brown'] == left_view]
            right_data = filtered_data[filtered_data['green_brown'] == right_view]
            
            # Apply pagination to both sides
            start = current_page * posts_per_page
            end = start + posts_per_page
            
            left_posts = [create_post_component(row) for _, row in left_data.iloc[start:end].iterrows()]
            right_posts = [create_post_component(row) for _, row in right_data.iloc[start:end].iterrows()]
            
            max_posts = max(len(left_data), len(right_data))
            
            pagination_buttons = html.Div([
                html.Button(
                    '← Previous',
                    id='prev_page',
                    n_clicks=0,
                    disabled=current_page == 0,
                    className="pagination-button"
                ),
                html.Button(
                    'Next →',
                    id='next_page',
                    n_clicks=0,
                    disabled=end >= max_posts,
                    className="pagination-button"
                )
            ], style={
                "text-align": "center",
                "margin-top": "32px",
                "padding-bottom": "32px"
            })
            
            post_counts = html.Div([
                "Showing ",
                html.Strong(f"{min(end, len(left_data)) - start}"),
                f" of {len(left_data)} {classification_labels[left_view]} posts and ",
                html.Strong(f"{min(end, len(right_data)) - start}"),
                f" of {len(right_data)} {classification_labels[right_view]} posts"
            ], className="post-count")
            
            return html.Div([
                post_counts,
                html.Div([
                    html.Div([
                        html.H3(classification_labels[left_view], className="comparison-title"),
                        html.Div(left_posts, className="posts-grid")
                    ], style={"width": "48%", "display": "inline-block"}),
                    html.Div([
                        html.H3(classification_labels[right_view], className="comparison-title"),
                        html.Div(right_posts, className="posts-grid")
                    ], style={"width": "48%", "display": "inline-block", "margin-left": "4%"})
                ]),
                pagination_buttons
            ])
    
    elif tab_name == "analytics":
        # Generate overview plots using the Plotly-based functions
        overview_fig = plot_overview(filtered_data, codebook, green_brown_colors)
        #time_trends_fig = plot_time_trends(filtered_data, codebook, green_brown_colors)
        ratios_fig = plot_green_ratio(filtered_data, green_brown_colors)
        
        post_count = html.Div([
            "Analysis based on ",
            html.Strong(f"{len(filtered_data)}"),
            " posts"
        ], className="post-count")
        
        return html.Div([
            post_count,
            # Overview Section
            html.Div([
                html.H2("Post Classification Overview", className="analytics-header"),
                html.P(
                    "This section shows the distribution of posts across different categories. "
                    "Green posts are related to renewable energy and sustainability, while brown posts "
                    "are related to fossil fuels and carbon-intensive activities.",
                    className="analytics-description"
                ),
                dcc.Graph(
                    figure=overview_fig,
                    config={'displayModeBar': False},
                    style={"height": "700px"}
                )
            ], className="analytics-section"),
            
            # Time Trends Section
            html.Div([
                html.H2("Low Carbon Ratio", className="analytics-header"),
                html.P(
                    "description",
                    className="analytics-description"
                ),
                dcc.Graph(
                    figure=ratios_fig,
                    config={'displayModeBar': False},
                    style={"height": "700px"}
                )
            ], className="analytics-section")
        ], className="analytics-container")

@app.callback(
    Output('current_page', 'data'),
    [Input('prev_page', 'n_clicks'),
     Input('next_page', 'n_clicks')],
    [State('current_page', 'data')]
)
def update_page(prev_clicks, next_clicks, current_page):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_page
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'prev_page' and current_page > 0:
        return current_page - 1
    elif button_id == 'next_page':
        return current_page + 1
    return current_page

@app.callback(
    Output("comparison_subtoggle", "style"),
    [Input("view_toggle", "value")]
)
def toggle_comparison_controls(view_toggle):
    if view_toggle == "compare_posts":
        return {"display": "block"}
    return {"display": "none"}

if __name__ == "__main__":
    app.run_server(debug=True)