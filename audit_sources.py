import os
import csv
import json
import requests
import django

from urllib.parse import urljoin, urlparse

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bqb.settings"
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

TIMEOUT = 12


def normalize_base_url(url):
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}/"


def test_url(url):
    result = {
        "url": url,
        "status": None,
        "content_type": "",
        "final_url": "",
        "length": 0,
        "rss": False,
        "json": False,
        "html": False,
        "error": "",
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        result["status"] = response.status_code
        result["final_url"] = response.url
        result["content_type"] = (
            response.headers.get(
                "Content-Type",
                ""
            )
            .lower()
        )

        result["length"] = len(response.content)

        text_start = response.text[:1000].lower()

        if (
            "application/rss+xml"
            in result["content_type"]
            or "application/xml"
            in result["content_type"]
            or "<rss" in text_start
            or "<feed" in text_start
        ):
            result["rss"] = True

        if (
            "application/json"
            in result["content_type"]
        ):
            try:
                response.json()
                result["json"] = True
            except Exception:
                pass

        if (
            "text/html"
            in result["content_type"]
            or "<html" in text_start
        ):
            result["html"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def choose_method(results):
    wp = results.get("wordpress_api")
    feed = results.get("feed")
    rss = results.get("rss")
    configured = results.get("configured")

    if wp and wp["status"] == 200 and wp["json"]:
        return "WORDPRESS_API"

    if feed and feed["status"] == 200 and feed["rss"]:
        return "RSS"

    if rss and rss["status"] == 200 and rss["rss"]:
        return "RSS"

    if (
        configured
        and configured["status"] == 200
        and configured["rss"]
    ):
        return "RSS"

    if (
        configured
        and configured["status"] == 200
        and configured["html"]
    ):
        return "HTML"

    if configured and configured["status"] == 403:
        return "BLOCKED"

    return "REVIEW"


def main():
    sources = (
        News.objects
        .order_by("title")
    )

    report = []

    print()
    print("=" * 110)
    print("BURQUEBRO SOURCE AUDIT")
    print("=" * 110)

    for source in sources:
        configured_url = (
            source.feed_url or source.source
        )

        base_url = normalize_base_url(
            configured_url
        )

        if not base_url:
            print(
                f"{source.title:<35} "
                f"INVALID URL"
            )
            continue

        tests = {
            "configured": configured_url,
            "feed": urljoin(
                base_url,
                "feed/"
            ),
            "rss": urljoin(
                base_url,
                "rss"
            ),
            "rss_slash": urljoin(
                base_url,
                "rss/"
            ),
            "wordpress_api": urljoin(
                base_url,
                "wp-json/wp/v2/posts?per_page=1"
            ),
        }

        results = {}

        for name, url in tests.items():
            results[name] = test_url(url)

        method = choose_method(results)

        configured_status = (
            results["configured"]["status"]
        )

        wp_status = (
            results["wordpress_api"]["status"]
        )

        feed_status = (
            results["feed"]["status"]
        )

        rss_status = (
            results["rss"]["status"]
        )

        print(
            f"{source.title:<35} "
            f"{method:<15} "
            f"PAGE:{str(configured_status):<4} "
            f"WP:{str(wp_status):<4} "
            f"FEED:{str(feed_status):<4} "
            f"RSS:{str(rss_status):<4}"
        )

        report.append({
            "source": source.title,
            "function": source.function,
            "configured_url": configured_url,
            "recommended_method": method,
            "tests": results,
        })

    print("=" * 110)

    # ------------------------------------------------------------------
    # Write JSON report
    # ------------------------------------------------------------------
    with open(
            "source_audit.json",
            "w",
            encoding="utf-8",
    ) as outfile:
        json.dump(
            report,
            outfile,
            indent=4,
        )

    # ------------------------------------------------------------------
    # Write CSV report
    # ------------------------------------------------------------------
    with open(
            "source_audit.csv",
            "w",
            newline="",
            encoding="utf-8",
    ) as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "Source",
            "Function",
            "Configured URL",
            "Recommended Method",
            "Page Status",
            "Page Type",
            "WP API Status",
            "WP API JSON",
            "Feed Status",
            "Feed RSS",
            "RSS Status",
            "RSS XML",
            "RSS/ Status",
            "RSS/ XML",
            "Final URL",
            "Notes",
        ])

        for item in report:

            configured = item["tests"]["configured"]
            wp = item["tests"]["wordpress_api"]
            feed = item["tests"]["feed"]
            rss = item["tests"]["rss"]
            rss_slash = item["tests"]["rss_slash"]

            notes = ""

            if configured["error"]:
                notes = configured["error"]

            elif item["recommended_method"] == "BLOCKED":
                notes = "403 Forbidden"

            writer.writerow([
                item["source"],
                item["function"],
                item["configured_url"],
                item["recommended_method"],
                configured["status"],
                configured["content_type"],
                wp["status"],
                wp["json"],
                feed["status"],
                feed["rss"],
                rss["status"],
                rss["rss"],
                rss_slash["status"],
                rss_slash["rss"],
                configured["final_url"],
                notes,
            ])

    print()
    print(f"Audit complete. {len(report)} sources tested.")
    print("JSON report : source_audit.json")
    print("CSV report  : source_audit.csv")


if __name__ == "__main__":
    main()