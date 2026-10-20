#!/usr/bin/env python3
"""
Lace Up site builder — stdlib only, no deps.
Reads data/programs.json + template.html, writes index.html.
Idempotent: re-running produces byte-identical output for the same inputs.

Usage: python3 build.py
"""
import json
import html
import os
import hashlib, pathlib, re
CSS_V = hashlib.md5((pathlib.Path(__file__).parent / "styles.css").read_bytes()).hexdigest()[:8]  # cache-buster

ROOT = os.path.dirname(os.path.abspath(__file__))


def esc(s):
    return html.escape(str(s), quote=True)


FIG_RE = re.compile(r"^(\d[\w+\-]*)\s+(.*)$")


def split_fig(text):
    """A credential that opens with a figure (2000, 3-time, 35+) keeps that figure in the ledger column; the words stay verbatim."""
    m = FIG_RE.match(text)
    return (m.group(1), m.group(2)) if m else ("", text)


def render_program_rows(programs):
    rows = []
    for i, p in enumerate(programs):
        rows.append(
            f'        <li class="row" style="--i:{i}">\n'
            f'          <span class="fig">{esc(p["tag"])}</span>\n'
            f'          <div class="txt"><h3>{esc(p["name"])}</h3><p>{esc(p["blurb"])}</p></div>\n'
            '        </li>'
        )
    return "\n".join(rows)


def render_coach_blocks(coaches, tag="h3"):
    blocks = []
    for c in coaches:
        items = []
        for i, cr in enumerate(c["credentials"]):
            fig, rest = split_fig(cr)
            items.append(f'            <li class="row" style="--i:{i}"><span class="fig">{esc(fig)}</span><p class="txt-ink">{esc(rest)}</p></li>')
        blocks.append(
            '      <div class="coach">\n'
            f'        <{tag}>{esc(c["name"])}</{tag}>\n'
            '        <ol class="ledger" data-reveal>\n'
            + "\n".join(items) + '\n'
            '        </ol>\n'
            '      </div>'
        )
    return "\n".join(blocks)


def render_pull_quote(t):
    return ('      <figure class="pull">\n'
            f'        <blockquote>{esc(t["quote"])}</blockquote>\n'
            f'        <figcaption>{esc(t["voice"])}</figcaption>\n'
            '      </figure>')


def render_testimonial_rows(testimonials, only=None):
    rows = []
    if only is not None:
        testimonials = [testimonials[i] for i in only]
    for i, t in enumerate(testimonials):
        rows.append(f'        <li class="row" style="--i:{i}"><span class="fig">{esc(t["voice"])}</span><p>{esc(t["quote"])}</p></li>')
    return "\n".join(rows)


def render_faq(faq):
    blocks = []
    pending_markers = ("coming soon",)
    for item in faq:
        is_pending = any(m in item["a"].lower() for m in pending_markers)
        p_class = ' class="pending"' if is_pending else ""
        blocks.append(
            '      <details>\n'
            f'        <summary>{esc(item["q"])}</summary>\n'
            f'        <p{p_class}>{esc(item["a"])}</p>\n'
            '      </details>'
        )
    return "\n".join(blocks)


def render_pillars(pillars):
    rows = []
    for i, p in enumerate(pillars):
        rows.append(f'        <li class="row row-stack" style="--i:{i}"><span class="fig">{esc(p["label"])}</span><p>{esc(p["body"])}</p></li>')
    return "\n".join(rows)


def render_placements_section(placements):
    if not placements:
        return ""
    rows = "\n".join(f'        <li>{esc(p)}</li>' for p in placements)
    return (
        '  <section class="section-tight" id="placements">\n'
        '    <div class="wrap">\n'
        '      <div class="section-head">\n'
        '        <h2>Where our players went.</h2>\n'
        '      </div>\n'
        '      <ul class="placements">\n'
        f'{rows}\n'
        '      </ul>\n'
        '    </div>\n'
        '  </section>\n'
    )


