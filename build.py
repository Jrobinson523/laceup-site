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
            f'          <div class="status">{esc(p["dates"])}</div>\n'
            '        </div>'
        )
    return "\n".join(blocks)


def render_coach_blocks(coaches):
    blocks = []
    for c in coaches:
        initials = "".join(w[0] for w in c["name"].replace("Coach ", "").split()[:2]).upper()
        items = "\n".join(
            f'            <li>{esc(cr)}</li>' for cr in c["credentials"]
        )
        blocks.append(
            '      <div class="coach rise">\n'
            f'        <div class="coach-badge">{esc(initials)}</div>\n'
            '        <div>\n'
            f'          <h3>{esc(c["name"])}</h3>\n'
            '          <ul class="coach-credentials">\n'
            f'{items}\n'
            '          </ul>\n'
            '        </div>\n'
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


def main():
    data_path = os.path.join(ROOT, "data", "programs.json")
    testimonials_path = os.path.join(ROOT, "data", "testimonials.json")
    template_path = os.path.join(ROOT, "template.html")
    out_path = os.path.join(ROOT, "index.html")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(testimonials_path, "r", encoding="utf-8") as f:
        testimonials_data = json.load(f)
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    contact = data["contact"]
    seo = data["seo"]
    about = data["about"]

    replacements = {
        "{{TITLE}}": esc(seo["title"]),
        "{{DESCRIPTION}}": esc(seo["description"]),
        "{{CANONICAL}}": esc(seo["canonical"]),
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
    }

    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Built {out_path} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
