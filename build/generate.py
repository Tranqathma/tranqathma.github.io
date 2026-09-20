#!/usr/bin/env python3
"""
The site builder. Reads data/goals.json and data/site.json, writes every page.
The agents never touch HTML. They write data, this writes the site.

    python3 build/generate.py
"""
import datetime, html, json, pathlib, shutil

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"
OUT = ROOT            # the site lives at the repository root, so GitHub Pages works on its default setting
GOALS = json.loads((DATA / "goals.json").read_text(encoding="utf-8"))
SITE = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
CREW = json.loads((DATA / "crew.json").read_text(encoding="utf-8")) if (DATA / "crew.json").exists() else {"members": [], "messages": []}
BY_N = {g["n"]: g for g in GOALS}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Archivo:wdth,wght@62..125,100..900&"
         "family=Martian+Mono:wdth,wght@75..112.5,100..800&"
         "family=Newsreader:opsz,wght@6..72,200..700&display=swap")

PAGES = [("index.html", "Overview"), ("indices.html", "All Indices"),
         ("crew.html", "The Crew"), ("why.html", "Why the Goals"),
         ("about.html", "About"), ("contribute.html", "Contribute")]

STATUS_CLASS = {"major challenge": "bad", "declining": "bad", "improving": "good",
                "notable progress": "good", "slow": "warn"}


def pretty(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%d %B %Y").lstrip("0")


def e(x):
    return html.escape(str(x), quote=True)


def depth(path):
    return "../" if "/" in path else ""


def head(title, desc, path, accent=None):
    up = depth(path)
    acc = f"<style>:root{{--accent:{accent}}}</style>" if accent else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)} | TRANQATHMA</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}theme.css">
{acc}
</head><body>"""


def nav(current, path):
    up = depth(path)
    drop = "".join(
        f'<a href="{up}goals/{g["n"]:02d}.html" style="border-left-color:{g["hue"]}">'
        f'<i style="color:{g["hue"]}">{g["n"]:02d}</i><span>{e(g["title"])}</span></a>'
        for g in GOALS)
    def item(href, label):
        on = " on" if label == current else ""
        return f'<a class="{on.strip()}" href="{up}{href}">{label}</a>'
    goals_on = " on" if current == "Goals" else ""
    return f"""<div class="testing"><div class="w">
  <b>Under testing</b>
  <span>This register is being built and checked in public. Figures are not final and should not yet be cited.</span>
</div></div>
<header class="mast"><div class="w mast-in">
<a class="brand" href="{up}index.html">
  <span class="nm">Tranqathma</span>
  <span class="tg">Build it for Society</span>
</a>
<div class="stamp">
  <b>Register of the Seventeen Goals</b><br>
  India measured against the world<br>
  Updated {pretty(SITE['compiled'])}
</div>
</div></header>
<nav><div class="w"><div class="nav-in">
{item('index.html','Overview')}
{item('indices.html','All Indices')}
<details><summary class="{goals_on.strip()}">SDG Goals</summary><div class="drop">{drop}</div></details>
{item('crew.html','The Crew')}
{item('why.html','Why the Goals')}
{item('about.html','About')}
{item('contribute.html','Contribute')}
</div></div></nav>
<main>"""


def foot(path):
    up = depth(path)
    links = "".join(f'<a href="{up}{h}">{l}</a>' for h, l in PAGES)
    return f"""</main>
<footer><div class="w fgrid">
<div>
  <span class="nm" style="font-family:var(--exp);font-variation-settings:'wdth' 125;font-weight:800;
    font-size:19px;letter-spacing:.3em;text-transform:uppercase;color:var(--gold)">Tranqathma</span>
  <div class="fnote" style="margin-top:8px">Build it for Society<br>
  A non profit public register. Nothing on this site is for sale.</div>
</div>
<div>
  <div class="fnav">{links}</div>
  <div class="fnote" style="margin-top:14px">
  Every figure carries its source and the date it was read.<br>
  Where no admissible source exists, the cell is left blank.<br>
  Updated four times a day. Last updated {pretty(SITE['compiled'])}.</div>
