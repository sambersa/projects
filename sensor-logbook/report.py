"""Render a portable SVG report without charting dependencies."""
from html import escape
from logbook import RULES, timestamp


def render(book, status):
    rows = book.readings("pump-01")
    count = status["reading_count"]
    stale = sum(a["stale"] for a in status["assets"])
    alarms = len(status["alarms"])
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="720" viewBox="0 0 1100 720" role="img" aria-labelledby="title desc">',
             '<title id="title">Sensor Logbook — demo report</title>',
             '<desc id="desc">Pump 01 temperature and vibration over five minutes, with alarm and recovery thresholds. Pump 02 stops reporting and becomes stale.</desc>',
             '<rect width="1100" height="720" fill="#101b2d"/>',
             '<g font-family="Segoe UI,Arial,sans-serif" fill="#eff5ff">',
             '<text x="48" y="54" font-size="14" fill="#64daca" letter-spacing="3">SENSOR LOGBOOK / LOCAL DEMO</text>',
             '<text x="48" y="100" font-size="32" font-weight="700">A small record of machine health.</text>']
    for i, (label, value) in enumerate([("READINGS", count), ("ALARM EPISODES", alarms), ("STALE ASSETS", stale)]):
        x = 48 + i * 338
        parts += [f'<rect x="{x}" y="130" width="320" height="94" rx="12" fill="#1b2b43"/>',
                  f'<text x="{x+20}" y="158" font-size="12" fill="#a8bad3">{label}</text>',
                  f'<text x="{x+20}" y="204" font-size="34" font-weight="700">{value}</text>']
    for index, (metric, (high, clear, unit)) in enumerate(RULES.items()):
        y = 275 + index * 195
        max_value = 100 if metric == "temperature" else 10
        left, right, height = 95, 1040, 115
        def ordinate(value):
            return y + height - value / max_value * height
        parts += [f'<text x="48" y="{y-15}" font-size="16">pump-01 / {escape(metric)} ({escape(unit)})</text>',
                  f'<text x="1040" y="{y-15}" text-anchor="end" font-size="12" fill="#a8bad3">alarm ≥ {high:g} / clear ≤ {clear:g}</text>']
        for tick in (0, max_value / 2, max_value):
            ty = ordinate(tick)
            parts += [f'<line x1="{left}" y1="{ty}" x2="{right}" y2="{ty}" stroke="#2b3d57"/>',
                      f'<text x="75" y="{ty+4}" text-anchor="end" font-size="11" fill="#a8bad3">{tick:g}</text>']
        for threshold, color, label in [(high, "#ffb86b", "alarm"), (clear, "#8495ad", "clear")]:
            ty = ordinate(threshold)
            parts += [f'<line x1="{left}" y1="{ty}" x2="{right}" y2="{ty}" stroke="{color}" stroke-dasharray="5 5"/>']
        if rows:
            start = timestamp(rows[0]["timestamp"])
            points = " ".join(f'{left + (timestamp(r["timestamp"])-start).total_seconds()/300*(right-left):.1f},{ordinate(r[metric]):.1f}' for r in rows)
            parts += [f'<polyline points="{points}" fill="none" stroke="#64daca" stroke-width="3"/>']
        for minute in range(6):
            x = left + minute / 5 * (right - left)
            parts += [f'<text x="{x}" y="{y+height+22}" text-anchor="middle" font-size="11" fill="#a8bad3">{minute}m</text>']
    parts += ['<text x="48" y="676" font-size="12" fill="#a8bad3">Synthetic data · 23 Nov 2026, 09:00–09:05 UTC · alarm acknowledgement does not clear a fault</text>', '</g></svg>']
    return "\n".join(parts) + "\n"
