import dash
from dash import dcc, html
import pandas as pd
import json
import pathlib
import time
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
from process_data import process_data_json

"""
    This code sets up the dashboard, combining the layout, callbacks, and data processing.
    It also includes a proxy for retrieving Junkipedia's post html embeddings and displaying within the dashboard.
    The app is built using Dash, and custom CSS is located in styles/custom.css.
"""

# Load data
codebook_path = "data/codebook.json"
data_path = ""
channel_mapping_path = "data/channel_mapping.csv"

channel_mapping = pd.read_csv(channel_mapping_path)

# Load codebook
with open(codebook_path, "r") as f:
    codebook = json.load(f)

data = json.load(open(data_path))
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
    html.Div(id='_', style={'display': 'none'}),
    html.Button('← Previous', id='prev_page', n_clicks=0, style={'display': 'none'}),
    html.Button('Next →', id='next_page', n_clicks=0, style={'display': 'none'})
])

# Register callbacks
register_filter_callbacks(app, data)
register_navigation_callbacks(app)
register_content_callbacks(app, data, codebook, green_brown_colors, classification_labels)

# ---------- Junkipedia proxy (persistent + conditional cache + highlighter) ----------

CACHE_DIR = pathlib.Path("/tmp/junkipedia_proxy_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TTL_SECONDS = 60 * 60 * 24  # 24h
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 15
MAX_RETRIES = 2
BASE_URL = "https://www.junkipedia.org"
POST_URL = BASE_URL + "/posts/{post_id}"
HL_PLACEHOLDER = "__HL_PLACEHOLDER__"  # token replaced at serve-time

# Global session w/ retries and pooling
_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=10, pool_maxsize=20, max_retries=MAX_RETRIES
)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


def _paths_for(post_id: str):
    safe = "".join(c for c in post_id if c.isalnum() or c in ("-", "_"))
    body = CACHE_DIR / f"{safe}.html"
    meta = CACHE_DIR / f"{safe}.json"
    return body, meta


def _load_cache(post_id: str):
    body_path, meta_path = _paths_for(post_id)
    if not body_path.exists():
        return None, None
    try:
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    except Exception:
        meta = {}
    try:
        html_template = body_path.read_text()
    except Exception:
        html_template = None
    return html_template, meta


def _save_cache(post_id: str, html_template: str, meta: dict):
    body_path, meta_path = _paths_for(post_id)
    try:
        body_path.write_text(html_template)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False))
    except Exception:
        # Best-effort cache; failures shouldn't break the request
        pass


def _stale(meta: dict) -> bool:
    fetched_at = meta.get("fetched_at", 0)
    return (time.time() - fetched_at) > TTL_SECONDS


def _build_processed_html(resp_text: str, post_id: str) -> str:
    """
    Build a minimal embed HTML for the Junkipedia post list containing this post.
    The result contains a placeholder token for the highlight term that is replaced
    at serve-time so the disk cache does not fragment by hl value.
    """
    try:
        soup = BeautifulSoup(resp_text, "lxml")
    except Exception:
        soup = BeautifulSoup(resp_text, "html.parser")

    head = soup.head or soup.new_tag("head")
    if not soup.head:
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)

    # base href to fix relative URLs
    base = soup.new_tag("base", href=BASE_URL + "/")
    head.insert(0, base)

    # Normalize href/src pointing to root
    for tag in head.find_all(["link", "script"]):
        if tag.has_attr("href") and isinstance(tag["href"], str) and tag["href"].startswith("/"):
            tag["href"] = BASE_URL + tag["href"]
        if tag.has_attr("src") and isinstance(tag["src"], str) and tag["src"].startswith("/"):
            tag["src"] = BASE_URL + tag["src"]

    # CSS
    style = soup.new_tag("style")
    style.string = """
      html, body { margin:0; padding:0; height:100%; overflow:hidden; background:transparent; }
      * { scrollbar-width: none; } *::-webkit-scrollbar { display: none; }
      .embedded-post-wrapper { width:100%; max-width:100%; overflow:hidden; padding-left:10px; box-sizing:border-box; }
      .embedded-post-wrapper > * { max-width:100%; box-sizing:border-box; }
      mark { background: #ffea94; color: inherit; padding: 0 .1em; border-radius: .15em; }
    """
    head.append(style)

    # JS highlighter: uses HL_PLACEHOLDER at build time; replaced when serving
    script = soup.new_tag("script")
    script.string = f"""
      (function(){{
        function escapeRegExp(s){{return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&');}}
        function highlight(term){{
          if(!term || !term.trim()) return;
          var rx = new RegExp(escapeRegExp(term), 'gi');
          var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
          var nodes=[], n;
          while(n = walker.nextNode()) {{
            var p = n.parentNode;
            if(!p) continue;
            var tag = p.nodeName;
            if(tag==='SCRIPT'||tag==='STYLE'||tag==='NOSCRIPT'||tag==='IFRAME') continue;
            if(n.nodeValue && rx.test(n.nodeValue)) nodes.push(n);
          }}
          nodes.forEach(function(text){{
            var span = document.createElement('span');
            var html = text.nodeValue.replace(rx, function(m){{ return '<mark>'+m+'</mark>'; }});
            span.innerHTML = html;
            text.parentNode.replaceChild(span, text);
          }});
        }}
        document.addEventListener('DOMContentLoaded', function(){{
          // This gets replaced to a JSON string or 'null' at serve-time:
          var term = {HL_PLACEHOLDER};
          if(!term){{
            try {{ term = new URLSearchParams(location.search).get('hl'); }} catch(_){{
              term = null;
            }}
          }}
          if(term) highlight(term);
        }});
      }})();
    """
    head.append(script)

    head_html = str(head)

    # Keep only the matching post
    outer_list = soup.find_all("div", {"data-controller": "posts"})
    if not outer_list:
        outer = soup.body or soup
    else:
        outer = outer_list[0]
        for item in outer.select("div.post-item"):
            if not item.select_one(f"a[href$='/posts/{post_id}']"):
                item.decompose()

    body_html = f'<div class="embedded-post-wrapper">{str(outer)}</div>'

    return f"""<!DOCTYPE html>
<html>
  {head_html}
  <body style="margin:0;padding:0;display:flex;justify-content:center;overflow:hidden;">
    {body_html}
  </body>
</html>
"""