</div>
</div></footer>
</body></html>"""


def ago(iso):
    then = datetime.datetime.fromisoformat(iso)
    mins = (datetime.datetime.now(then.tzinfo) - then).total_seconds() / 60
    if mins < 60:
        return f"{int(max(mins,1))} min ago"
    if mins < 1440:
        return f"{int(mins//60)} h ago"
    d = int(mins // 1440)
    return "yesterday" if d == 1 else f"{d} days ago"


def wire_items(up=""):
    """The scrolling strip. Pinned first, then newest."""
    msgs = sorted(CREW["messages"], key=lambda m: (not m.get("pinned"), m["at"]), reverse=False)
    msgs = [m for m in msgs if m.get("pinned")] + \
           [m for m in reversed(CREW["messages"]) if not m.get("pinned")]
    out = []
    for m in msgs[:14]:
        cam = ('<span class="wcam">photo</span>' if m.get("photo") else "")
        out.append(
            f'<span class="wi"><i style="background:{m["colour"]}"></i>'
            f'<b style="color:{m["colour"]}">{e(m["name"])}</b>'
            f'<span class="wt">{e(m["text"][:190])}</span>{cam}'
            f'<u>{ago(m["at"])}</u></span>')
    return "".join(out)


def pill(status):
    return f'<span class="pill {STATUS_CLASS.get(status,"")}">{e(status)}</span>'


# ---------------------------------------------------------------- overview
def page_overview():
    h = SITE["headline"]
    t = SITE["targets"]
    cards = []
    for g in GOALS:
        sc = g["india"]["score"]
        bar = f'<i style="background:{g["hue"]};width:{sc}%"></i>' if sc else ""
        val = (f'<b style="color:{g["hue"]}">{sc}</b><span>India score, 0 to 100</span>'
               if sc else '<b class="none">NOT PUBLISHED</b>'
                          '<span>no composite score at source</span>')
        cards.append(f"""<a class="gc" href="goals/{g['n']:02d}.html">
<span class="bar" style="background:{g['hue']}"></span>
<span class="in">
  <span class="num" style="color:{g['hue']}">{g['n']:02d}</span>
  <span class="ti">{e(g['title'])}</span>
  {pill(g['status'])}
  <span class="sc">{val}</span>
  <span class="track">{bar}</span>
</span></a>""")

    lead = SITE["warroom"][0]
    traj_rows = []
    for p in SITE["trajectory"]:
        style = ' style="color:var(--gold)"' if p["year"] == 2026 else ""
        traj_rows.append(f'<div class="tile"><span class="n fig"{style}>{p["rank"]}</span>'
                         f'<span class="lbl">rank in {p["year"]}</span></div>')
    traj = "".join(traj_rows)
    items = wire_items()
    wire = (f'''<div class="wire" aria-label="What the crew are saying">
  <div class="wire-tag"><span class="lbl">The Crew</span></div>
  <div class="wire-track"><div class="wire-run">{items}{items}</div></div>
  <a class="wire-more" href="crew.html">All &rarr;</a>
</div>''' if items else "")

    return f"""<div class="w hero">
<h1 class="xp">India is <em>{h['gap']} points</em> behind the best country on earth</h1>
<p class="sub">Seventeen goals. For each one this register carries India's official figure, the world
figure beside it, and the distance to the best any country has attained. Every number names the
document it came from and the day it was read. Where nothing admissible exists, the space is left empty.</p>
<div class="tiles">
  <div class="tile"><span class="n fig" style="color:var(--gold)">{h['india_index']}</span><span class="lbl">India, SDG index 2026</span></div>
  <div class="tile"><span class="n fig" style="color:var(--teal)">{h['best']['score']}</span><span class="lbl">{e(h['best']['country'])}, rank 1</span></div>
  <div class="tile"><span class="n fig">{SITE['niti']['score']}</span><span class="lbl">India's own index, from {SITE['niti']['first']} in {SITE['niti']['first_period']}</span></div>
  <div class="tile"><span class="n fig">{t['on_track']}%</span><span class="lbl">of India's targets on track</span></div>
  <div class="tile"><span class="n fig" style="color:var(--coral)">{t['worsened']}%</span><span class="lbl">of India's targets have worsened</span></div>
  <div class="tile"><span class="n fig">{SITE['world']['on_track_targets']}%</span><span class="lbl">of world targets on track</span></div>
</div>
</div>

{wire}

<section class="w">
  <div class="kick"><span class="n">In focus</span><span class="lbl">{pretty(SITE['compiled'])}</span></div>
  <h2 class="h2">{e(BY_N[lead['goal']]['title'])}</h2>
  <div class="reading" style="border-color:{BY_N[lead['goal']]['hue']}">
    <p>{e(BY_N[lead['goal']]['reading'])}</p>
    <div class="by"><a href="goals/{lead['goal']:02d}.html" style="color:var(--gold)">
      Read goal {lead['goal']:02d} in full &rarr;</a></div>
  </div>
</section>

