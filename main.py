import requests
from urllib.parse import urlparse


sites = {
    "Alamogordo Daily News":
        "https://www.alamogordonews.com/",

    "Artesia Daily Press":
        "https://www.artesianews.com/",

    "Carlsbad Current Argus":
        "https://www.currentargus.com/",

    "Farmington Daily Times":
        "https://www.daily-times.com/",

    "Hobbs Sun":
        "https://www.hobbsnews.com/",

    "Los Alamos Daily Post":
        "https://ladailypost.com/",

    "Roosevelt Review":
        "https://www.therooseveltreview.com/",

    "Ruidoso News":
        "https://www.ruidosonews.com/",
}


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


for name, base_url in sites.items():

    parsed = urlparse(base_url)

    root = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}/"
    )

    tests = [
        root + "feed/",
        root + "rss/",
        root + "wp-json/wp/v2/posts?per_page=5&_embed=1",
    ]

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    for url in tests:

        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=20,
                allow_redirects=True,
            )

            content_type = (
                r.headers
                .get("Content-Type", "")
                .lower()
            )

            method = "UNKNOWN"

            if (
                r.status_code == 200
                and "application/json" in content_type
            ):
                method = "WORDPRESS API"

            elif (
                r.status_code == 200
                and (
                    "rss" in content_type
                    or "xml" in content_type
                    or "<rss" in r.text[:1000].lower()
                )
            ):
                method = "RSS"

            elif r.status_code == 200:
                method = "HTML"

            elif r.status_code == 403:
                method = "BLOCKED"

            else:
                method = f"HTTP {r.status_code}"

            print(
                f"{method:<15} "
                f"{r.status_code:<4} "
                f"{content_type[:32]:<32} "
                f"{r.url}"
            )

        except Exception as e:
            print(
                f"{'ERROR':<15} "
                f"{url} "
                f"{e}"
            )