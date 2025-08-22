import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urljoin
import re
import html
import json

PORT = 8000
TIME_BASE_URL = "https://time.com"


def get_html_content(url: str) -> str:
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (compatible; TimeScraperBot/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def clean_html_tags(raw_text: str) -> str:
    text_without_tags = re.sub(r"<[^>]+>", "", raw_text, flags=re.DOTALL)
    return html.unescape(text_without_tags).strip()


def extract_time_stories(html_text: str, limit: int = 6):
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


class TimeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/getTimeStories":
            try:
                html_content = get_html_content(TIME_BASE_URL)
                stories = extract_time_stories(html_content)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                
               
                self.wfile.write(json.dumps(stories, indent=2).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


with socketserver.TCPServer(("", PORT), TimeHandler) as httpd:
    print(f"Server running at http://127.0.0.1:{PORT}/getTimeStories")
    httpd.serve_forever()




