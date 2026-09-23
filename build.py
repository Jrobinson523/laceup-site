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

    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Built {out_path} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
