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

ROOT = os.path.dirname(os.path.abspath(__file__))


def esc(s):
    return html.escape(str(s), quote=True)


def render_program_cards(programs):
    blocks = []
    for p in programs:
        blocks.append(
            '        <div class="card rise">\n'
            f'          <h3>{esc(p["name"])}</h3>\n'
            f'          <p>{esc(p["blurb"])}</p>\n'
            '        </div>'
        )
    return "\n".join(blocks)


def render_coach_blocks(coaches):
    blocks = []
    for c in coaches:
        items = "\n".join(
            f'            <li>{esc(cr)}</li>' for cr in c["credentials"]
        )
        blocks.append(
            '      <div class="coach rise">\n'
            f'        <h3>{esc(c["name"])}</h3>\n'
            '        <ul class="coach-credentials">\n'
            f'{items}\n'
            '        </ul>\n'
            '      </div>'
        )
    return "\n".join(blocks)


def render_testimonial_cards(testimonials):
    blocks = []
    for t in testimonials:
        blocks.append(
            '      <figure class="testimonial rise">\n'
            f'        <blockquote>{esc(t["quote"])}</blockquote>\n'
            f'        <figcaption>{esc(t["voice"])}</figcaption>\n'
            '      </figure>'
        )
    return "\n".join(blocks)


def render_faq(faq):
    blocks = []
    pending_markers = ("coming soon",)
    for item in faq:
        is_pending = any(m in item["a"].lower() for m in pending_markers)
        p_class = ' class="pending"' if is_pending else ""
        blocks.append(
            '      <details class="rise">\n'
            f'        <summary>{esc(item["q"])}</summary>\n'
            f'        <p{p_class}>{esc(item["a"])}</p>\n'
            '      </details>'
        )
    return "\n".join(blocks)


def render_pillars(pillars):
    blocks = []
    for p in pillars:
        blocks.append(
            '        <div class="pillar rise">\n'
            f'          <h3>{esc(p["label"])}</h3>\n'
            f'          <p>{esc(p["body"])}</p>\n'
            '        </div>'
        )
    return "\n".join(blocks)


def render_placements_section(placements):
    if not placements:
        return ""
    rows = "\n".join(f'        <li>{esc(p)}</li>' for p in placements)
    return (
        '  <section class="section-tight" id="placements">\n'
        '    <div class="wrap">\n'
        '      <div class="section-head rise">\n'
        '        <h2>Where our players went.</h2>\n'
        '      </div>\n'
        '      <ul class="placements rise">\n'
        f'{rows}\n'
        '      </ul>\n'
        '    </div>\n'
        '  </section>\n'
    )


def render_photostrip(stills):
    tiles = []
    for s in stills:
        tiles.append(
            f'        <img src="{esc(s["image"])}" alt="{esc(s["alt"])}" loading="lazy" width="480" height="600">'
        )
    # duplicate the set once so the CSS marquee can loop seamlessly
    tiles_doubled = tiles + tiles
    return "\n".join(tiles_doubled)


def render_photostrip_grid(stills):
    blocks = []
    for s in stills:
        blocks.append(
            f'        <img src="{esc(s["image"])}" alt="{esc(s["alt"])}" loading="lazy" width="480" height="600">'
        )
    return "\n".join(blocks)


def render_ig_tiles(tiles):
    blocks = []
    for t in tiles:
        blocks.append(
            '        <a class="ig-tile" href="https://www.instagram.com/laceupsportsny" target="_blank" rel="noopener">\n'
            f'          <img src="{esc(t["image"])}" alt="{esc(t["alt"])}" loading="lazy" width="480" height="480">\n'
            '        </a>'
        )
    return "\n".join(blocks)


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

NAV = '''<header class="topnav"><div class="wrap topnav-inner">
<a href="/" class="wordmark">LACE UP</a>
<button type="button" class="nav-burger" id="navBurger" aria-label="Menu" aria-controls="nav-menu" aria-expanded="false"><span></span><span></span><span></span></button>
<nav id="nav-menu" class="nav-menu" aria-label="Primary">
<a href="/">Home</a><a href="/programs/">Programs</a><a href="/about/">About</a><a href="/testimonials/">Testimonials</a><a href="/contact/">Contact</a>
<a class="nav-book" href="/contact/#book">Book a Free Call</a></nav></div></header>'''