<section class="w">
  <div class="kick"><span class="n">The register</span><span class="lbl">All seventeen goals</span></div>
  <h2 class="h2">Where India stands, goal by goal</h2>
  <div class="grid17">{"".join(cards)}</div>
  <p style="margin-top:22px;font-size:15px;color:var(--dim)">Scores are India's own composite for each
  goal, published by {e(SITE['niti']['source'])}. Six goals are not scored at source and are shown as
  such rather than filled in. Status labels are taken from {e(t['source'])} and attributed to it.</p>
</section>

<section class="w">
  <div class="kick"><span class="n">Movement</span><span class="lbl">India's world rank, four readings</span></div>
  <h2 class="h2">Eighteen places in eleven years</h2>
  <div class="tiles">{traj}</div>
  <p style="margin-top:20px">A lower number is a better position. The register carries the rank because
  it is what circulates, and the score beside it because a rank moves when other countries move and a
  score does not.</p>
</section>"""


# ---------------------------------------------------------------- goal page
def move_bar(ind, hue):
    if not ind or ind.get("prior") is None:
        return ""
    lo, hi = sorted([ind["value"], ind["prior"]])
    span = hi - lo if hi != lo else 1
    pad = span * 0.25
    left, right = lo - pad, hi + pad
    width = right - left

    def pos(v):
        return max(1, min(97, (v - left) / width * 100))
    a, b = pos(ind["prior"]), pos(ind["value"])
    f_l, f_w = min(a, b), abs(b - a)
    return f"""<div class="move">
  <span class="rail"></span>
  <span class="fill" style="left:{f_l}%;width:{f_w}%;background:{hue}"></span>
  <span class="mk" style="left:{a}%" data-l="{e(ind['prior_period'])}"></span>
  <span class="mk now" style="left:{b}%;background:{hue}" data-l="{e(ind['period'])}"></span>
</div>"""


def page_goal(g):
    hue = g["hue"]
    ind, ia = g["india_ind"], g["india"]

    if ia["score"]:
        prev = ia.get("prev")
        marker = f'<u style="left:{prev}%"></u>' if prev else ""
        prevtxt = (f'<span>from {prev} in {e(ia["prev_period"])}</span>' if prev else "")
        score_block = f"""<div class="score">
  <div class="v"><b>{ia['score']}</b>{prevtxt}</div>
  <div class="scbar"><i style="background:{hue};width:{ia['score']}%"></i>{marker}</div>
  <div class="scends"><span>0</span><span>India's composite score for this goal</span><span>100</span></div>
  <div style="margin-top:12px">{f'<span class="pill">{e(ia["band"])}</span>' if ia.get("band") else ""}</div>
  {f'<p style="margin:14px 0 0;font-size:14.5px;color:var(--dim)">{e(ia["note"])}</p>' if ia.get("note") else ""}
</div>"""
    else:
        score_block = f"""<div class="score">
  <div class="v"><b style="font-size:20px;color:var(--dimmer)">NOT PUBLISHED</b></div>
  <p style="margin:12px 0 0;font-size:14.5px;color:var(--dim)">
  {e(ia.get("note") or "A composite score for this goal is not published at source. The register does not compute a substitute.")}</p>
</div>"""

    if ind:
        extra_rows = []
        for x in g.get("india_extra") or []:
            note = f'{e(x["note"])} &middot; ' if x.get("note") else ""
            extra_rows.append(
                f'<div class="wrow"><span class="k">{e(x["label"])}</span>'
                f'<span class="v" style="color:{hue}">{e(x["value"])}</span>'
                f'<span class="nt">{note}{e(x["source"])}</span></div>')
        extra = "".join(extra_rows)
        prior = (f'<span>from {ind["prior"]} in {e(ind["prior_period"])}</span>'
                 if ind.get("prior") is not None else f'<span>{e(ind["period"])}</span>')
        ind_block = f"""<div class="ind">
  <div class="k">{e(ind['label'])}</div>
  <div class="val"><b style="color:{hue}">{ind['value']}</b>
    <span>{e(ind['unit'])}</span>{prior}</div>
  {move_bar(ind, hue)}
  {f'<p style="margin:10px 0 0;font-size:14px;color:var(--coral)">{e(ind["note"])}</p>' if ind.get("note") else ""}
  <p style="margin:12px 0 0;font-size:13px;color:var(--dimmer)">Source: {e(ind['source'])}</p>
  {f'<div class="wlist" style="margin-top:12px">{extra}</div>' if extra else ""}