def pic(src, alt, w, h, widths, sizes, cls="", lazy=True, extra=""):
    """<picture> with AVIF + WebP variants generated beside the JPEG (name-WIDTH.ext); JPEG fallback."""
    base = src.rsplit(".", 1)[0]
    base = base if base.startswith("/") else "/" + base
    srcj = src if src.startswith("/") else "/" + src
    av = ", ".join(f"{base}-{x}.avif {x}w" for x in widths)
    wb = ", ".join(f"{base}-{x}.webp {x}w" for x in widths)
    c = f' class="{cls}"' if cls else ""
    ld = ' loading="lazy"' if lazy else ' loading="eager" fetchpriority="high"'
    return (f'<picture><source type="image/avif" srcset="{av}" sizes="{sizes}"><source type="image/webp" srcset="{wb}" sizes="{sizes}">'
            f'<img{c} src="{srcj}" alt="{esc(alt)}" width="{w}" height="{h}"{ld} decoding="async"{extra}></picture>')


def render_photostrip(stills):
    """One set of tiles: a swipeable row on phones, a 3-up grid on wide screens (no marquee)."""
    tiles = []
    for s in stills:
        tiles.append("        " + pic(s["image"], s["alt"], 480, 600, [320, 480], "(max-width: 759px) 220px, (max-width: 1100px) 24vw, 260px"))
    return "\n".join(tiles)


# ---- sub-page generator (about/programs/testimonials/contact, schema, sitemap) ----

def schema(data):
    c = data["contact"]
    return ('<script type="application/ld+json">\n' + json.dumps({
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "SportsActivityLocation"],
        "name": "Lace Up Sports",
        "description": "Basketball training for youth and high school players in Westchester, NY.",
        "url": data["seo"]["canonical"],
        "email": c["email"],
        "image": data["seo"]["og_image_host"].rstrip("/") + "/assets/og.jpg",
        "sameAs": [c["instagram_url"]],
        "areaServed": [{"@type": "City", "name": t + ", NY"} for t in data["towns"]],
        "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": p["name"]}} for p in data["programs"]],
    }, separators=(",", ":")) + '\n</script>')

def nav(path):
    links = [("/", "Home"), ("/programs/", "Programs"), ("/about/", "About"), ("/testimonials/", "Testimonials"), ("/contact/", "Contact")]
    cur = ' aria-current="page"'
    items = "".join(f'<a href="{h}"{cur if h == path else ""}>{l}</a>' for h, l in links)
    book = "#book" if path == "/contact/" else "/contact/#book"
    jb = "" if path == "/contact/" else " js-book"
    return ('''<header class="topnav"><div class="wrap topnav-inner">
<a href="/" class="wordmark">LACE UP</a>
<button type="button" class="nav-burger" id="navBurger" aria-label="Menu" aria-controls="nav-menu" aria-expanded="false"><span></span><span></span><span></span></button>
<nav id="nav-menu" class="nav-menu" aria-label="Primary">
''' + items + '''
<a class="nav-book%s" href="%s">Book a free call</a></nav></div></header>''' % (jb, book))

