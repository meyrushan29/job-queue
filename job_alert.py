"""
Sri Lanka IT job queue.

Polls ITPro.lk's public jobs API and scrapes topjobs.lk's IT listings, scores
every vacancy against your profile, and writes docs/jobs.json for the
dashboard to read. Telegram notifications are optional and off unless you set
the two environment variables.

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

# topjobs.lk has no public API; its IT category page is plain server-rendered
# HTML (JSP), so we scrape the listing table directly. It never exposes real
# description text (postings are image ads), so topjobs jobs are scored on
# title alone.
TOPJOBS_LIST_URL = "https://topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA={fa}&jst=OPEN"
TOPJOBS_DETAIL_URL = "https://topjobs.lk/employer/JobAdvertismentServlet?ac={ac}&jc={jc}&ec={ec}"
TOPJOBS_CATEGORIES = {
    "SDQ": "IT-Software/DB/QA/Web/Graphics/GIS",
}
TOPJOBS_ROW_RE = re.compile(
    r"createAlert\('\d+','(?P<agent>[^']*)','(?P<job>[^']*)','(?P<emp>[^']*)'.*?"
    r"<h2><span>(?P<title>.*?)</span></h2>\s*"
    r"<h1>(?P<company>.*?)</h1>.*?"
    r'<td width="35%">.*?</td>\s*'
    r'<td width="12%" nowrap class="" >\s*(?P<opened>[^<]*?)</td>.*?'
    r'<td width="12%" nowrap class="" >\s*(?P<closed>[^<]*?)</td>.*?'
    r'<td width="8%" nowrap class="" >\s*(?P<location>[^<]*?)</td>',
    re.DOTALL,
)

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
                     "kottawa", "moratuwa", "jaffna", "dehiwala", "kaduwela",
                     "all island"}


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


def fetch_topjobs_jobs():
    """Scrape topjobs.lk's IT functional-area listing page(s)."""
    jobs = []
    for fa_code, category in TOPJOBS_CATEGORIES.items():
        url = TOPJOBS_LIST_URL.format(fa=fa_code)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                page = response.read().decode("utf-8", errors="replace")
        except Exception as error:
            print(f"topjobs.lk fetch failed for {fa_code}: {error}", file=sys.stderr)
            continue

        for match in TOPJOBS_ROW_RE.finditer(page):
            job_code = match.group("job")
            jobs.append({
                "id": "tj-" + job_code,
                "title": html.unescape(match.group("title")).strip(),
                "company": html.unescape(match.group("company")).strip(),
                "location": html.unescape(match.group("location")).strip(),
                "category": category,
                "posted": parse_topjobs_date(match.group("opened").strip()),
                "url": TOPJOBS_DETAIL_URL.format(
                    ac=match.group("agent"), jc=job_code, ec=match.group("emp")),
            })
    return jobs


def parse_topjobs_date(text):
    """'Sat Sep 05 2026' -> '2026-09-05 00:00:00', the dashboard's format."""
    try:
        parsed = time.strptime(text, "%a %b %d %Y")
    except ValueError:
        return ""
    return time.strftime("%Y-%m-%d 00:00:00", parsed)


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


def title_blocked(title):
    return any(blocked in title for blocked in TITLE_BLOCKLIST)


def location_allowed(location):
    if not ALLOWED_LOCATIONS:
        return True
    location = location.lower()
    return any(place in location for place in ALLOWED_LOCATIONS)


def score_by_keywords(title, body=""):
    """Return (score, matched_keywords). A hit in the title counts triple."""
    score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        in_title = keyword in title
        in_body = bool(body) and keyword in body
        if in_title:
            score += weight * 3
            matched.append(keyword)
        elif in_body:
            score += weight
            matched.append(keyword)
    return score, matched


def score_job(job):
    """Return (score, matched_keywords) for a single ITPro.lk job."""
    title = (job.get("title") or "").lower()
    body = strip_html(job.get("description")) + " " + (job.get("summary") or "").lower()

    if title_blocked(title):
        return 0, []

    if ALLOWED_CATEGORIES and str(job.get("category_id")) not in ALLOWED_CATEGORIES:
        return 0, []

    location = parse_location(job.get("summary"))
    if not location_allowed(location):
        return 0, []

    return score_by_keywords(title, body)


