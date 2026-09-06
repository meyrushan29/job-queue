"""
ITPro.lk job queue.

Polls the public ITPro.lk jobs API, scores every vacancy against your profile,
and writes docs/jobs.json for the dashboard to read. Telegram notifications are
optional and off unless you set the two environment variables.

Build the dashboard data:  python job_alert.py
Preview in the terminal:   python job_alert.py --dry-run
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://itpro.lk/api/v1/jobs"
JOB_URL = "https://itpro.lk/job/{id}/"
ROOT = Path(__file__).parent
SEEN_FILE = ROOT / "seen.json"
EXPORT_FILE = ROOT / "docs" / "jobs.json"
USER_AGENT = "job-alert-bot/1.0 (personal job search)"

# ITPro.lk category ids, for showing a readable label in the dashboard.
CATEGORY_NAMES = {
    "20": "Management",
    "21": "Software Engineering",
    "37": "IT and Operations",
    "38": "DevOps and Cloud",
    "39": "Quality Assurance",
    "40": "Digital Marketing",
    "41": "Mobile Development",
    "42": "AI and Data",
    "43": "Web Development",
}

JOB_TYPES = {"1": "Full-time", "2": "Part-time", "3": "Freelance", "4": "Internship"}

# ---------------------------------------------------------------------------
# Matching rules — edit these to change what you get notified about.
# ---------------------------------------------------------------------------

# Words that make a job MORE relevant. Higher number = stronger signal.
# A hit in the job title counts triple.
KEYWORDS = {
    # core stack
    "react": 5,
    "node": 5,
    "node.js": 5,
    "nodejs": 5,
    "typescript": 4,
    "javascript": 3,
    "full stack": 5,
    "full-stack": 5,
    "fullstack": 5,
    "mern": 5,
    "next.js": 3,
    "express": 3,
    "mongodb": 3,
    "postgresql": 2,
    "mysql": 2,
    "rest api": 2,
    "restful": 2,
    # python / ml
    "python": 4,
    "fastapi": 3,
    "machine learning": 4,
    "ml engineer": 4,
    "ai/ml": 4,
    "tensorflow": 2,
    "pytorch": 2,
    "pandas": 2,
    "llm": 2,
    # mobile
    "flutter": 3,
    "react native": 3,
    "dart": 2,
    # level
    "associate": 4,
    "junior": 3,
    "graduate": 3,
    "trainee": 1,
}

# If any of these appear in the TITLE, skip the job — you are not senior enough
# yet and these will only waste your time.
TITLE_BLOCKLIST = [
    "senior",
    "lead",
    "head of",
    "principal",
    "architect",
    "manager",
    "director",
    "sap ",
    "abap",
    "delphi",
    "wordpress",
    "business development",
    "sales",
    "marketing",
    "hr ",
    "human resource",
    "accountant",
    "intern",  # you have 2 years experience — remove this line to see internships
]

# ITPro.lk category ids. Only jobs in these categories are considered.
# 21 = Software Engineering, 41 = Mobile Development, 43 = Web Development,
# 42 = AI and Data, 39 = Quality Assurance, 38 = DevOps and Cloud
ALLOWED_CATEGORIES = {"21", "41", "43", "42", "38"}

# Only notify when the score reaches this. Lower it if you get too few alerts,
# raise it if you get too many.
SCORE_THRESHOLD = 8

# Locations you would actually accept. Leave empty to accept everything.
ALLOWED_LOCATIONS = {"colombo", "remote", "malabe", "rajagiriya", "nugegoda",
                     "kottawa", "moratuwa", "jaffna", "dehiwala", "kaduwela"}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fetch_jobs(retries=3):
    """Download the current job list from ITPro.lk."""
    request = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # network hiccup, bad JSON, rate limit
            last_error = error
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Could not fetch jobs after {retries} tries: {last_error}")


def strip_html(text):
    """Turn the HTML job description into plain lowercase text."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_location(summary):
    """ITPro puts the location inside the summary sentence, e.g.
    'Join X as a Y in Colombo, Full-time.' -> 'Colombo'."""
    if not summary:
        return "Unknown"
    match = re.search(
        r"\bin ([^,]+?),\s*(Full-time|Part-time|Internship|Freelance|Contract)",
        summary,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else "Unknown"


def score_job(job):
    """Return (score, matched_keywords) for a single job."""
    title = (job.get("title") or "").lower()
    body = strip_html(job.get("description")) + " " + (job.get("summary") or "").lower()

    for blocked in TITLE_BLOCKLIST:
        if blocked in title:
            return 0, []

    if ALLOWED_CATEGORIES and str(job.get("category_id")) not in ALLOWED_CATEGORIES:
        return 0, []

    location = parse_location(job.get("summary")).lower()
    if ALLOWED_LOCATIONS and not any(place in location for place in ALLOWED_LOCATIONS):
        return 0, []

    score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        in_title = keyword in title
        in_body = keyword in body
        if in_title:
            score += weight * 3
            matched.append(keyword)
        elif in_body:
            score += weight
            matched.append(keyword)

    return score, matched


def build_export_record(job, score, matched):
    """Shape one job for the dashboard."""
    blurb = strip_html(job.get("description"))
    if len(blurb) > 260:
        blurb = blurb[:257].rsplit(" ", 1)[0] + "..."

    return {
        "id": str(job.get("id")),
        "title": job.get("title") or "Untitled",
        "company": job.get("company") or "",
        "location": parse_location(job.get("summary")),
        "category": CATEGORY_NAMES.get(str(job.get("category_id")), "Other"),
        "jobType": JOB_TYPES.get(str(job.get("type_id")), ""),
        "posted": job.get("created_on") or "",
        "score": score,
        "matched": sorted(set(matched)),
        "blurb": blurb,
        "url": JOB_URL.format(id=job.get("id")),
    }


def export_for_dashboard(records):
    """Write docs/jobs.json, sorted best match first."""
    records.sort(key=lambda record: (-record["score"], record["posted"]))
    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "threshold": SCORE_THRESHOLD,
        "count": len(records),
        "jobs": records,
    }
    EXPORT_FILE.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    print(f"Wrote {len(records)} job(s) to {EXPORT_FILE}")