SCRIPT = '''<script>(function(){var b=document.getElementById('navBurger'),m=document.getElementById('nav-menu');
function c(){m.classList.remove('open');b.setAttribute('aria-expanded','false');}
b.addEventListener('click',function(){var o=m.classList.toggle('open');b.setAttribute('aria-expanded',o);});
m.querySelectorAll('a').forEach(function(a){a.addEventListener('click',c);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m.classList.contains('open')){c();b.focus();}});})();</script>
<script>(function(){var k=document.querySelector('main .cta-row'),B=document.body;if(!k||!window.IntersectionObserver){B.classList.add('cta-passed');return;}new IntersectionObserver(function(e){var x=e[e.length-1];B.classList.toggle('cta-passed',!x.isIntersecting&&x.boundingClientRect.top<70);},{rootMargin:'-70px 0px 0px 0px'}).observe(k);})();</script>
<script>(function(){if(!window.IntersectionObserver)return;var L=document.querySelectorAll('.ledger[data-reveal]');if(!L.length)return;var o=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');o.unobserve(x.target);}});},{rootMargin:'0px 0px -10% 0px'});L.forEach(function(l){o.observe(l);});})();</script>
<script>(function(){var el=document.querySelector('[data-count]');if(!el||!window.IntersectionObserver||!window.requestAnimationFrame||matchMedia('(prefers-reduced-motion: reduce)').matches)return;if(el.getBoundingClientRect().top<innerHeight)return;var end=+el.getAttribute('data-count'),suf=el.getAttribute('data-suffix')||'';var o=new IntersectionObserver(function(e){if(!e[0].isIntersecting)return;o.disconnect();var t0=null,d=1100;function f(t){if(t0===null)t0=t;var p=Math.min(1,(t-t0)/d);p=1-Math.pow(1-p,3);el.textContent=Math.round(end*p)+suf;if(p<1)requestAnimationFrame(f);}requestAnimationFrame(f);},{threshold:.6});o.observe(el);})();</script>
<script>(function(){var A=document.querySelectorAll('.js-book');if(!A.length)return;var U='__CAL__',P=null;
function load(){if(P)return P;P=new Promise(function(ok,no){var l=document.createElement('link');l.rel='stylesheet';l.href='https://assets.calendly.com/assets/external/widget.css';document.head.appendChild(l);var s=document.createElement('script');s.src='https://assets.calendly.com/assets/external/widget.js';s.async=true;s.onload=ok;s.onerror=no;document.head.appendChild(s);});return P;}
function warm(){load().catch(function(){});}
A.forEach(function(a){a.addEventListener('pointerenter',warm,{once:true});a.addEventListener('focus',warm,{once:true});a.addEventListener('touchstart',warm,{once:true,passive:true});
a.addEventListener('click',function(e){if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||e.button)return;e.preventDefault();var h=a.getAttribute('href'),done=false;var t=setTimeout(function(){if(!done){done=true;location.href=h;}},2500);
load().then(function(){if(done||!window.Calendly)return;done=true;clearTimeout(t);window.Calendly.initPopupWidget({url:U});}).catch(function(){if(!done){done=true;clearTimeout(t);location.href=h;}});});});})();</script>
__EXTRA__'''

CAL = '''<script>(function(){var k=document.getElementById('book'),w=document.querySelector('.book-embed');function r(){if(w)w.classList.add('ready');}
function l(){var s=document.createElement('script');s.src='https://assets.calendly.com/assets/external/widget.js';s.async=true;s.onerror=r;document.body.appendChild(s);setTimeout(r,6000);}
window.addEventListener('message',function(e){if(/^https:\\/\\/([a-z0-9-]+\\.)*calendly\\.com$/.test(e.origin)&&e.data&&e.data.event==='calendly.event_type_viewed')r();});
if(!k||!window.IntersectionObserver){l();return;}var o=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting){o.disconnect();l();}});},{rootMargin:'300px'});o.observe(k);})();</script>'''

def cal_url(c):
    return c["calendly_url"] + "?hide_gdpr_banner=1&background_color=0b0b0b&text_color=f5f5f6&primary_color=eb9006"


def scripts(data, extra_js=""):
    return SCRIPT.replace("__CAL__", cal_url(data["contact"])).replace("__EXTRA__", extra_js)


def shell(data, path, title, desc, h1, lede, body, extra_js=""):
    c = data["contact"]; canon = "https://www.trulaceup.com" + path
    book = "#book" if path == "/contact/" else "/contact/#book"
    jb = "" if path == "/contact/" else " js-book"
    head_cta = "" if path == "/contact/" else f'<div class="cta-row"><a class="btn btn-primary{jb}" href="{book}">Book a free discovery call</a><a class="text-link" href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">DM us on Instagram</a></div>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="{esc(data["seo"]["robots"])}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="https://www.trulaceup.com/assets/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:url" content="{canon}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" sizes="180x180">
