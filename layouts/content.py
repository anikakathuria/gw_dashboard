from dash import html, dcc

# Defines content layout, organizing the three tabs
content_layout = html.Div([
    html.Div(
        id="content",
        style={
            "backgroundColor": "white",
            "padding": "24px",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.2)"
        }
    )
])
