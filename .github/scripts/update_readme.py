"""Refresh the "Latest Writing" block in README.md from davireis.com's RSS feed.

The block always gets today's date, so the daily workflow has something to
commit even when no new post was published. If the feed can't be fetched,
the current post list is kept as is.
"""
import datetime as dt
import email.utils
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

FEED_URL = "https://davireis.com/blog/feed.xml"
README = pathlib.Path(__file__).resolve().parents[2] / "README.md"
START, END = "<!-- LATEST-WRITING:START -->", "<!-- LATEST-WRITING:END -->"
MAX_POSTS = 3


def fetch_posts():
    request = urllib.request.Request(FEED_URL, headers={"User-Agent": "DaviReisVieira profile README"})
    with urllib.request.urlopen(request, timeout=20) as response:
        channel = ET.fromstring(response.read()).find("channel")
    posts = []
    for item in channel.findall("item")[:MAX_POSTS]:
        published = email.utils.parsedate_to_datetime(item.findtext("pubDate"))
        posts.append(f"- [{item.findtext('title').strip()}]({item.findtext('link').strip()}) · {published:%b %-d, %Y}")
    return posts


def main():
    readme = README.read_text()
    current = re.search(re.escape(START) + r"\n(.*?)" + re.escape(END), readme, re.S)
    if not current:
        raise SystemExit("README is missing the LATEST-WRITING markers")

    try:
        posts = fetch_posts()
    except Exception as error:  # keep yesterday's list rather than failing the run
        print(f"Feed unavailable ({error}); keeping the current list")
        posts = [line for line in current.group(1).splitlines() if line.startswith("- ")]

    today = dt.datetime.now(dt.timezone.utc)
    block = "\n".join(posts + ["", f"<sub>Updated {today:%b %-d, %Y} · [all posts](https://davireis.com/blog)</sub>"])
    README.write_text(readme.replace(current.group(0), f"{START}\n{block}\n{END}"))


if __name__ == "__main__":
    main()