<meta name="theme-color" content="#0B0B0B"><meta property="og:site_name" content="Lace Up Sports">
<link rel="preload" as="font" type="font/woff2" href="/assets/fonts/syne-latin-vf.woff2" crossorigin>
<link rel="preconnect" href="https://assets.calendly.com">
<link rel="stylesheet" href="/styles.css?v={CSS_V}">
<script>document.documentElement.classList.add('js');</script>
{schema(data)}
</head><body>
{nav(path)}
<main>
<section class="page-head"><div class="wrap">
<h1>{h1}</h1><p class="page-lede">{lede}</p>
{head_cta}
<div class="hero-meta">{", ".join(data["towns"][:3])} &amp; Westchester, NY</div>
</div></section>
{body}
</main>
<footer><div class="wrap"><div class="foot-wordmark">LACE UP</div>
<nav class="foot-nav" aria-label="Pages"><a href="/programs/">Programs</a><a href="/about/">About</a><a href="/testimonials/">Testimonials</a><a href="/contact/">Contact</a></nav>
<div>Serving {", ".join(data["towns"][:-1])} and {data["towns"][-1]}, NY</div>
<div class="foot-row"><a href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">{esc(c["instagram_handle"])}</a><a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a></div></div></footer>
<nav class="sticky-bar" aria-label="Quick actions"><a href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">DM</a><a class="{jb.strip()}" href="{book}">Book a free call</a></nav>
{scripts(data, extra_js)}
</body></html>
'''

def build(root, data, testimonials):
    c = data["contact"]; towns = data["towns"]
    towns_s = ", ".join(towns[:-1]) + " and " + towns[-1]
    robots_note = data["seo"]["robots"]
    pages = {}

    # ---- Programs: real formats only (from live-site copy); gaps are flagged in the report, not invented
    fmt = [
     ("1:1 Private Training", "Individual", "One-on-one sessions focused on your game and your pace, with a coach watching every rep. Every session works on footwork, ball handling and shot mechanics.", ""),
     ("Small Group Training", "2-5 players", "Groups of 2 to 5 players. The same individual attention as 1:1, with shared reps and built-in competition.", ""),
     ("Team &amp; Squad Sessions", "Team", "Bring your team or AAU squad in for skill work and conditioning.", ""),
     ("Clinics", "Clinic", "Multi-week clinics for players building fundamentals, at every level.", ""),
    ]
    cards = "\n".join(f'<li class="row" style="--i:{i}"><span class="fig">{tag}</span><div class="txt"><h3>{n}</h3><p>{b}</p></div></li>' for i, (n, tag, b, f) in enumerate(fmt))
    steps = ("<ol class=\"steps\"><li><strong>Book a free discovery call.</strong> Pick a time online, or DM us on Instagram.</li>"
             "<li><strong>Talk goals.</strong> A Lace Up coach calls you. We ask about the player's level, goals and schedule.</li>"
             "<li><strong>Get on the schedule.</strong> We match the player to 1:1, small group, team or clinic. Pricing is covered on the call.</li></ol>")
    def fa(a):
        a = esc(a).replace("Book a free discovery call below,", "Book a free discovery call,")
        return a.replace("Full lists are in the About section.", 'Full lists are on the <a href="/about/">About page</a>.')
    faq = "\n".join('<details><summary>%s</summary><p>%s</p></details>' % (esc(i["q"]), fa(i["a"])) for i in data["faq"])
    pages["programs/index.html"] = shell(data, "/programs/",
        "Basketball Programs: 1:1, Small Group, Team | Lace Up Sports Westchester",
        f"Individual, small-group (2-5 players), team and clinic basketball training for players in {towns_s}. Start with a free discovery call.",
        "Basketball training programs", f"Four ways to train with Lace Up, for players from beginner through varsity and AAU in {towns_s}.",
        f'''<section class="section-tight"><div class="wrap"><div class="section-head"><h2>Pick your format</h2><span class="season-tag">{esc(data["season_tag"])}</span></div>
