from dash import html, dcc

# Banner component
banner = html.Div([
    html.Div("CLAIMS", style={
        "font-size": "40px",
        "font-weight": "bold",
        "color": "white",
        "text-orientation": "upright",
        "height": "10%",
        "display": "flex",
        "align-items": "left",
        "justify-content": "left",
        "padding-right": "16px",
        "margin-bottom": "3px"
    }),
    html.Div([
        html.Div("Climate Language and", style={
            "font-size": "18px",
            "font-weight": "500",
            "color": "white",
            "margin-bottom": "4px"
        }),
        html.Div("Influence Monitoring System", style={
            "font-size": "18px",
            "font-weight": "500",
            "color": "white",
            "margin-bottom": "3px"
        })
    ], style={
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "left",
        "margin-left": "16px"
    })
], className="banner", style={
    "display": "flex",
    "align-items": "left",
    "height": "10%"
})

# Main content layout
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