</div>"""
    else:
        ind_block = """<div class="ind"><div class="k">Headline indicator</div>
  <p style="margin:10px 0 0;font-size:15px;color:var(--dimmer)">No admissible Indian source publishes a
  single headline figure for this goal, so none is shown.</p></div>"""

    if g["world"]:
        rows = "".join(
            f'<div class="wrow"><span class="k">{e(w["label"])}</span>'
            f'<span class="v">{e(w["value"])}</span>'
            f'<span class="nt">{e(w.get("note",""))}{" &middot; " if w.get("note") else ""}'
            f'{e(w.get("period",""))}{" &middot; " if w.get("period") else ""}{e(w["source"])}</span></div>'
            for w in g["world"])
        world_block = f'<div class="wlist">{rows}</div>'
    else:
        world_block = ('<p style="color:var(--dimmer);font-size:15px">No world figure has been ingested for '
                       'this goal. The space stays empty rather than being filled with an estimate.</p>')

    best_block = ""
    if g.get("best"):
        b = g["best"]
        best_block = f"""<div class="best">
  <span class="n">{b['value']}</span>
  <p><b style="color:var(--teal)">{e(b['country'])}</b> holds the best value any country has attained,
  in {e(b['period'])}. The register compares against what has been reached, never against a target,
  because an attained value cannot be dismissed as unrealistic. Source: {e(b['source'])}.</p>
</div>"""

    dispute_block = ""
    if ind and ind.get("dispute"):
        d = ind["dispute"]
        dispute_block = f"""<div class="dispute">
  <span class="lbl" style="color:var(--coral)">Sources disagree</span>
  <div class="n">{d['gap']}</div>
  <p>{e(ind['source'])} gives {ind['value']} for {e(ind['period'])}.
  {e(d['source'])} gives {d['value']} for {e(d['period'])}. The two differ by {d['gap']},
  and neither source discloses the other. Both are published here and no average is formed,
  because an average of two figures built by different methods over different periods is a
  third figure that no source supports.</p>
</div>"""

    nxt = BY_N[g["n"] + 1] if g["n"] < 17 else BY_N[1]
    prv = BY_N[g["n"] - 1] if g["n"] > 1 else BY_N[17]

    body = f"""<div class="w goalhead">
  <div class="row">
    <div class="big">{g['n']:02d}</div>
    <div>
      <h1>{e(g['title'])}</h1>
      <div style="margin-top:14px">{pill(g['status'])}</div>
      <p class="q">{e(g['question'])}</p>
    </div>
  </div>
</div>

<section class="w" style="border-top:0;padding-top:0">
  <div class="two">
    <div class="pan india">
      <h3>India, official</h3>
      {score_block}
      {ind_block}
    </div>
    <div class="pan">
      <h3>The world</h3>
      {world_block}
    </div>
  </div>
  {best_block}
  {dispute_block}
</section>

<section class="w">
  <div class="kick"><span class="n" style="color:{hue}">What this means</span>
    <span class="lbl">Reading of {pretty(SITE['compiled'])}</span></div>
  <div class="reading" style="border-color:{hue};margin-top:18px">
    <p>{e(g['reading'])}</p>
    <div class="by">Both sources above were read on {pretty(SITE['compiled'])}</div>
  </div>
</section>

<section class="w">
  <div class="meta">
    <div><span class="lbl">Indian source</span><p>{e(ind['source'] if ind else ia['source'])}</p></div>
    <div><span class="lbl">World source</span><p>{e(g['world'][0]['source']) if g['world'] else 'Not ingested'}</p></div>
    <div><span class="lbl">Last updated</span><p>{pretty(SITE['compiled'])}</p></div>
    <div><span class="lbl">Update frequency</span><p>Four times a day</p></div>
  </div>
  <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-top:28px">
    <a href="{prv['n']:02d}.html" class="cmd">&larr; {prv['n']:02d} {e(prv['title'])}</a>
    <a href="{nxt['n']:02d}.html" class="cmd">{nxt['n']:02d} {e(nxt['title'])} &rarr;</a>
  </div>
</section>"""
    return body


# ---------------------------------------------------------------- the crew
def page_crew():
    if not CREW["members"]:
        return """<div class="w hero">
<h1 class="xp">Four people, <em>working in the open</em></h1>
<p class="sub">The register is kept by four of us. What we say to each other while building it appears
here as it happens, unedited. It is here because a public record that hides its own workings has no
business asking anyone to trust it.</p>
<div class="waiting">
  <span class="lbl" style="color:var(--gold)">Nothing posted yet</span>
  <p>The crew has just been formed. The first four voices to speak take their place on this page, and
  what they say begins appearing here and on the strip across the front page.</p>
