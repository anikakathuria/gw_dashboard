from dash import html, dcc

# Defines content layout, organizing the three tabs
content_layout = html.Div([
    dcc.Tabs(
        id="tabs",
        value="social_media",
        children=[
            dcc.Tab(label="Post Feed", value="social_media", style={"padding": "12px 24px", "font-weight": "500"}),
            dcc.Tab(label="Analytics", value="analytics", style={"padding": "12px 24px", "font-weight": "500"}),
            dcc.Tab(label="About", value="about", style={"padding": "12px 24px", "font-weight": "500"})
        ], style={"margin-bottom": "24px"}
    ),
    html.Div(id='content')
])
