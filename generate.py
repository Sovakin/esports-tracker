import os
import json
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("в консоль pip install requests")
    sys.exit(1)

API_TOKEN = "6LJZ7XV9wKYQ72JisFq64ZRBnEcT11JWpnZypduhmj-P6ky0SEM"
API_BASE_URL = "https://api.pandascore.co"
OUTPUT_DIR = "build"

TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def format_date_ru(dt):
    return f"{dt.day} {MONTHS_RU[dt.month]} {dt.year}"


def format_date_iso(dt):
    return dt.strftime("%Y-%m-%d")


def fetch_matches(endpoint, date_from, date_to):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {
        "range[begin_at]": f"{date_from}T00:00:00Z,{date_to}T23:59:59Z",
        "sort": "begin_at",
        "per_page": 50,
    }
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Ошибка API: {e}")
        return []


def get_matches_for_date(dt):
    date_str = format_date_iso(dt)
    today_str = format_date_iso(TODAY)

    if date_str < today_str:
        endpoint = "/matches/past"
    elif date_str > today_str:
        endpoint = "/matches/upcoming"
    else:
        endpoint = "/matches"

    print(f"  Запрос: {endpoint} за {date_str}")
    return fetch_matches(endpoint, date_str, date_str)


def process_match(match):
    opponents = match.get("opponents", [])
    team1 = opponents[0]["opponent"] if len(opponents) > 0 else None
    team2 = opponents[1]["opponent"] if len(opponents) > 1 else None

    begin_at = match.get("begin_at", "")
    time_str = ""
    if begin_at:
        try:
            dt = datetime.fromisoformat(begin_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M")
        except (ValueError, TypeError):
            time_str = "TBD"

    results = match.get("results", [])
    score1 = results[0].get("score", 0) if len(results) > 0 else 0
    score2 = results[1].get("score", 0) if len(results) > 1 else 0

    game = match.get("videogame", {})
    game_name = game.get("name", "Unknown") if game else "Unknown"

    league = match.get("league", {})
    league_name = league.get("name", "") if league else ""

    serie = match.get("serie", {})
    serie_name = serie.get("full_name", "") if serie else ""

    status = match.get("status", "unknown")
    match_type = match.get("match_type", "")
    number_of_games = match.get("number_of_games", 0)

    status_labels = {
        "finished": "Завершён",
        "running": "LIVE",
        "not_started": "Ожидается",
        "canceled": "Отменён",
        "postponed": "Отложен",
    }
    status_label = status_labels.get(status, status)

    status_classes = {
        "finished": "status-finished",
        "running": "status-live",
        "not_started": "status-upcoming",
        "canceled": "status-canceled",
        "postponed": "status-canceled",
    }
    status_class = status_classes.get(status, "status-upcoming")

    return {
        "id": match.get("id", 0),
        "team1_name": team1.get("name", "TBD") if team1 else "TBD",
        "team1_image": team1.get("image_url", "") if team1 else "",
        "team2_name": team2.get("name", "TBD") if team2 else "TBD",
        "team2_image": team2.get("image_url", "") if team2 else "",
        "score1": score1,
        "score2": score2,
        "time": time_str,
        "game": game_name,
        "league": league_name,
        "serie": serie_name,
        "status": status,
        "status_label": status_label,
        "status_class": status_class,
        "match_type": match_type,
        "number_of_games": number_of_games,
        "begin_at": begin_at,
    }


CSS_STYLES = """
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
}

.header {
    background-color: #2c3e50;
    color: white;
    padding: 15px 20px;
}

.header-inner {
    max-width: 1000px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header h2 {
    margin: 0;
    font-size: 20px;
}

.nav {
    display: flex;
    gap: 5px;
}

.nav a {
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

.nav a:hover {
    background-color: #3d566e;
}

.nav a.active {
    background-color: #3498db;
    font-weight: bold;
}

h1 {
    text-align: center;
    margin: 30px 0 10px;
    font-size: 24px;
    color: #2c3e50;
}

.subtitle {
    text-align: center;
    color: #777;
    margin-bottom: 25px;
    font-size: 14px;
}

.main {
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 20px 40px;
}

.match-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 15px 20px;
    margin-bottom: 10px;
}

.match-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    font-size: 13px;
    color: #888;
}

.match-game {
    font-weight: bold;
    color: #555;
}

.match-body {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
}

.team {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
}

.team-left {
    justify-content: flex-end;
    text-align: right;
}

.team-right {
    justify-content: flex-start;
    text-align: left;
}

.team-name {
    font-weight: bold;
    font-size: 15px;
}

.team-logo {
    width: 36px;
    height: 36px;
    border-radius: 4px;
    object-fit: contain;
}

.team-logo-placeholder {
    width: 36px;
    height: 36px;
    background: #eee;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #999;
    font-size: 14px;
}

.score-block {
    font-size: 22px;
    font-weight: bold;
    padding: 5px 15px;
    background: #f0f0f0;
    border-radius: 4px;
    white-space: nowrap;
}

.score-winner {
    color: #27ae60;
}

.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
}

.status-finished {
    background: #e8f5e9;
    color: #2e7d32;
}

.status-live {
    background: #ffebee;
    color: #c62828;
}

.status-upcoming {
    background: #e3f2fd;
    color: #1565c0;
}

.status-canceled {
    background: #fff3e0;
    color: #e65100;
}

.match-bottom {
    margin-top: 8px;
    font-size: 12px;
    color: #aaa;
    display: flex;
    justify-content: space-between;
}

.empty-msg {
    text-align: center;
    padding: 60px 20px;
    color: #999;
    font-size: 16px;
}

.footer {
    background: #2c3e50;
    color: #aaa;
    text-align: center;
    padding: 20px;
    font-size: 12px;
}

.footer a {
    color: #3498db;
    text-decoration: none;
}

@media (max-width: 600px) {
    .match-body {
        flex-direction: column;
        gap: 8px;
    }
    .team {
        justify-content: center !important;
        text-align: center !important;
    }
    .header-inner {
        flex-direction: column;
        gap: 10px;
    }
}
"""


def generate_match_card(match, index):
    if match["team1_image"]:
        team1_logo = f'<img class="team-logo" src="{match["team1_image"]}" alt="{match["team1_name"]}">'
    else:
        initial = match["team1_name"][0] if match["team1_name"] != "TBD" else "?"
        team1_logo = f'<div class="team-logo-placeholder">{initial}</div>'

    if match["team2_image"]:
        team2_logo = f'<img class="team-logo" src="{match["team2_image"]}" alt="{match["team2_name"]}">'
    else:
        initial = match["team2_name"][0] if match["team2_name"] != "TBD" else "?"
        team2_logo = f'<div class="team-logo-placeholder">{initial}</div>'

    s1_class = " score-winner" if match["status"] == "finished" and match["score1"] > match["score2"] else ""
    s2_class = " score-winner" if match["status"] == "finished" and match["score2"] > match["score1"] else ""

    format_text = ""
    if match["match_type"] == "best_of":
        format_text = f'BO{match["number_of_games"]}'

    league_info = match["league"]
    if match["serie"]:
        league_info += f' — {match["serie"]}'

    bottom_html = ""
    if format_text or league_info:
        bottom_html = f'<div class="match-bottom"><span>{league_info}</span><span>{format_text}</span></div>'

    return f"""
    <div class="match-card" itemscope itemtype="https://schema.org/SportsEvent">
        <meta itemprop="name" content="{match['team1_name']} vs {match['team2_name']}">
        <meta itemprop="startDate" content="{match['begin_at']}">
        <meta itemprop="eventStatus" content="https://schema.org/EventScheduled">
        <span itemprop="location" itemscope itemtype="https://schema.org/VirtualLocation">
            <meta itemprop="url" content="https://pandascore.co">
        </span>
        <div class="match-top">
            <span class="match-game">{match['game']}</span>
            <span>
                <span class="status-badge {match['status_class']}">{match['status_label']}</span>
                {match['time']}
            </span>
        </div>
        <div class="match-body">
            <div class="team team-left" itemprop="competitor" itemscope itemtype="https://schema.org/SportsTeam">
                <span class="team-name" itemprop="name">{match['team1_name']}</span>
                {team1_logo}
            </div>
            <div class="score-block">
                <span class="{s1_class}">{match['score1']}</span> : <span class="{s2_class}">{match['score2']}</span>
            </div>
            <div class="team team-right" itemprop="competitor" itemscope itemtype="https://schema.org/SportsTeam">
                {team2_logo}
                <span class="team-name" itemprop="name">{match['team2_name']}</span>
            </div>
        </div>
        {bottom_html}
    </div>
    """


def generate_schema_org(page_title, page_description, page_url):
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_title,
        "description": page_description,
        "url": page_url,
        "publisher": {
            "@type": "Organization",
            "name": "Esports Match Tracker",
            "url": page_url,
            "logo": {
                "@type": "ImageObject",
                "url": f"{page_url}/logo.png",
            },
        },
        "isPartOf": {
            "@type": "WebSite",
            "name": "Esports Match Tracker",
            "url": page_url,
        },
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'


def generate_page(filename, date, date_label, badge_text, matches_raw, nav_active):
    date_str = format_date_ru(date)
    page_title = f"Киберспортивные матчи — {date_label} ({date_str})"
    page_description = (
        f"Расписание и результаты киберспортивных матчей за {date_str}. "
        f"CS2, Dota 2, League of Legends, Valorant и другие дисциплины."
    )

    matches = [process_match(m) for m in matches_raw]

    if matches:
        cards_html = "\n".join(generate_match_card(m, i) for i, m in enumerate(matches))
    else:
        cards_html = '<div class="empty-msg">На эту дату матчей не найдено.</div>'

    nav_yesterday = ' class="active"' if nav_active == "yesterday" else ""
    nav_today = ' class="active"' if nav_active == "today" else ""
    nav_tomorrow = ' class="active"' if nav_active == "tomorrow" else ""

    schema_org = generate_schema_org(page_title, page_description, "https://esports-tracker-eb0es52mr-s0vakin.vercel.app")

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{page_title}</title>
    <meta name="description" content="{page_description}">
    <meta name="keywords" content="киберспорт, esports, матчи, CS2, Dota 2, League of Legends, Valorant, расписание, результаты">
    <meta name="author" content="Esports Match Tracker">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://esports-tracker-eb0es52mr-s0vakin.vercel.app/{filename}">

    <meta property="og:type" content="website">
    <meta property="og:title" content="{page_title}">
    <meta property="og:description" content="{page_description}">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="Esports Match Tracker">
    {schema_org}

    <style>
    {CSS_STYLES}
    </style>
</head>
<body>

    <header class="header">
        <div class="header-inner">
            <h2>Esports Tracker</h2>
            <nav class="nav">
                <a href="yesterday.html"{nav_yesterday}>Вчера</a>
                <a href="index.html"{nav_today}>Сегодня</a>
                <a href="tomorrow.html"{nav_tomorrow}>Завтра</a>
            </nav>
        </div>
    </header>

    <h1>Матчи за {date_str}</h1>
    <p class="subtitle">Всего матчей: {len(matches)}</p>

    <main class="main">
        {cards_html}
    </main>

    </body>
</html>"""

    return html


def main():
    print("=" * 60)
    print("  Генератор сайта киберспортивных матчей")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pages = [
        {
            "filename": "yesterday.html",
            "date": YESTERDAY,
            "label": "Вчерашний день",
            "badge": f"Вчера — {format_date_ru(YESTERDAY)}",
            "nav": "yesterday",
        },
        {
            "filename": "index.html",
            "date": TODAY,
            "label": "Сегодняшний день",
            "badge": f"Сегодня — {format_date_ru(TODAY)}",
            "nav": "today",
        },
        {
            "filename": "tomorrow.html",
            "date": TOMORROW,
            "label": "Завтрашний день",
            "badge": f"Завтра — {format_date_ru(TOMORROW)}",
            "nav": "tomorrow",
        },
    ]

    for page in pages:
        print(f"\n{'─' * 40}")
        print(f"Генерация: {page['filename']} ({page['label']})")

        matches = get_matches_for_date(page["date"])
        print(f"  Получено матчей: {len(matches)}")

        html = generate_page(
            filename=page["filename"],
            date=page["date"],
            date_label=page["label"],
            badge_text=page["badge"],
            matches_raw=matches,
            nav_active=page["nav"],
        )

        filepath = os.path.join(OUTPUT_DIR, page["filename"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Сохранено: {filepath}")

    site_url = "https://esports-tracker-eb0es52mr-s0vakin.vercel.app"
    today_iso = format_date_iso(TODAY)
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{site_url}/index.html</loc>
        <lastmod>{today_iso}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{site_url}/yesterday.html</loc>
        <lastmod>{today_iso}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{site_url}/tomorrow.html</loc>
        <lastmod>{today_iso}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""

    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"\nСоздан: {sitemap_path}")

    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {site_url}/sitemap.xml"""

    robots_path = os.path.join(OUTPUT_DIR, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots_txt)
    print(f"Создан: {robots_path}")

    print(f"\n{'=' * 60}")
    print(f"  Готово! Файлы в папке: {OUTPUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
