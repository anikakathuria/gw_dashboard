import dash
from dash import dcc, html
import pandas as pd
import json
import requests
from flask import Response, request
from bs4 import BeautifulSoup

# Import layouts
from layouts.sidebars import create_sidebars
from layouts.content import content_layout
from layouts.components import green_brown_colors, classification_labels, banner

# Import callbacks
from callbacks.filters import register_filter_callbacks
from callbacks.navigation import register_navigation_callbacks
from callbacks.content import register_content_callbacks

# Import data processing
from process_data import process_data_csv, process_data_json

"""
    This code sets up the dashboard, combining the layout, callbacks, and data processing.
    It also includes a proxy for retrieving Junkipedia's post html embeddings and displaying within the dashboard.
    The app is built using Dash, and custom CSS is located in styles/custom.css.
"""

# Load data
codebook_path = "data/codebook.json"
data_path = "data/final_greenwashing_dataset_for_dashboard_english_only.csv"
channel_mapping_path = "data/channel_mapping.csv"

channel_mapping = pd.read_csv(channel_mapping_path)

# Load codebook
with open(codebook_path, "r") as f:
    codebook = json.load(f)

# Load and preprocess data
# data = pd.read_csv(data_path)
# data = process_data_csv(data, channel_mapping)

data = json.load(open("data/dashboard_1.2_sample_english_dimensions_parententities.json"))
data = process_data_json(data)
print(f"Loaded {len(data)} posts")

# Initialize Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
    ]
)

# def print_nan_summary(df):
#     nan_counts = df.isna().sum()
#     summary = pd.DataFrame({
#         'Column': nan_counts.index,
#         'NaN Count': nan_counts.values
#     })
#     # Ensure full output is shown
#     pd.set_option('display.max_rows', None)
#     print(summary)
#     pd.reset_option('display.max_rows')

# print_nan_summary(data)

print("Number of fossil fuel posts:", (data['fossil_fuel'] == True).sum())
print(data['y_pred'].head(n=10))

# Custom CSS - Load from external file
with open('styles/custom.css', 'r') as f:
    custom_css = f.read()

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {custom_css}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

# Create sidebars with the data
social_sidebar, analytics_sidebar, about_sidebar = create_sidebars(data)

# App layout
app.layout = html.Div([
    banner,
    html.Div([about_sidebar, social_sidebar, analytics_sidebar]),
    html.Div([content_layout], className="main-content"),
    dcc.Store(id='current_page', data=0),
    # Add a hidden div for the scroll-to-top callback
    html.Div(id='_', style={'display': 'none'}),
    # Add pagination buttons to the layout but hide them initially
    # They will be shown/hidden by the content callback as needed
    html.Button('← Previous', id='prev_page', n_clicks=0, style={'display': 'none'}),
    html.Button('Next →', id='next_page', n_clicks=0, style={'display': 'none'})
])

# Register callbacks
register_filter_callbacks(app, data)
register_navigation_callbacks(app)
register_content_callbacks(app, data, codebook, green_brown_colors, classification_labels)

@app.server.route('/junkipedia_proxy/<post_id>')
def junkipedia_proxy(post_id):
    """
    Proxy for Junkipedia posts. This function fetches the post from Junkipedia and returns a minimal HTML embedding
      with the post content. This is used to display the post in an iframe.

    Arguments:
        post_id (str): The "post_id" of the post to fetch from Junkipedia.
    
    Returns:
        Response: A Flask Response object containing the HTML content of the post.
    """
    resp = requests.get(f"https://www.junkipedia.org/posts/{post_id}")
    if resp.status_code != 200:
        return Response("…", status=resp.status_code)

    soup = BeautifulSoup(resp.text, 'html.parser')

    # — 1) Grab all the original <head> tags we need —
    head = soup.head or soup.new_tag('head')

    # insert a <base> so absolute + relative URLs in CSS/JS/images resolve back to the real origin
    base = soup.new_tag('base', href="https://www.junkipedia.org/")
    head.insert(0, base)

    # turn every /… link/src into an absolute URL
    for tag in head.find_all(['link','script']):
        if tag.has_attr('href') and tag['href'].startswith('/'):
            tag['href'] = "https://www.junkipedia.org" + tag['href']
        if tag.has_attr('src') and tag['src'].startswith('/'):
            tag['src'] = "https://www.junkipedia.org" + tag['src']

    head_html = str(head)

    # — 2) Extract the full posts‐wrapper, then prune to just your one post —
    outer = soup.find_all('div', {'data-controller':'posts'})[0]
    for item in outer.select('div.post-item'):
        if not item.select_one(f"a[href$='/posts/{post_id}']"):
            item.decompose()
    body_html = str(outer)

    # — 3) Rebuild a minimal page —
    html = f"""
    <!DOCTYPE html>
    <html>
      {head_html}
      <body style="margin:0;padding:0;display:flex;justify-content:center;">
        {body_html}
      </body>
    </html>
    """
    return Response(html, content_type='text/html')

if __name__ == "__main__":
    app.run(debug=True)
    