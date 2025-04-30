from flask import Flask, Response, request
import requests

app = Flask(__name__)

JUNKIPEDIA_POST_URL = "https://www.junkipedia.org/posts/434229051"

@app.route("/")
def render_full_post():
    # Fetch the entire HTML page
    response = requests.get(JUNKIPEDIA_POST_URL)
    if response.status_code == 200:
        # Modify the HTML to ensure relative paths for CSS/JS/images are proxied
        html_content = response.text.replace(
            'href="/', 'href="/proxy?url=https://www.junkipedia.org/'
        ).replace(
            'src="/', 'src="/proxy?url=https://www.junkipedia.org/'
        )
        return Response(html_content, content_type='text/html')
    else:
        return f"Failed to load post. Status code: {response.status_code}"

@app.route("/proxy")
def proxy_resource():
    # Proxy external resources (CSS, JS, images, etc.)
    url = request.args.get("url")
    if not url:
        return "Missing URL parameter", 400

    proxied_response = requests.get(url)
    if proxied_response.status_code == 200:
        return Response(proxied_response.content, content_type=proxied_response.headers.get("Content-Type"))
    else:
        return f"Failed to fetch resource. Status code: {proxied_response.status_code}", proxied_response.status_code

if __name__ == "__main__":
    app.run(debug=True)