</div>
</div>"""
    cols = []
    for m in CREW["members"]:
        mine = [x for x in reversed(CREW["messages"]) if x["by"] == m["telegram_id"]]
        posts = []
        for x in mine[:40]:
            img = (f'<img src="{e(x["photo"])}" alt="" loading="lazy">' if x.get("photo") else "")
            pin = '<span class="pin">held</span>' if x.get("pinned") else ""
            posts.append(f"""<div class="post">
  <div class="pmeta"><time datetime="{e(x['at'])}">{ago(x['at'])}</time>{pin}</div>
  {f'<p>{e(x["text"])}</p>' if x['text'] else ''}
  {img}
</div>""")
        if not posts:
            posts.append('<div class="post"><p class="none">Nothing posted yet.</p></div>')
        initials = "".join(w[0] for w in m["name"].split()[:2]).upper()
        face = (f'<img class="face" src="{e(m["photo"])}" alt="">' if m.get("photo")
                else f'<span class="face" style="border-color:{m["colour"]};color:{m["colour"]}">{e(initials)}</span>')
        cols.append(f"""<div class="member">
  <div class="mhead" style="border-top-color:{m['colour']}">
    {face}
    <div>
      <b>{e(m['name'])}</b>
      <span>{e(m['role'])}</span>
    </div>
  </div>
  <div class="posts">{"".join(posts)}</div>
</div>""")

    total = len(CREW["messages"])
    return f"""<div class="w hero">
<h1 class="xp">Four people, <em>working in the open</em></h1>
<p class="sub">The register is kept by four of us. What follows is what we have actually said to each
other while building it, posted as it happened and not tidied up afterwards. It is here because a
public record that hides its own workings has no business asking anyone to trust it.</p>
<div class="tiles">
  <div class="tile"><span class="n fig" style="color:var(--gold)">{len(CREW['members'])}</span><span class="lbl">on the crew</span></div>
  <div class="tile"><span class="n fig">{total}</span><span class="lbl">messages on the record</span></div>
  <div class="tile"><span class="n fig">0</span><span class="lbl">edited after posting</span></div>
  <div class="tile"><span class="n fig">0</span><span class="lbl">paid to be here</span></div>
</div>
</div>
<section class="w" style="border-top:0;padding-top:0">
  <div class="crewgrid">{"".join(cols)}</div>
  <p style="margin-top:28px;font-size:15px;color:var(--dim)">Nothing on this page is a figure from the
  register. These are people talking. Anything any of us says here carries no more weight than any
  other reader's view, and none of it changes a number.</p>
</section>"""


# ---------------------------------------------------------------- indices
def page_indices():
    rows = []
    for g in GOALS:
        ind, ia = g["india_ind"], g["india"]
        iv = (f'<b style="color:{g["hue"]}">{ind["value"]}</b> <span style="color:var(--dimmer);'
              f'font-size:11px">{e(ind["unit"])}</span>' if ind else '<span class="na">NOT INGESTED</span>')
        wv = (f'{e(g["world"][0]["value"])} <span style="color:var(--dimmer);font-size:11px">'
              f'{e(g["world"][0]["label"].lower())}</span>' if g["world"]
              else '<span class="na">NOT INGESTED</span>')
        bv = (f'<b style="color:var(--teal)">{g["best"]["value"]}</b> '
              f'<span style="color:var(--dimmer);font-size:11px">{e(g["best"]["country"])}</span>'
              if g.get("best") else '<span class="na">NOT INGESTED</span>')
        sc = f'<b>{ia["score"]}</b>' if ia["score"] else '<span class="na">NOT PUBLISHED</span>'
        rows.append(f"""<tr>
  <td class="n" style="color:{g['hue']}">{g['n']:02d}</td>
  <td><a href="goals/{g['n']:02d}.html"><span class="gdot" style="background:{g['hue']}"></span>{e(g['title'])}</a></td>
  <td>{e(ind['label']) if ind else '<span class="na">none assigned</span>'}</td>
  <td class="n">{sc}</td>
  <td class="n">{iv}</td>
  <td class="n">{wv}</td>
  <td class="n">{bv}</td>
  <td>{pill(g['status'])}</td>
</tr>""")

    counted = sum(1 for g in GOALS if g["india_ind"])
    return f"""<div class="w hero">