<ol class="ledger" data-reveal>{cards}</ol><p class="cards-note">{esc(data["programs_note"])}</p></div></section>
<section class="section-tight"><div class="wrap"><div class="section-head"><h2>How booking works</h2></div>{steps}
<p class="fine">Families can train more than once a week, up to four days, and choose what fits their schedule.</p></div></section>
<section class="section-tight" id="resources"><div class="wrap"><div class="section-head"><h2>Free resource: a drill from a session</h2></div>
<div class="resource-block"><video class="resource-video" muted loop playsinline controls poster="/{esc(data["resource"]["poster"])}" preload="none" width="1280" height="720"><source src="/{esc(data["resource"]["video"])}" type="video/mp4"></video>
<p class="resource-caption">{esc(data["resource"]["caption"])}</p></div></div></section>
<section class="section-tight"><div class="wrap"><div class="section-head"><h2>Questions</h2></div>{faq}</div></section>
<section class="section book-band"><div class="wrap"><h2>Book a free discovery call</h2><p class="band-sub">Pick a time online. A Lace Up coach calls you to talk through goals and get the player on the schedule.</p><div class="cta-row"><a class="btn btn-primary js-book" href="/contact/#book">Pick a time</a></div></div></section>''')

    # ---- Testimonials: verbatim only
    tcards = render_pull_quote(testimonials[1]) + '\n<ol class="ledger ledger-quotes" data-reveal>\n' + render_testimonial_rows(testimonials, only=[4, 2, 3, 0, 5]) + '\n</ol>'
    pages["testimonials/index.html"] = shell(data, "/testimonials/",
        "Parent & Player Reviews | Lace Up Sports Basketball Training",
        "What parents and players say about Lace Up basketball training in Westchester, in their own words.",
        "What Lace Up families say", "Reviews from parents and players, word for word.",
        f'<section class="section-tight"><div class="wrap">{tcards}</div></section>'
        '<section class="section book-band"><div class="wrap"><h2>Book a free discovery call</h2><p class="band-sub">Pick a time online. A Lace Up coach calls you to talk through goals and get the player on the schedule.</p><div class="cta-row"><a class="btn btn-primary js-book" href="/contact/#book">Pick a time</a></div></div></section>')

    # ---- About: live copy, typos already fixed in data
    coaches = render_coach_blocks(data["coaches"], tag="h2")
    a = data["about"]
    pages["about/index.html"] = shell(data, "/about/",
        "About Lace Up Sports | Coaches Robinson & Dweck, Westchester Basketball",
        "Meet the Lace Up coaches: a 3x collegiate national champion head coach and a NYC PSAL city champion head coach, 65+ years of combined coaching.",
        "About Lace Up", "Two coaches. 65+ years of combined coaching experience.",
        f'''<section class="section-tight"><div class="wrap"><div class="about-copy"><h2>Our Organization</h2><p>{esc(a["org"])}</p><h2>Our Mission</h2><p>{esc(a["mission"])}</p><h2>Our Offer</h2><p>{esc(a["offer"])}</p></div>
<div class="record">{coaches}</div></div></section>
<section class="section book-band"><div class="wrap"><h2>Book a free discovery call</h2><p class="band-sub">Pick a time online. A Lace Up coach calls you to talk through goals and get the player on the schedule.</p><div class="cta-row"><a class="btn btn-primary js-book" href="/contact/#book">Pick a time</a></div></div></section>''')

    # ---- Contact / booking
    pages["contact/index.html"] = shell(data, "/contact/",
        "Book a Free Discovery Call | Lace Up Sports Basketball Training Westchester",
        f"Book a free discovery call with Lace Up Sports. Basketball training for players in {towns_s}. Email, DM or pick a time online.",
        "Book a free discovery call", "Pick a time below. A Lace Up coach will call you to talk through goals and get the player on the schedule.",
        f'''<section class="section-tight" id="book"><div class="wrap">
