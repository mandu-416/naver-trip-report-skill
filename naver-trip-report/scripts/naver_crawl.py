"""Crawl Naver blog search, Naver blog posts, and Google results through Firecrawl.

Reads FIRECRAWL_API_KEY from the environment or from a .env file in the current
directory. Writes UTF-8 files instead of printing content, because Windows
consoles (cp949) crash on Korean text and emoji.

Usage:
  python -I naver_crawl.py search "<query>" --out DIR
  python -I naver_crawl.py posts DIR/posts.txt [--limit N] [--workers N] --out DIR

Rate limits (HTTP 429) and transient 5xx errors are retried automatically with
backoff. Avoid launching many script instances in parallel; use --workers.
  python -I naver_crawl.py google "<query>" [--limit N] --out DIR
  python -I naver_crawl.py page <url> --out DIR
  python -I naver_crawl.py prices DIR [DIR ...] --out prices.txt [--context 2]
      Pull every line that mentions a price (A$, AUD, 달러, 불, 원, $) out of the
      crawled posts, with a couple of lines before it for the item name, one
      section per post with its URL. Much faster than reading every post when
      checking shopping prices.
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.firecrawl.dev/v1"


def api_key():
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key and os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            if line.strip().startswith("FIRECRAWL_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("FIRECRAWL_API_KEY not found in environment or .env")
    return key


RETRY_STATUS = {429, 500, 502, 503, 504}


def call(endpoint, body, timeout=120, retries=5):
    """POST to Firecrawl, retrying rate limits (429) and transient 5xx errors.

    Waits for the server's Retry-After when given, otherwise backs off
    exponentially (5, 10, 20, 40, 60 s) so parallel runs don't hammer the API.
    """
    data = json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"}
    for attempt in range(retries + 1):
        req = urllib.request.Request(f"{API}/{endpoint}", data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_STATUS or attempt == retries:
                raise
            retry_after = e.headers.get("Retry-After")
            wait = int(retry_after) if retry_after and retry_after.isdigit() else min(60, 5 * 2 ** attempt)
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries:
                raise
            wait = min(60, 5 * 2 ** attempt)
        sys.stderr.write(f"retry {attempt + 1}/{retries} for {endpoint} in {wait}s\n")
        time.sleep(wait)


def scrape(url):
    d = call("scrape", {"url": url, "formats": ["markdown"], "onlyMainContent": True})
    return (d.get("data") or {}).get("markdown", "")


def clean(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)  # images
    md = re.sub(r"\]\([^)]*\)", "]", md)  # link targets
    noise = r"(재생|음소거|전체 화면|광고 후|데이터 사용료|subject|author|본문 폰트|URL복사|신고하기|공유하기)"
    lines = [l.rstrip() for l in md.split("\n") if len(l.strip()) > 2 and not re.search(noise, l)]
    return "\n".join(lines)


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def cmd_search(args):
    q = urllib.parse.quote_plus(args.query)
    md = scrape(f"https://search.naver.com/search.naver?ssc=tab.blog.all&query={q}")
    write(os.path.join(args.out, "search.md"), md)
    seen, rows = set(), []
    for title, url in re.findall(r"\[([^\]\[]{5,140})\]\((https://blog\.naver\.com/\w+/\d+)\)", md):
        if url in seen or "\\" in title:
            continue
        seen.add(url)
        rows.append(f"{url} | {title.replace('새 창 열림', '').strip()}")
    write(os.path.join(args.out, "posts.txt"), "\n".join(rows) + "\n")
    print(f"{len(rows)} posts -> {os.path.join(args.out, 'posts.txt')}")


def cmd_posts(args):
    urls = [l.split("|")[0].strip() for l in open(args.list, encoding="utf-8") if l.strip()]
    urls = urls[: args.limit]

    def one(url):
        m = re.search(r"blog\.naver\.com/(\w+)/(\d+)", url)
        blog_id, post_no = m.group(1), m.group(2)
        try:
            md = clean(scrape(f"https://m.blog.naver.com/{blog_id}/{post_no}"))
            write(os.path.join(args.out, f"{blog_id}_{post_no}.md"), f"source: {url}\n\n{md}")
            return f"ok   {blog_id}_{post_no}.md ({len(md)} chars)"
        except Exception as e:  # keep going on single failures
            return f"fail {url}: {e}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for line in ex.map(one, urls):
            print(line)


def cmd_google(args):
    d = call("search", {"query": args.query, "limit": args.limit,
                        "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True}})
    data = d.get("data") or []
    if isinstance(data, dict):
        data = data.get("web") or []
    out = []
    for r in data:
        md = clean(r.get("markdown") or "")
        heads = [l.strip() for l in md.split("\n")
                 if re.match(r"^#{1,4} ", l.strip()) or re.match(r"^\*\*[^*]{3,80}\*\*$", l.strip())]
        out.append(f"## {r.get('title')}\n{r.get('url')}\n\n" + "\n".join(heads[:60]))
        slug = re.sub(r"[^A-Za-z0-9]+", "_", (r.get("url") or "x"))[:80]
        write(os.path.join(args.out, "pages", f"{slug}.md"), f"source: {r.get('url')}\n\n{md}")
    write(os.path.join(args.out, "google.md"), "\n\n".join(out))
    print(f"{len(data)} results -> {os.path.join(args.out, 'google.md')}")


def cmd_page(args):
    md = clean(scrape(args.url))
    slug = re.sub(r"[^A-Za-z0-9]+", "_", args.url)[:80]
    path = os.path.join(args.out, f"{slug}.md")
    write(path, f"source: {args.url}\n\n{md}")
    print(f"{len(md)} chars -> {path}")


PRICE = re.compile(r"(\$\s?\d|\d+(?:\.\d+)?\s?(달러|불|AUD|aud)\b|AUD\s?\$?\d|\d[\d,]*\s?원)")


def cmd_prices(args):
    import glob
    out, seen = [], set()
    for d in args.dirs:
        for f in sorted(glob.glob(os.path.join(d, "**", "*.md"), recursive=True)):
            name = os.path.basename(f)
            if name == "search.md" or name in seen:
                continue
            seen.add(name)
            lines = [l.strip() for l in open(f, encoding="utf-8").read().splitlines() if l.strip()]
            keep = set()
            for i, l in enumerate(lines):
                if PRICE.search(l):
                    keep.update(range(max(0, i - args.context), i + 1))
            if keep:
                src = next((l for l in lines[:3] if l.startswith("source:")), name)
                out.append(f"## {src}")
                out += [lines[i][:220] for i in sorted(keep)]
    write(args.out, "\n".join(out))
    print(f"{len(seen)} posts -> {args.out}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--out", required=True)
    s = sub.add_parser("posts"); s.add_argument("list"); s.add_argument("--limit", type=int, default=6); s.add_argument("--workers", type=int, default=3); s.add_argument("--out", required=True)
    s = sub.add_parser("google"); s.add_argument("query"); s.add_argument("--limit", type=int, default=6); s.add_argument("--out", required=True)
    s = sub.add_parser("page"); s.add_argument("url"); s.add_argument("--out", required=True)
    s = sub.add_parser("prices"); s.add_argument("dirs", nargs="+"); s.add_argument("--context", type=int, default=2); s.add_argument("--out", required=True)
    args = p.parse_args()
    {"search": cmd_search, "posts": cmd_posts, "google": cmd_google, "page": cmd_page, "prices": cmd_prices}[args.cmd](args)


if __name__ == "__main__":
    main()
