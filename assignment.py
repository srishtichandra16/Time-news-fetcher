from flask import Flask, jsonify, Response
import urllib.request
import urllib.error
from urllib.parse import urljoin
import re
import html

app = Flask(__name__)

TIME_BASE_URL = "https://time.com"


def get_html_content(url: str) -> str:
    """
    Retrieve HTML content from a URL using urllib.
    Sets a User-Agent to avoid being blocked by the website.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; MyTimeBot/1.0)"}
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def clean_html_tags(raw_text: str) -> str:
    """
    Remove HTML tags and unescape HTML entities.
    """
    text_without_tags = re.sub(r"<[^>]+>", "", raw_text, flags=re.DOTALL)
    return html.unescape(text_without_tags).strip()


def extract_time_stories(html_text: str, limit: int = 6):
    """
    Extracts TIME.com articles (with numeric IDs) and returns a list of dictionaries.
    """
    stories_list = []
    visited_links = set()

    anchor_regex = re.compile(
        r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<content>.*?)</a>',
        re.IGNORECASE | re.DOTALL
    )
    article_id_regex = re.compile(r"/\d{7,}/")

    for match in anchor_regex.finditer(html_text):
        href = match.group("href")
        content = match.group("content")

      
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = urljoin(TIME_BASE_URL, href)

        if not href.startswith(TIME_BASE_URL):
            continue
        if not article_id_regex.search(href):
            continue

        title = clean_html_tags(content)
        if not title:
            continue
        title = " ".join(title.split())

        if href not in visited_links:
            stories_list.append({"title": title, "link": href})
            visited_links.add(href)

        if len(stories_list) >= limit:
            break

    return stories_list


@app.get("/getTimeStories")
def get_stories():
    try:
        page_content = get_html_content(TIME_BASE_URL)
        stories = extract_time_stories(page_content, limit=6)

        if not stories:
            return jsonify({"error": "No stories found. Page layout may have changed."}), 502

        return jsonify(stories)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        return jsonify({"error": f"Failed to fetch Time.com: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500


@app.get("/")
def home():
    return Response(
        "Server is active. Visit /getTimeStories to get the latest 6 Time.com stories in JSON format.",
        mimetype="text/plain",
    )


if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000/getTimeStories")
    app.run(host="127.0.0.1", port=5000, debug=True)