<h1 class="xp">Every index on <em>one board</em></h1>
<p class="sub">India's own composite score, its headline indicator, the world figure and the best value
attained anywhere, for all seventeen goals. {counted} of 17 carry an Indian headline figure today.
The rest are blank, and blank means blank.</p>
</div>
<section class="w" style="border-top:0;padding-top:0">
<div class="scroll"><table>
<thead><tr>
<th>#</th><th>Goal</th><th>Headline indicator</th><th>India score</th>
<th>India value</th><th>World</th><th>Best attained</th><th>Status</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table></div>
<p style="margin-top:22px;font-size:15px;color:var(--dim)">India score is the composite published by
{e(SITE['niti']['source'])}, on a scale of 0 to 100. India value and World are different quantities on
different scales and are not comparable with each other across rows. They are comparable down a row,
which is the only comparison this board makes.</p>
</section>"""


# ---------------------------------------------------------------- prose pages
def page_why():
    return """<div class="w hero">
<h1 class="xp">Seventeen promises, <em>one clock</em></h1>
<p class="sub">In 2015 every country on earth signed the same list. Not a treaty and not a law, but a
public promise with a date on it: 2030. The Sustainable Development Goals are that list.</p>
</div>

<section class="w prose">
<h3>What the goals actually are</h3>
<p>They are seventeen ordinary human problems written down in order. Hunger. Water you can drink.
Whether a child finishes school. Whether a mother survives childbirth. Whether there is work worth
having. Whether the air and the sea and the soil survive the century. Nothing on the list is abstract,
and nothing on it is new. What was new in 2015 was the agreement to count.</p>

<h3>Why counting is the whole thing</h3>
<p>A promise with no number attached cannot fail, and a promise that cannot fail is not a promise. The
goals matter because each one carries indicators, and indicators can be measured, and measurements can
be compared across years and across countries. That is what turns an aspiration into an obligation.</p>
<p>It also means the goals can be quietly abandoned without anybody announcing it, simply by letting
the counting go unexamined. Worldwide, only 16.5 per cent of the targets are on track, and not one of
the seventeen goals is on course for 2030. Those two sentences are the reason this register exists.</p>

<h3>Why India, and why against the best</h3>
<p>India carries roughly one in six human beings. No global figure on this list moves very far without
India moving, which makes India's position on each goal a matter of consequence well beyond India.</p>
<p>This register compares India against the best value any country has attained, and never against a
target. A target is a promise and can be revised. An attained value is a fact about what a human
society has already reached, and it cannot be argued away. When Norway records one maternal death per
hundred thousand births, that number stops being an aspiration and becomes evidence about what is
possible.</p>

<h3>The part nobody says out loud</h3>
<p>Whoever supplies the benchmark holds power over the repair. A body that measures its own performance
has an interest in the result. A body that sells advice on closing the gap has an interest in the gap
being large. Between those two sits a space for somebody who sells nothing, advises no one, and shows
the arithmetic.</p>
<p>That space is small, unglamorous and almost entirely unoccupied. This register is an attempt to
occupy it.</p>
</section>"""


def page_about():
    return f"""<div class="w hero">
<h1 class="xp">A register that <em>sells nothing</em></h1>
<p class="sub">TRANQATHMA publishes this register on a not for profit basis. It carries no advertising,
accepts no payment for an entry or a ranking, and gives no body advance sight of a figure about itself.</p>
</div>

<section class="w prose">
<h3>The aim</h3>
<p>Build it for Society. Not a slogan bolted on afterwards, but the constraint the whole thing was
designed around. Everything here is free to read, free to reproduce and free to attack. The only thing
asked of a reader is that they check.</p>

<h3>How a figure gets onto this site</h3>
<p>Every goal is tied to two sources of record, one Indian and one international. Both are read four
times a day. A copy of each document is kept exactly as it was published, with the date it was read,
so that any figure on this site can be traced back to the page it came from on the day it came from it.</p>
<p>When a source publishes a new number, it is read out, checked a second time against the stored copy
by a separate route, and only then does it appear here. When the two checks disagree, nothing is
published and the problem is recorded. Everything a reader would call a judgment, as opposed to
arithmetic, is decided by a named person who answers for it.</p>

<h3>The rules this register holds itself to</h3>
<p><b>The indicator is named before the value is sought</b>, and is never swapped because the number it
produces is unflattering. <b>The comparator is the best attained value, never a target.</b> <b>Where two
admissible sources disagree, both are published</b> and neither is averaged away. <b>Where no admissible
source exists, the space is left blank</b>, with no estimate, no proxy and no carrying forward of last
year. <b>A correction is a new dated revision</b>, never a silent edit.</p>

<h3>Where it stands today</h3>
<p>The register is published by an individual author under the TRANQATHMA imprint. No entity is yet
incorporated and no money has been received from any party. The intended form is a Section 8 company,
which is prohibited by statute from distributing any surplus to its members, because a refusal of
payment is only believable when the legal form makes it structural rather than merely stated.</p>
<p>Every rupee ever received will be listed on this page, with the giver named and the date, before it
is spent.</p>