def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except (json.JSONDecodeError, ValueError):
            print("seen.json was corrupt, starting fresh", file=sys.stderr)
    return set()


def save_seen(seen_ids):
    # Keep the file from growing forever; the newest 2000 ids is plenty.
    trimmed = sorted(seen_ids, key=lambda value: int(value), reverse=True)[:2000]
    SEEN_FILE.write_text(json.dumps(trimmed, indent=1))


def format_message(job, score, matched):
    """Build the Telegram message for one job."""
    title = html.escape(job.get("title") or "Untitled")
    company = html.escape(job.get("company") or "Company not listed")
    location = html.escape(parse_location(job.get("summary")))
    link = JOB_URL.format(id=job.get("id"))
    tags = ", ".join(sorted(set(matched))[:6])

    return (
        f"<b>{title}</b>\n"
        f"{company} — {location}\n"
        f"Match score: {score}\n"
        f"Skills matched: {html.escape(tags)}\n\n"
        f'<a href="{link}">Open the listing</a>'
    )


def send_telegram(message):
    """Send one message. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set", file=sys.stderr)
        return False

    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }).encode()

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(url, data=payload, timeout=20) as response:
            return json.loads(response.read()).get("ok", False)
    except Exception as error:
        print(f"Telegram send failed: {error}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="print matches instead of sending them")
    parser.add_argument("--seed", action="store_true",
                        help="mark everything as seen without notifying")
    args = parser.parse_args()

    jobs = fetch_jobs()
    print(f"Fetched {len(jobs)} jobs from ITPro.lk")

    seen = load_seen()

    if args.seed:
        save_seen(seen | {str(job.get("id")) for job in jobs})
        print("Marked all current jobs as seen.")
        return

    # Score everything once. Matches feed the dashboard; the unseen subset
    # feeds Telegram, if it is switched on at all.
    all_matches = []
    fresh_matches = []
    for job in jobs:
        score, matched = score_job(job)
        if score < SCORE_THRESHOLD:
            continue
        all_matches.append(build_export_record(job, score, matched))
        if str(job.get("id")) not in seen:
            fresh_matches.append((score, job, matched))

    print(f"{len(all_matches)} job(s) above threshold {SCORE_THRESHOLD}, "
          f"{len(fresh_matches)} of them new")

    if args.dry_run:
        for record in sorted(all_matches, key=lambda r: -r["score"]):
            print(f"  {record['score']:3d}  {record['location']:10s}  "
                  f"{record['title'][:50]}")
        return

    export_for_dashboard(all_matches)

    # Telegram is optional. Skipped silently when the variables are absent.
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        fresh_matches.sort(key=lambda row: row[0], reverse=True)
        for score, job, matched in fresh_matches:
            send_telegram(format_message(job, score, matched))
            time.sleep(1)  # stay under Telegram's rate limit

    seen |= {str(job.get("id")) for job in jobs}
    save_seen(seen)


if __name__ == "__main__":
    main()