def _revalidate_from_origin(post_id: str, cached_meta: dict):
    """
    Fetch from origin using ETag/Last-Modified when possible; return (html_template, status, new_meta).
    The html includes HL_PLACEHOLDER (not an inlined term) to keep the cache generic.
    """
    headers = {}
    if cached_meta:
        if cached_meta.get("etag"):
            headers["If-None-Match"] = cached_meta["etag"]
        if cached_meta.get("last_modified"):
            headers["If-Modified-Since"] = cached_meta["last_modified"]

    url = POST_URL.format(post_id=post_id)
    r = _session.get(url, headers=headers, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    if r.status_code == 304:
        new_meta = dict(cached_meta or {})
        new_meta["fetched_at"] = time.time()
        return None, 304, new_meta

    if r.status_code != 200:
        return None, r.status_code, cached_meta or {}

    html_template = _build_processed_html(r.text, post_id)
    new_meta = {
        "fetched_at": time.time(),
        "etag": r.headers.get("ETag"),
        "last_modified": r.headers.get("Last-Modified"),
    }
    return html_template, 200, new_meta


def _finalize_for_term(html_template: str, highlight_term: str) -> str:
    """
    Replace the HL placeholder with a safe JSON string representing the term,
    or 'null' when no term is provided.
    """
    term_js = json.dumps(highlight_term) if highlight_term else 'null'
    return html_template.replace(HL_PLACEHOLDER, term_js)


def fetch_junkipedia_post_html(post_id: str, highlight_term: str):
    """
    Fast, persistent, conditional-cached proxy.
    Returns (html:str|None, status:int).
    Caches a template HTML with a placeholder for highlight term.
    """
    cached_html_tmpl, cached_meta = _load_cache(post_id)

    # Serve fresh cache immediately
    if cached_html_tmpl and cached_meta and not _stale(cached_meta):
        return _finalize_for_term(cached_html_tmpl, highlight_term), 200

    # Revalidate with origin
    try:
        html_tmpl, status, new_meta = _revalidate_from_origin(post_id, cached_meta)
        if status == 304 and cached_html_tmpl:
            _save_cache(post_id, cached_html_tmpl, new_meta)
            return _finalize_for_term(cached_html_tmpl, highlight_term), 200
        if status == 200 and html_tmpl:
            _save_cache(post_id, html_tmpl, new_meta)
            return _finalize_for_term(html_tmpl, highlight_term), 200
        # Non-200/304: fall back to stale if available
        if cached_html_tmpl:
            return _finalize_for_term(cached_html_tmpl, highlight_term), 200
        return None, status
    except Exception:
        if cached_html_tmpl:
            return _finalize_for_term(cached_html_tmpl, highlight_term), 200
        return None, 502


@app.server.route('/junkipedia_proxy/<post_id>')
def junkipedia_proxy(post_id):
    # Read ?hl=... from the iframe URL; pass it along (optional)
    hl = request.args.get('hl')
    html_out, status = fetch_junkipedia_post_html(post_id, highlight_term=hl)
    if html_out is None:
        return Response("Unable to load post.", status=status)
    resp = Response(html_out, content_type='text/html', status=200)
    # Encourage browser/CDN caching; responses vary by query string (hl), which is OK.
    resp.headers["Cache-Control"] = f"public, max-age={TTL_SECONDS}"
    return resp


if __name__ == "__main__":
    app.run(debug=True)