SCRIPT = '''<script>(function(){var b=document.getElementById('navBurger'),m=document.getElementById('nav-menu');
function c(){m.classList.remove('open');b.setAttribute('aria-expanded','false');}
b.addEventListener('click',function(){var o=m.classList.toggle('open');b.setAttribute('aria-expanded',o);});
m.querySelectorAll('a').forEach(function(a){a.addEventListener('click',c);});})();</script>
%s'''

CAL = '''<script>(function(){var k=document.getElementById('book');function l(){var s=document.createElement('script');s.src='https://assets.calendly.com/assets/external/widget.js';s.async=true;document.body.appendChild(s);}
if(!k||!window.IntersectionObserver){l();return;}var o=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting){o.disconnect();l();}});},{rootMargin:'300px'});o.observe(k);})();</script>'''

def shell(data, path, title, desc, h1, lede, body, extra_js=""):
    c = data["contact"]; canon = "https://www.trulaceup.com" + path
    tel = esc(c["phone_tel"]); disp = esc(c["phone_display"])
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
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
{schema(data)}
</head><body>
{NAV}
<main>
<section class="page-head"><div class="wrap">
<h1>{h1}</h1><p class="page-lede">{lede}</p>
<div class="cta-row"><a class="btn btn-primary" href="{'#book' if path=='/contact/' else '/contact/#book'}">Book a free discovery call</a><a class="btn btn-ghost" href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">DM us on Instagram</a></div>
<div class="hero-meta">{", ".join(data["towns"][:3])} &amp; Westchester, NY</div>
</div></section>
{body}
</main>
<footer><div class="wrap"><div class="foot-wordmark">LACE UP</div>
<div>Serving {", ".join(data["towns"][:-1])} and {data["towns"][-1]}, NY</div>
<div class="foot-row"><a href="{esc(c["instagram_url"])}" target="_blank" rel="noopener">{esc(c["instagram_handle"])}</a> &middot; <a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a></div></div></footer>
<nav class="sticky-bar" aria-label="Quick actions"><a href="{esc(c["instagram_url"])}" target="_blank" rel="noopener"><span class="sticky-icon">&#9993;</span>DM</a><a href="{'#book' if path=='/contact/' else '/contact/#book'}"><span class="sticky-icon">&#9679;</span>Book</a></nav>
{SCRIPT % extra_js}
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
    cards = "\n".join(f'<div class="card"><span class="season-tag">{tag}</span><h3>{n}</h3><p>{b}</p></div>' for n, tag, b, f in fmt)
    steps = ("<ol class=\"steps\"><li><strong>Book a free discovery call.</strong> Pick a time online, or call or text us.</li>"
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
<div class="cards">{cards}</div><p class="cards-note">{esc(data["programs_note"])}</p></div></section>
<section class="section-tight"><div class="wrap"><div class="section-head"><h2>How it works</h2></div>{steps}
<p class="fine">Families can train more than once a week, up to four days, and choose what fits their schedule.</p></div></section>
<section class="section-tight"><div class="wrap"><div class="section-head"><h2>Questions</h2></div>{faq}</div></section>''')

    # ---- Testimonials: verbatim only
    tcards = "\n".join(f'<figure class="testimonial"><blockquote>{esc(t["quote"])}</blockquote><figcaption>{esc(t["voice"])}</figcaption></figure>' for t in testimonials)
    pages["testimonials/index.html"] = shell(data, "/testimonials/",
        "Parent & Player Reviews | Lace Up Sports Basketball Training",
        "What parents and players say about Lace Up basketball training in Westchester, in their own words.",
        "What Lace Up families say", "Reviews from parents and players, word for word.",
        f'<section class="section-tight"><div class="wrap"><div class="testimonials">{tcards}</div></div></section>')

    # ---- About: live copy, typos already fixed in data
    coaches = "\n".join('<div class="coach"><h3>%s</h3><ul class="coach-credentials">%s</ul></div>' % (esc(k["name"]), "".join(f"<li>{esc(x)}</li>" for x in k["credentials"])) for k in data["coaches"])
    a = data["about"]
    pages["about/index.html"] = shell(data, "/about/",
        "About Lace Up Sports | Coaches Robinson & Dweck, Westchester Basketball",
        "Meet the Lace Up coaches: a 3x collegiate national champion head coach and a NYC PSAL city champion head coach, 65+ years of combined coaching.",
        "About Lace Up", "Two coaches. 65+ years of combined coaching experience.",
        f'''<section class="section-tight"><div class="wrap"><div class="about-copy"><h3>Our Organization</h3><p>{esc(a["org"])}</p><h3>Our Mission</h3><p>{esc(a["mission"])}</p><h3>Our Offer</h3><p>{esc(a["offer"])}</p></div>
<div class="coaches-wrap"><div class="bg-video-content">{coaches}</div></div></div></section>''')

    # ---- Contact / booking
    pages["contact/index.html"] = shell(data, "/contact/",
        "Book a Free Discovery Call | Lace Up Sports Basketball Training Westchester",
        f"Book a free discovery call with Lace Up Sports. Basketball training for players in {towns_s}. Email, DM or pick a time online.",
        "Book a free discovery call", "Pick a time below. A Lace Up coach will call you to talk through goals and get the player on the schedule.",
        f'''<section class="section-tight" id="book"><div class="wrap"><div class="book-embed"><div class="calendly-inline-widget" data-url="{esc(c["calendly_url"])}" style="min-width:280px;height:700px;"></div></div>
<p class="book-fallback">Widget not loading? Book at <a href="{esc(c["calendly_url"])}">{esc(c["calendly_url"])}</a>, or email <a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>.</p></div></section>
<section class="section-tight"><div class="wrap"><div class="contact-grid">
<a class="contact-item" href="mailto:{esc(c["email"])}"><span class="contact-label">Email</span>{esc(c["email"])}</a>
<a class="contact-item" href="{esc(c["instagram_url"])}" target="_blank" rel="noopener"><span class="contact-label">Instagram</span>{esc(c["instagram_handle"])}</a>
<div class="contact-item contact-item-static"><span class="contact-label">Serving</span>{towns_s}</div></div></div></section>''', CAL)

    # faq/ keeps a redirect (existing stub) -> programs
    for rel, body in pages.items():
        os.makedirs(os.path.join(root, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(root, rel), "w", encoding="utf-8").write(body)
    # sitemap
    urls = ["/"] + ["/" + r.rsplit("index.html", 1)[0] for r in pages]
    open(os.path.join(root, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>https://www.trulaceup.com{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print("pages:", ", ".join(pages))


def main():
    data_path = os.path.join(ROOT, "data", "programs.json")
    testimonials_path = os.path.join(ROOT, "data", "testimonials.json")
    placements_path = os.path.join(ROOT, "data", "placements.json")
    ig_path = os.path.join(ROOT, "data", "ig.json")
    photostrip_path = os.path.join(ROOT, "data", "photostrip.json")
    template_path = os.path.join(ROOT, "template.html")
    out_path = os.path.join(ROOT, "index.html")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(testimonials_path, "r", encoding="utf-8") as f:
        testimonials_data = json.load(f)
    with open(placements_path, "r", encoding="utf-8") as f:
        placements_data = json.load(f)
    with open(ig_path, "r", encoding="utf-8") as f:
        ig_data = json.load(f)
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
        "{{PHONE_TEL}}": esc(contact["phone_tel"]),
        "{{PHONE_DISPLAY}}": esc(contact["phone_display"]),
        "{{EMAIL}}": esc(contact["email"]),
        "{{INSTAGRAM_URL}}": esc(contact["instagram_url"]),
        "{{INSTAGRAM_HANDLE}}": esc(contact["instagram_handle"]),
        "{{CALENDLY_URL}}": esc(contact["calendly_url"]),
        "{{PROGRAM_CARDS}}": render_program_cards(data["programs"]),
        "{{COACH_BLOCKS}}": render_coach_blocks(data["coaches"]),
        "{{FAQ_ITEMS}}": render_faq(data["faq"]),
        "{{ABOUT_ORG}}": esc(about["org"]),
        "{{ABOUT_MISSION}}": esc(about["mission"]),
        "{{ABOUT_OFFER}}": esc(about["offer"]),
        "{{TESTIMONIAL_CARDS}}": render_testimonial_cards(testimonials_data["testimonials"]),
        "{{PILLARS}}": render_pillars(data["pillars"]),
        "{{PLACEMENTS_SECTION}}": render_placements_section(placements_data["placements"]),
        "{{PHOTOSTRIP_TRACK}}": render_photostrip(photostrip_data["stills"]),
        "{{PHOTOSTRIP_GRID}}": render_photostrip_grid(photostrip_data["stills"]),
        "{{IG_TILES}}": render_ig_tiles(ig_data["tiles"]),
        "{{RESOURCE_VIDEO}}": esc(resource["video"]),
        "{{RESOURCE_POSTER}}": esc(resource["poster"]),
        "{{RESOURCE_CAPTION}}": esc(resource["caption"]),
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