<h3>Corrections</h3>
<p>If you find an error in an input, a conversion, an indicator choice or a rule, send it. Accepted
corrections are published with the date and the name of whoever sent it. Rejected corrections are also
published, with the reason for rejection. A register that shows only what it accepted is asking to be
trusted. One that shows what it threw out is handing you the means to check it.</p>

<h3>Compiled</h3>
<p>Last updated {pretty(SITE['compiled'])}. Sources are read four times a day, at 06:00, 12:00, 18:00
and midnight, Indian Standard Time.</p>
</section>"""


def page_contribute():
    return """<div class="w hero">
<h1 class="xp">Checking is <em>the contribution</em></h1>
<p class="sub">This register does not ask for money. It asks for the one thing that actually makes a
public record trustworthy, which is somebody on the outside going through it and finding what is wrong.</p>
</div>

<section class="w prose">
<p>Every figure on this site names the document it came from and the day it was read. That is not
decoration. It is an invitation. Open the source, follow the arithmetic, and if the number does not
survive that, say so.</p>

<div class="acts">
  <div class="act"><div class="who">If you are a student</div>
    <p>Pick one goal. Open both its sources, the Indian and the international one, and read them against
    each other. You will find that they frequently do not agree, and almost none of them say so. Write
    down what you found and send it. That is a piece of real research, and it is publishable here with
    your name on it.</p></div>

  <div class="act"><div class="who">If you are a researcher</div>
    <p>Eight of the seventeen goals carry no Indian headline figure and three carry no world figure.
    Each of those gaps is a small, tractable, citable piece of work. Take one, establish the admissible
    source, and it goes into the register attributed to you.</p></div>

  <div class="act"><div class="who">If you work in an institution</div>
    <p>If your body holds a record that belongs on this list and publishes it in a form a machine cannot
    read, that is a fixable problem and the fix costs almost nothing. Tell us where the record lives and
    we will say precisely what shape would make it usable.</p></div>

  <div class="act"><div class="who">If you are a journalist</div>
    <p>Take any figure here and use it, free, with attribution. The disagreements are the story. Two
    competent bodies reporting different values for the same indicator over overlapping years, with
    neither acknowledging the other, is a pattern that repeats across this list.</p></div>

  <div class="act"><div class="who">If you are a citizen</div>
    <p>Read one goal page. Just one. Find the gap between what India records and what the best country
    on earth has already reached, and carry that number into whatever argument you were going to have
    anyway. An argument with a sourced number in it is a different argument.</p></div>

  <div class="act"><div class="who">If you found an error</div>
    <p>Send it. It gets published either way. If we accept it, it appears with the date and your name.
    If we reject it, it appears with the reason we rejected it. Both are on the record.</p></div>
</div>

<h3>What this register will never ask you for</h3>
<p>Not money, not an email address, not your attention on a schedule. There is no newsletter, no
membership and no campaign. The work either stands up to inspection or it does not, and inspection is
the only participation that changes anything here.</p>
</section>

<section class="w">
  <div class="kick"><span class="n">From the imprint</span><span class="lbl">A separate thing entirely</span></div>
  <h2 class="h2">Play DRISTA</h2>
  <p>The register takes no money, and that is not negotiable. DRISTA is something else. It is a game
  made under the same imprint, and it has nothing to do with the figures on this site.</p>
  <p>Play it in your browser. If it was worth something to you, pay what you think it was worth, and
  nothing if it was not. <b style="color:var(--gold)">Nothing anyone pays changes a single number
  anywhere on this site.</b> That line exists so that neither you nor anybody else ever has to wonder.</p>

  <div class="play">
    <div class="play-top">
      <span class="lbl" style="color:var(--gold)">TRANQATHMA &middot; DRISTA</span>
      <span class="lbl">Built in Godot</span>
      <span class="lbl">Plays in the browser, nothing to install</span>
      <span class="pill warn" style="margin-left:auto">Under construction</span>
    </div>
    <div class="play-frame">
      <div class="play-holder">
        <div class="gridlines"></div>
        <div class="play-msg">
          <div class="pt">DRISTA</div>
          <p>The playable build is being prepared. It will run here, in this frame, with no download
          and no account. Come back for the full release.</p>
        </div>
      </div>
    </div>
    <div class="play-foot">
      <div>
        <span class="lbl">Pay what you think it was worth</span>
        <p>Opens once the game does. There will be no minimum, no suggested amount and no reminder
        if you pay nothing.</p>
      </div>
      <span class="cmd" aria-disabled="true">Contribute &middot; available at release</span>
    </div>
  </div>