def score_topjobs_job(title, location):
    """Return (score, matched_keywords) for a topjobs.lk job (title only —
    topjobs postings are image ads with no machine-readable description)."""
    title = title.lower()
    if title_blocked(title):
        return 0, []
    if not location_allowed(location):
        return 0, []
    return score_by_keywords(title)


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
        "source": "ITPro.lk",
    }


def build_topjobs_export_record(job, score, matched):
    """Shape one scraped topjobs.lk row for the dashboard."""
    return {
        "id": job["id"],
        "title": job["title"] or "Untitled",
        "company": job["company"] or "",
        "location": job["location"] or "Unknown",
        "category": job["category"],
        "jobType": "",
        "posted": job["posted"],
        "score": score,
        "matched": sorted(set(matched)),
        "blurb": "",
        "url": job["url"],
        "source": "topjobs.lk",
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


def _seen_sort_key(value):
    """Ids are either plain ITPro numbers or 'tj-<number>'; sort newest-ish first."""
    digits = re.sub(r"\D", "", value)
    return int(digits) if digits else 0


def save_seen(seen_ids):
    # Keep the file from growing forever; the newest 2000 ids is plenty.
    trimmed = sorted(seen_ids, key=_seen_sort_key, reverse=True)[:2000]
    SEEN_FILE.write_text(json.dumps(trimmed, indent=1))


def format_message(record):
    """Build the Telegram message for one exported job record."""
    title = html.escape(record["title"])
    company = html.escape(record["company"] or "Company not listed")
    location = html.escape(record["location"])
    tags = ", ".join(record["matched"][:6])

    return (
        f"<b>{title}</b>\n"
        f"{company} — {location} · {html.escape(record['source'])}\n"
        f"Match score: {record['score']}\n"
        f"Skills matched: {html.escape(tags)}\n\n"
        f'<a href="{record["url"]}">Open the listing</a>'
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

    itpro_jobs = fetch_jobs()
    print(f"Fetched {len(itpro_jobs)} jobs from ITPro.lk")
    topjobs_jobs = fetch_topjobs_jobs()
    print(f"Fetched {len(topjobs_jobs)} jobs from topjobs.lk")

    all_ids = ({str(job.get("id")) for job in itpro_jobs}
               | {job["id"] for job in topjobs_jobs})

    seen = load_seen()

    if args.seed:
        save_seen(seen | all_ids)
        print("Marked all current jobs as seen.")
        return

    # Score everything once. Matches feed the dashboard; the unseen subset
    # feeds Telegram, if it is switched on at all.
    all_matches = []
    fresh_matches = []
    for job in itpro_jobs:
        score, matched = score_job(job)
        if score < SCORE_THRESHOLD:
            continue
        record = build_export_record(job, score, matched)
        all_matches.append(record)
        if record["id"] not in seen:
            fresh_matches.append(record)

    for job in topjobs_jobs:
        score, matched = score_topjobs_job(job["title"], job["location"])
        if score < SCORE_THRESHOLD:
            continue
        record = build_topjobs_export_record(job, score, matched)
        all_matches.append(record)
        if record["id"] not in seen:
            fresh_matches.append(record)

    print(f"{len(all_matches)} job(s) above threshold {SCORE_THRESHOLD}, "
          f"{len(fresh_matches)} of them new")

    if args.dry_run:
        for record in sorted(all_matches, key=lambda r: -r["score"]):
            print(f"  {record['score']:3d}  {record['location']:10s}  "
                  f"{record['title'][:45]:45s}  [{record['source']}]")
        return

    export_for_dashboard(all_matches)

    # Telegram is optional. Skipped silently when the variables are absent.
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        fresh_matches.sort(key=lambda record: record["score"], reverse=True)
        for record in fresh_matches:
            send_telegram(format_message(record))
            time.sleep(1)  # stay under Telegram's rate limit

    seen |= all_ids
    save_seen(seen)


if __name__ == "__main__":
    main()
