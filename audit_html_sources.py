import os
import csv
import time
import requests
import django

from bs4 import BeautifulSoup

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from news.models import News

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0 Safari/537.36"
    )
}

TIMEOUT = 20


def test_source(source):
    result = {
        "published": source.published,
        "source": source.title,
        "function": source.function,
        "url": source.feed_url,
        "status": None,
        "content_type": "",
        "final_url": "",
        "html_size": 0,
        "article_tags": 0,
        "h2_tags": 0,
        "h3_tags": 0,
        "links": 0,
        "story_links": 0,
        "elapsed": 0,
        "error": "",
    }

    started = time.time()

    try:
        response = requests.get(
            source.feed_url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        result["status"] = response.status_code
        result["content_type"] = response.headers.get(
            "Content-Type",
            ""
        )
        result["final_url"] = response.url
        result["html_size"] = len(response.content)

        if response.status_code == 200:
            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            result["article_tags"] = len(
                soup.find_all("article")
            )

            result["h2_tags"] = len(
                soup.find_all("h2")
            )

            result["h3_tags"] = len(
                soup.find_all("h3")
            )

            links = soup.find_all(
                "a",
                href=True
            )

            result["links"] = len(links)

            # Rough estimate of likely story links
            story_count = 0

            for link in links:
                href = link.get("href", "")
                text = link.get_text(
                    " ",
                    strip=True
                )

                if not text:
                    continue

                if len(text) < 20:
                    continue

                if any(
                        token in href.lower()
                        for token in [
                            "/story/",
                            "/news/",
                            "/article/",
                            "/stories/",
                            "/2026/",
                        ]
                ):
                    story_count += 1

            result["story_links"] = story_count

    except Exception as e:
        result["error"] = str(e)

    result["elapsed"] = round(
        time.time() - started,
        2
    )

    return result


def classify(result):
    if result["error"]:
        return "ERROR"

    if result["status"] == 403:
        return "BLOCKED"

    if result["status"] == 429:
        return "RATE LIMITED"

    if result["status"] != 200:
        return f"HTTP {result['status']}"

    if result["story_links"] > 0:
        return "LIKELY WORKING"

    if (
            result["article_tags"] > 0
            or result["h2_tags"] > 0
            or result["h3_tags"] > 0
    ):
        return "REVIEW SELECTORS"

    return "NO CONTENT"


def main():
    sources = (
        News.objects
        .filter(
            scrape_type=News.SCRAPE_HTML,
        )
        .order_by("title")
    )

    results = []

    print()
    print("=" * 125)
    print("BURQUEBRO HTML SOURCE AUDIT")
    print("=" * 125)

    print(
        f"{'Pub':<5}"
        f"{'Source':<34}"
        f"{'Status':<18}"
        f"{'HTTP':<7}"
        f"{'Articles':<10}"
        f"{'H2':<7}"
        f"{'H3':<7}"
        f"{'Links':<8}"
        f"{'Stories':<9}"
        f"{'Sec':<7}"
    )

    print("-" * 130)

    for source in sources:
        result = test_source(source)
        result["classification"] = classify(result)

        results.append(result)

        print(
            f"{'✓' if result['published'] else '✗':<5}"
            f"{result['source'][:33]:<34}"
            f"{result['classification']:<18}"
            f"{str(result['status']):<7}"
            f"{result['article_tags']:<10}"
            f"{result['h2_tags']:<7}"
            f"{result['h3_tags']:<7}"
            f"{result['links']:<8}"
            f"{result['story_links']:<9}"
            f"{result['elapsed']:<7}"
        )

    print("=" * 125)

    filename = "html_source_audit.csv"

    with open(
            filename,
            "w",
            newline="",
            encoding="utf-8",
    ) as csvfile:
        fieldnames = [
            "published",
            "source",
            "function",
            "url",
            "classification",
            "status",
            "content_type",
            "final_url",
            "html_size",
            "article_tags",
            "h2_tags",
            "h3_tags",
            "links",
            "story_links",
            "elapsed",
            "error",
        ]

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print(
        f"Audited {len(results)} HTML sources."
    )
    print(
        f"CSV report written to {filename}"
    )


if __name__ == "__main__":
    main()