</section>"""


def page_warroom():
    props = ""
    for p in SITE["warroom"]:
        g = BY_N[p["goal"]]
        kind = ('<span class="pill bad">source break</span>' if p["kind"] == "break"
                else '<span class="pill warn">editorial</span>')
        props += f"""<div class="prop">
  <div class="top">
    <span class="lbl" style="color:{g['hue']}">{p['id']} &middot; goal {p['goal']:02d} {e(g['title'])}</span>
    {kind}
    <span class="lbl">weight <span class="weight"><i style="width:{p['weight']*100:.0f}%"></i></span>
      {p['weight']:.2f}</span>
    <span class="lbl" style="margin-left:auto">{e(p['raised_by'])}</span>
  </div>
  <div class="body">
    <h4>{e(p['proposal'])}</h4>
    <p>{e(p['why'])}</p>
  </div>
  <div class="acts2">
    <span class="cmd go">/publish {p['id']}</span>
    <span class="cmd">/hold {p['id']}</span>
    <span class="cmd no">/reject {p['id']}</span>
    <span class="cmd">/why {p['id']}</span>
  </div>
</div>"""

    return f"""<div class="w hero">
<h1 class="xp">War Room</h1>
<p class="sub">The Master Agent has read all seventeen goal agents and ranked what it believes deserves
the front page. Nothing below is public. Nothing below publishes until it is approved.</p>
<div class="tiles">
  <div class="tile"><span class="n fig">17</span><span class="lbl">goal agents reported</span></div>
  <div class="tile"><span class="n fig" style="color:var(--gold)">{len([p for p in SITE['warroom'] if p['state']=='awaiting'])}</span><span class="lbl">awaiting your decision</span></div>
  <div class="tile"><span class="n fig">1</span><span class="lbl">source break to resolve</span></div>
  <div class="tile"><span class="n fig">0</span><span class="lbl">published without approval</span></div>
</div>
</div>
<section class="w" style="border-top:0;padding-top:0">
  <div class="kick"><span class="n">Queue</span><span class="lbl">Oldest first</span></div>
  <h2 class="h2">Proposals for your decision</h2>
  {props}
  <p style="margin-top:26px;font-size:15px;color:var(--dim)">Mechanical changes do not appear here. When
  a source publishes a new number, the agent recomputes and the goal page updates on its own. Only
  judgment reaches this queue.</p>
</section>"""


# ---------------------------------------------------------------- write
def write(path, title, desc, nav_current, body, accent=None):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(head(title, desc, path, accent) + nav(nav_current, path) + body + foot(path),
                 encoding="utf-8")
    return p


def clean():
    """Remove only what this script produced. Never touch anything else."""
    for f in OUT.glob("*.html"):
        f.unlink()
    goals = OUT / "goals"
    if goals.exists():
        shutil.rmtree(goals)
    css = OUT / "theme.css"
    if css.exists():
        css.unlink()


def main():
    clean()
    shutil.copy(ROOT / "build" / "theme.css", OUT / "theme.css")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    n = 0
    write("index.html", "Overview",
          "India measured against the best country on earth across all seventeen Sustainable Development Goals.",
          "Overview", page_overview()); n += 1
    write("indices.html", "All Indices",
          "Every index the register tracks, on one board.", "All Indices", page_indices()); n += 1
    write("why.html", "Why the Goals",
          "What the seventeen Sustainable Development Goals are and why counting them matters.",
          "Why the Goals", page_why()); n += 1
    write("about.html", "About",
          "How a figure gets onto this register, and the rules it holds itself to.", "About", page_about()); n += 1
    write("contribute.html", "Contribute",
          "Checking the register is the contribution it asks for.", "Contribute", page_contribute()); n += 1
    write("crew.html", "The Crew",
          "The four people who keep this register, and what they have said while building it.",
          "The Crew", page_crew()); n += 1
    write("warroom.html", "War Room",
          "The Master Agent's queue, awaiting the curator's approval.", "Overview", page_warroom()); n += 1

    for g in GOALS:
        write(f"goals/{g['n']:02d}.html", f"Goal {g['n']:02d}, {g['title']}",
              g["question"], "Goals", page_goal(g), accent=g["hue"]); n += 1

    print(f"built {n} pages into {OUT}")
    print("  overview, indices, crew, why, about, contribute, warroom, and 17 goal pages")


if __name__ == "__main__":
    main()