<div class="book-embed"><div class="book-skeleton" aria-hidden="true"><div class="book-skeleton-head"><span>Pick a time</span><span>Free discovery call</span></div><div class="book-skeleton-grid">{"<span></span>" * 35}</div></div>
<p class="book-fallback">Widget not loading? Book at <a href="{esc(c["calendly_url"])}">{esc(c["calendly_url"])}</a>, or email <a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>.</p>
<div class="calendly-inline-widget" data-url="{esc(cal_url(c))}" style="min-width:280px;height:700px;"></div></div></div></section>
<section class="section-tight"><div class="wrap"><ol class="ledger ledger-contact" data-reveal>
<li class="row row-stack" style="--i:0"><span class="fig">Email</span><a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a></li>
<li class="row row-stack" style="--i:1"><span class="fig">Instagram</span><a href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">{esc(c["instagram_handle"])}</a></li>
<li class="row row-stack" style="--i:2"><span class="fig">Serving</span><p class="txt-ink">{towns_s}</p></li></ol></div></section>''', CAL)

    # faq/ keeps a redirect (existing stub) -> programs
    for rel, body in pages.items():
        os.makedirs(os.path.join(root, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(root, rel), "w", encoding="utf-8").write(body)
    # sitemap
    urls = ["/"] + ["/" + r.rsplit("index.html", 1)[0] for r in pages]
    open(os.path.join(root, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>https://www.trulaceup.com{u}</loc><lastmod>{data['seo']['lastmod']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    print("pages:", ", ".join(pages))


def main():
    data_path = os.path.join(ROOT, "data", "programs.json")
    testimonials_path = os.path.join(ROOT, "data", "testimonials.json")
    placements_path = os.path.join(ROOT, "data", "placements.json")
    photostrip_path = os.path.join(ROOT, "data", "photostrip.json")
    template_path = os.path.join(ROOT, "template.html")
    out_path = os.path.join(ROOT, "index.html")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(testimonials_path, "r", encoding="utf-8") as f:
        testimonials_data = json.load(f)
    with open(placements_path, "r", encoding="utf-8") as f:
        placements_data = json.load(f)
    with open(photostrip_path, "r", encoding="utf-8") as f:
        photostrip_data = json.load(f)
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    contact = data["contact"]
    seo = data["seo"]
    about = data["about"]
    resource = data["resource"]
    # NOTE: flip data["season_tag"] in data/programs.json each January.
    og_image_url = seo["og_image_host"].rstrip("/") + "/assets/og.jpg"

    replacements = {
        "{{TITLE}}": esc(seo["title"]),
        "{{DESCRIPTION}}": esc(seo["description"]),
        "{{CANONICAL}}": esc(seo["canonical"]),
        "{{OG_IMAGE_URL}}": esc(og_image_url),
        "{{ROBOTS}}": esc(seo["robots"]),
        "{{SEASON_TAG}}": esc(data["season_tag"]),
        "{{PROGRAMS_NOTE}}": esc(data["programs_note"]),
        "{{EMAIL}}": esc(contact["email"]),
        "{{CSS_V}}": CSS_V,
        "{{INSTAGRAM_URL}}": esc(contact["instagram_url"]),
        "{{INSTAGRAM_HANDLE}}": esc(contact["instagram_handle"]),
        "{{PROGRAM_ROWS}}": render_program_rows(data["programs"]),
        "{{COACH_BLOCKS}}": render_coach_blocks(data["coaches"]),
        "{{FAQ_ITEMS}}": render_faq(data["faq"]),
        "{{PULL_QUOTE}}": render_pull_quote(testimonials_data["testimonials"][1]),
        "{{TESTIMONIAL_ROWS}}": render_testimonial_rows(testimonials_data["testimonials"], only=[4, 3]),
        "{{SCRIPTS}}": scripts(data),
        "{{TOWNS}}": esc(", ".join(data["towns"][:-1]) + " and " + data["towns"][-1]),
        "{{PILLARS}}": render_pillars(data["pillars"]),
        "{{PLACEMENTS_SECTION}}": render_placements_section(placements_data["placements"]),
        "{{PHOTOSTRIP_TRACK}}": render_photostrip(photostrip_data["stills"]),
    }

    replacements["{{SCHEMA}}"] = schema(data)
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Built {out_path} ({len(out)} bytes)")
    build(ROOT, data, testimonials_data["testimonials"])


if __name__ == "__main__":
    main()
