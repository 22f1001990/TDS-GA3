import json
import subprocess


def get_metadata(url):
    result = subprocess.run(
        ["yt-dlp", "--dump-single-json", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# Load your downloaded task file here
with open("GA_3/q1/q-youtube-metadata-filter-server.json", "r") as f:
    task = json.load(f)

source_urls = task["source_urls"]
required_words = [w.lower() for w in task["required_words"]]
forbidden_words = [w.lower() for w in task["forbidden_words"]]

min_duration = task["min_duration_seconds"]
max_duration = task["max_duration_seconds"]
limit = task["limit"]

videos = []

for url in source_urls:
    try:
        meta = get_metadata(url)

        duration = meta.get("duration")
        if duration is None:
            continue

        if not (min_duration <= duration <= max_duration):
            continue

        title = meta.get("title", "")
        description = meta.get("description", "")

        combined = (title + " " + description).lower()

        if not all(word in combined for word in required_words):
            continue

        if any(word in combined for word in forbidden_words):
            continue

        videos.append({
            "url": url,
            "upload_date": meta.get("upload_date", ""),
            "id": meta.get("id", "")
        })

    except Exception as e:
        print(f"Failed: {url}: {e}")

videos.sort(
    key=lambda x: (x["upload_date"], "".join(chr(255 - ord(c)) for c in x["id"])),
)

# Easier sort: newest first, ID ascending
videos = sorted(
    videos,
    key=lambda x: (-int(x["upload_date"]), x["id"])
)

result = [v["url"] for v in videos[:limit]]
data={"urls": result}
print(json.dumps(data, indent=2))
