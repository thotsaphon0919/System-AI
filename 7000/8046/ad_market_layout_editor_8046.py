from __future__ import annotations

import html
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "ad_market_uploads"
CONFIG_FILE = BASE_DIR / "ad_market_page_config.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

BLOCKS = ["hero", "titlebar", "video", "search", "chips", "categories"]
BLOCK_LABELS = {
    "hero": "รูปใหญ่ด้านบน",
    "titlebar": "แถบหัวข้อ AD MARKET",
    "video": "วิดีโอเล่าเรื่อง",
    "search": "ช่องค้นหา",
    "chips": "ปุ่มหมวดแนวนอน",
    "categories": "การ์ดหมวดโฆษณา",
}

CATEGORIES = [
    ("tech", "Tech & Gadget", "TECH", "◈"),
    ("fashion", "Fashion", "STYLE", "◇"),
    ("auto", "Auto & Vehicle", "AUTO", "⬡"),
    ("food", "Food & Drink", "FOOD", "◉"),
    ("game", "Game & Entertainment", "GAME", "✦"),
    ("finance", "Finance & Investment", "FIN", "◆"),
    ("travel", "Travel & Hotel", "TRAVEL", "△"),
    ("education", "Education", "EDU", "□"),
    ("lifestyle", "Lifestyle", "LIFE", "∞"),
]


def _default_config() -> dict[str, Any]:
    return {
        # fields from the old ad_market_upload_panel are kept for compatibility
        "image": "",
        "enter_link": "/tower/dashboard",
        "earn_link": "/tower/ad-market",
        "reward_link": "/tower/rewards",
        # editor fields
        "video": "",
        "order": BLOCKS.copy(),
        "enabled": {name: True for name in BLOCKS},
        "title": "AD MARKET",
        "subtitle": "เลือกหมวดโฆษณาที่สนใจ ดูครบตามเวลา แล้วรับ INF",
        "video_title": "ทำกิจกรรม • รับ INF • ปลดล็อกสิทธิ์",
        "video_subtitle": "คลิปสั้นช่วยเล่าเส้นทางก่อนเริ่มเลือกกิจกรรม",
        "video_link": "",
        "category_title": "เลือกหมวดโฆษณา",
        "category_note": "แตะเพื่อดูแคมเปญ",
        "hero_height": 520,
        "title_height": 102,
        "video_height": 220,
        "hero_fit": "cover",
        "video_fit": "cover",
        "background": "#000000",
        "accent": "#a83cff",
    }


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _safe_color(value: Any, default: str) -> str:
    value = str(value or "").strip()
    if len(value) == 7 and value.startswith("#") and all(ch in "0123456789abcdefABCDEF" for ch in value[1:]):
        return value
    return default


def _safe_fit(value: Any) -> str:
    return "contain" if str(value) == "contain" else "cover"


def load_config() -> dict[str, Any]:
    cfg = _default_config()
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass

    order = cfg.get("order")
    if not isinstance(order, list):
        order = []
    clean_order = [name for name in order if name in BLOCKS]
    clean_order.extend(name for name in BLOCKS if name not in clean_order)
    cfg["order"] = clean_order

    enabled = cfg.get("enabled")
    if not isinstance(enabled, dict):
        enabled = {}
    cfg["enabled"] = {name: bool(enabled.get(name, True)) for name in BLOCKS}

    cfg["hero_height"] = _clamp_int(cfg.get("hero_height"), 200, 760, 520)
    cfg["title_height"] = _clamp_int(cfg.get("title_height"), 72, 180, 102)
    cfg["video_height"] = _clamp_int(cfg.get("video_height"), 130, 460, 220)
    cfg["hero_fit"] = _safe_fit(cfg.get("hero_fit"))
    cfg["video_fit"] = _safe_fit(cfg.get("video_fit"))
    cfg["background"] = _safe_color(cfg.get("background"), "#000000")
    cfg["accent"] = _safe_color(cfg.get("accent"), "#a83cff")
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_FILE.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _media_url(filename: str) -> str:
    return f"/tower/ad-market-layout-media/{_esc(Path(filename).name)}" if filename else ""


def _file_path(filename: str) -> Path | None:
    if not filename:
        return None
    target = UPLOAD_DIR / Path(filename).name
    return target if target.exists() and target.is_file() else None


def _hero_block(cfg: dict[str, Any]) -> str:
    image = str(cfg.get("image") or "")
    target = _file_path(image)
    if target:
        media = f'<img src="{_media_url(image)}" alt="INFINI AD MARKET">'
    else:
        media = '<div class="adle-hero-empty"><b>INFINI ∞</b><span>อัปโหลดรูปใหญ่จากปุ่มเฟือง</span></div>'

    return f"""
    <section class="adle-hero" style="--hero-h:{int(cfg['hero_height'])}px;--hero-fit:{cfg['hero_fit']}">
      {media}
      <a class="adle-hotspot adle-hotspot-enter" href="{_esc(cfg.get('enter_link'))}" aria-label="Enter Tower"></a>
      <a class="adle-hotspot adle-hotspot-earn" href="{_esc(cfg.get('earn_link'))}" aria-label="Earn"></a>
      <a class="adle-hotspot adle-hotspot-reward" href="{_esc(cfg.get('reward_link'))}" aria-label="Rewards"></a>
    </section>
    """


def _titlebar_block(cfg: dict[str, Any], user_points: int) -> str:
    title = _esc(cfg.get("title"))
    subtitle = _esc(cfg.get("subtitle"))
    return f"""
    <section class="adle-titlebar" style="--title-h:{int(cfg['title_height'])}px">
      <div class="adle-title-main"><small>INFINI ACTIVITY POINT</small><h1>{title}</h1></div>
      <p>{subtitle}</p>
      <div class="adle-points"><small>MY POINT</small><strong>{int(user_points):,} INF</strong></div>
    </section>
    """


def _video_block(cfg: dict[str, Any]) -> str:
    video = str(cfg.get("video") or "")
    target = _file_path(video)
    video_link = str(cfg.get("video_link") or "").strip()
    if target:
        media = f'<video class="adle-video" src="{_media_url(video)}" autoplay muted loop playsinline preload="metadata"></video>'
    else:
        media = '<div class="adle-video-empty"><b>▶</b><span>อัปโหลดวิดีโอสั้นจากเครื่องมือจัดหน้า</span></div>'

    if video_link:
        media = f'<a class="adle-video-link" href="{_esc(video_link)}">{media}</a>'

    return f"""
    <section class="adle-story" style="--video-h:{int(cfg['video_height'])}px;--video-fit:{cfg['video_fit']}">
      <div class="adle-story-media">{media}<button class="adle-sound" type="button" onclick="adleToggleSound(this)" aria-label="เปิดหรือปิดเสียง">🔇</button></div>
      <div class="adle-story-copy"><strong>{_esc(cfg.get('video_title'))}</strong><span>{_esc(cfg.get('video_subtitle'))}</span></div>
    </section>
    """


def _search_block() -> str:
    return """
    <label class="adle-search"><span>⌕</span><input id="adleSearch" type="search" placeholder="ค้นหาหมวดโฆษณา..."></label>
    """


def _chips_block() -> str:
    chips = ['<button class="active" type="button" data-filter="">ทั้งหมด</button>']
    for key, _name, short, _icon in CATEGORIES:
        chips.append(f'<button type="button" data-filter="{_esc(key)}">{_esc(short)}</button>')
    return '<nav class="adle-chips">' + "".join(chips) + "</nav>"


def _categories_block(cfg: dict[str, Any]) -> str:
    cards = []
    for key, name, short, icon in CATEGORIES:
        cards.append(f"""
        <a class="adle-card" data-key="{_esc(key)}" data-name="{_esc(name.lower())}" href="/tower/ad-market/{_esc(key)}">
          <div class="adle-card-art"><span>{_esc(icon)}</span><small>{_esc(short)}</small></div>
          <div class="adle-card-copy"><h3>{_esc(name)}</h3><p>เปิดดูรายการและกิจกรรม</p></div>
          <footer><span>เข้าแคมเปญ</span><b>→</b></footer>
        </a>
        """)
    return f"""
    <section class="adle-categories">
      <div class="adle-section-head"><h2>{_esc(cfg.get('category_title'))}</h2><span>{_esc(cfg.get('category_note'))}</span></div>
      <div class="adle-grid">{''.join(cards)}</div>
    </section>
    """


def render_ad_market_page(page_func, user_points: int):
    cfg = load_config()
    renderers = {
        "hero": lambda: _hero_block(cfg),
        "titlebar": lambda: _titlebar_block(cfg, user_points),
        "video": lambda: _video_block(cfg),
        "search": _search_block,
        "chips": _chips_block,
        "categories": lambda: _categories_block(cfg),
    }
    blocks = []
    for name in cfg["order"]:
        if cfg["enabled"].get(name, True):
            blocks.append(renderers[name]())

    content = f"""
    <style>
      .wrap > header{{display:none}}
      html,body{{background:{cfg['background']}!important}}
      body{{background-image:none!important}}
      .wrap{{max-width:760px!important;padding:0 14px 110px!important}}
      .adle,.adle *{{box-sizing:border-box}}
      .adle{{--accent:{cfg['accent']};color:#fff;padding-top:0}}
      .adle-hero{{position:relative;width:100%;height:var(--hero-h);overflow:hidden;margin:0 0 14px;border:1px solid color-mix(in srgb,var(--accent) 54%,transparent);border-radius:0 0 28px 28px;background:#050507;box-shadow:0 18px 44px rgba(0,0,0,.44)}}
      .adle-hero img{{width:100%;height:100%;display:block;object-fit:var(--hero-fit)}}
      .adle-hero-empty{{height:100%;display:grid;place-content:center;gap:8px;text-align:center;background:radial-gradient(circle at 50% 25%,color-mix(in srgb,var(--accent) 42%,transparent),transparent 32%),#06060a}}
      .adle-hero-empty b{{font-size:34px}}.adle-hero-empty span{{color:#9895a5;font-size:12px}}
      .adle-hotspot{{position:absolute;bottom:2%;height:11%;border-radius:14px}}.adle-hotspot-enter{{left:36%;width:28%}}.adle-hotspot-earn{{left:3%;width:29%}}.adle-hotspot-reward{{right:3%;width:29%}}
      .adle-titlebar{{min-height:var(--title-h);display:grid;grid-template-columns:minmax(0,1fr) minmax(120px,1.4fr) auto;align-items:center;gap:14px;margin:0 0 14px;padding:15px 17px;border:1px solid color-mix(in srgb,var(--accent) 34%,transparent);border-radius:21px;background:radial-gradient(circle at 85% 10%,color-mix(in srgb,var(--accent) 20%,transparent),transparent 34%),#08090e}}
      .adle-title-main small{{display:block;color:#8d8998;font-size:8px;font-weight:900;letter-spacing:1.3px}}.adle-title-main h1{{margin:4px 0 0;font-size:clamp(22px,7vw,36px);line-height:.94;letter-spacing:-1px}}
      .adle-titlebar>p{{margin:0;color:#aaa7b5;font-size:11px;line-height:1.45}}
      .adle-points{{padding:9px 11px;border:1px solid rgba(79,218,255,.24);border-radius:14px;background:#070b10;color:#68deff;text-align:right;white-space:nowrap}}.adle-points small{{display:block;color:#85818f;font-size:8px;letter-spacing:1px}}.adle-points strong{{font-size:15px}}
      .adle-story{{overflow:hidden;margin:0 0 14px;border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);border-radius:22px;background:#07080d}}
      .adle-story-media{{position:relative;height:var(--video-h);overflow:hidden;background:#020204}}.adle-video-link{{display:block;width:100%;height:100%}}.adle-video{{width:100%;height:100%;display:block;object-fit:var(--video-fit);background:#000}}
      .adle-video-empty{{height:100%;display:grid;place-content:center;gap:8px;text-align:center;background:radial-gradient(circle at 50% 50%,color-mix(in srgb,var(--accent) 28%,transparent),transparent 36%),#050509}}.adle-video-empty b{{font-size:34px;color:#d178ff}}.adle-video-empty span{{color:#8c8997;font-size:11px}}
      .adle-sound{{position:absolute;right:11px;bottom:11px;width:38px;height:38px;border:1px solid rgba(255,255,255,.17);border-radius:50%;background:rgba(3,3,7,.72);color:#fff;font-size:16px}}
      .adle-story-copy{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px}}.adle-story-copy strong{{font-size:13px}}.adle-story-copy span{{color:#858290;font-size:10px;text-align:right}}
      .adle-search{{display:flex;height:52px;margin:0 0 11px;padding:0 15px;align-items:center;gap:10px;border:1px solid color-mix(in srgb,var(--accent) 26%,transparent);border-radius:18px;background:#08090e}}.adle-search span{{color:#6fe3ff;font-size:21px}}.adle-search input{{width:100%;margin:0;border:0;outline:0;background:transparent;color:#fff;font:inherit}}.adle-search input::placeholder{{color:#716e7c}}
      .adle-chips{{display:flex;gap:8px;margin:0 0 13px;padding:0 0 3px;overflow-x:auto;scrollbar-width:none}}.adle-chips::-webkit-scrollbar{{display:none}}.adle-chips button{{flex:0 0 auto;padding:10px 16px;border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);border-radius:999px;background:#0c0d13;color:#c7c4d0;font-weight:900}}.adle-chips button.active{{border-color:transparent;background:linear-gradient(135deg,var(--accent),#7430ff);color:#fff}}
      .adle-section-head{{display:flex;align-items:end;justify-content:space-between;gap:10px;margin:19px 2px 12px}}.adle-section-head h2{{margin:0;font-size:24px}}.adle-section-head span{{color:#807d89;font-size:10px}}
      .adle-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}.adle-card{{min-height:226px;display:flex;flex-direction:column;overflow:hidden;padding:12px;border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);border-radius:21px;background:radial-gradient(circle at 75% 15%,color-mix(in srgb,var(--accent) 20%,transparent),transparent 28%),#08090e;color:#fff;text-decoration:none}}
      .adle-card-art{{height:86px;display:grid;place-content:center;text-align:center;border:1px solid color-mix(in srgb,var(--accent) 25%,transparent);border-radius:16px;background:radial-gradient(circle at 34% 30%,color-mix(in srgb,var(--accent) 42%,transparent),transparent 26%),#0b0c15}}.adle-card-art span{{font-size:30px}}.adle-card-art small{{margin-top:6px;color:#ddd7e6;font-size:9px;font-weight:900;letter-spacing:1px}}
      .adle-card-copy{{margin-top:14px}}.adle-card-copy h3{{margin:0;font-size:17px;line-height:1.1}}.adle-card-copy p{{margin:7px 0 0;color:#8d8a97;font-size:10px}}
      .adle-card footer{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:15px;color:#70dfff;font-size:10px;font-weight:900}}.adle-card footer b{{display:flex;width:31px;height:31px;align-items:center;justify-content:center;border:1px solid rgba(87,220,255,.23);border-radius:50%;color:#fff}}
      .adle-gear{{position:fixed;right:16px;top:96px;z-index:1000;display:flex;width:52px;height:52px;align-items:center;justify-content:center;border:1px solid color-mix(in srgb,var(--accent) 70%,transparent);border-radius:50%;background:#080a12;color:#fff;text-decoration:none;font-size:23px;box-shadow:0 0 24px color-mix(in srgb,var(--accent) 34%,transparent)}}
      .adle-nav{{position:sticky;bottom:8px;z-index:20;display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:22px;padding:8px;border:1px solid color-mix(in srgb,var(--accent) 25%,transparent);border-radius:21px;background:rgba(6,7,12,.96);backdrop-filter:blur(14px)}}.adle-nav a{{padding:8px 2px;color:#777485;text-align:center;text-decoration:none;font-size:9px}}.adle-nav b{{display:block;margin-bottom:3px;color:#aa72ff;font-size:18px}}.adle-nav .active{{color:#fff}}
      @media(max-width:520px){{.adle-titlebar{{grid-template-columns:1fr auto}}.adle-titlebar>p{{grid-column:1/-1;order:3}}}}
      @media(max-width:360px){{.adle-grid{{gap:8px}}.adle-card{{min-height:210px;padding:10px}}.adle-card-copy h3{{font-size:15px}}}}
    </style>
    <main class="adle">{''.join(blocks)}
      <a class="adle-gear" href="/tower/ad-market/editor" aria-label="จัดหน้า">⚙</a>
      <nav class="adle-nav"><a href="/tower"><b>⌂</b>HOME</a><a class="active" href="/tower/ad-market"><b>▶</b>EARN</a><a href="/tower/rewards"><b>★</b>REWARD</a><a href="/tower/cards"><b>▤</b>CARD</a></nav>
    </main>
    <script>
      function adleToggleSound(button){{const video=button.parentElement.querySelector('video');if(!video)return;video.muted=!video.muted;button.textContent=video.muted?'🔇':'🔊';if(video.paused)video.play().catch(()=>{{}});}}
      (()=>{{const input=document.getElementById('adleSearch');const cards=[...document.querySelectorAll('.adle-card')];const chips=[...document.querySelectorAll('.adle-chips button')];let filter='';function apply(){{const q=input?input.value.trim().toLowerCase():'';cards.forEach(card=>{{const text=(card.dataset.name+' '+card.dataset.key).toLowerCase();card.style.display=(!filter||card.dataset.key===filter)&&(!q||text.includes(q))?'':'none';}});}}if(input)input.addEventListener('input',apply);chips.forEach(chip=>chip.addEventListener('click',()=>{{filter=chip.dataset.filter||'';chips.forEach(x=>x.classList.toggle('active',x===chip));apply();}}));}})();
    </script>
    """
    return page_func("AD Market", content)


def _checked(value: bool) -> str:
    return " checked" if value else ""


def _selected(value: str, current: str) -> str:
    return " selected" if value == current else ""


def editor_html(saved: bool = False) -> str:
    cfg = load_config()
    rows = []
    for name in cfg["order"]:
        rows.append(f"""
        <li class="ed-block" data-block="{name}">
          <span class="ed-drag">☰</span><strong>{_esc(BLOCK_LABELS[name])}</strong>
          <label><input type="checkbox" name="enable_{name}" value="1"{_checked(cfg['enabled'].get(name, True))}> แสดง</label>
          <button type="button" class="up">↑</button><button type="button" class="down">↓</button>
        </li>
        """)

    notice = '<div class="saved">บันทึกแล้ว — เปิดหน้าจริงดูผลได้เลย</div>' if saved else ""
    return f"""<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AD Market Layout Editor</title>
    <style>
      *{{box-sizing:border-box}}body{{margin:0;background:#000;color:#fff;font-family:Arial,sans-serif}}.ed{{max-width:760px;margin:auto;padding:18px 16px 80px}}.top{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px}}.top h1{{margin:0;font-size:22px}}.top a{{padding:10px 13px;border:1px solid #6131a1;border-radius:12px;color:#fff;text-decoration:none;background:#090a10}}.panel{{margin-bottom:13px;padding:16px;border:1px solid #402063;border-radius:19px;background:#08090e}}.panel h2{{margin:0 0 12px;font-size:17px}}.muted{{color:#898693;font-size:11px;line-height:1.5}}label{{display:block;margin:11px 0 6px;color:#c4c0cc;font-size:12px}}input,textarea,select{{width:100%;padding:12px;border:1px solid #40235f;border-radius:12px;background:#030409;color:#fff}}textarea{{min-height:78px;resize:vertical}}input[type=color]{{height:46px;padding:5px}}input[type=range]{{padding:0}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.ed-blocks{{display:grid;gap:8px;padding:0;list-style:none}}.ed-block{{display:grid;grid-template-columns:auto minmax(0,1fr) auto auto auto;align-items:center;gap:8px;padding:11px;border:1px solid #30203f;border-radius:13px;background:#05060a}}.ed-block label{{margin:0;white-space:nowrap}}.ed-block input{{width:auto}}.ed-block button{{width:34px;height:34px;border:1px solid #542781;border-radius:10px;background:#0a0b12;color:#fff}}.ed-drag{{color:#aa69ff;font-size:20px}}.actions{{position:sticky;bottom:8px;display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:9px;border:1px solid #432267;border-radius:18px;background:rgba(5,6,10,.96)}}.actions button,.actions a{{display:flex;min-height:48px;align-items:center;justify-content:center;border:0;border-radius:13px;background:linear-gradient(135deg,#7c2bff,#b938f0);color:#fff;text-decoration:none;font-weight:900}}.actions .secondary{{border:1px solid #45236b;background:#090a10}}.saved{{margin-bottom:12px;padding:12px;border:1px solid #246a55;border-radius:13px;background:#06130f;color:#9af3cf}}.media-now{{margin-top:8px;color:#75dfff;font-size:10px;word-break:break-all}}@media(max-width:520px){{.two{{grid-template-columns:1fr}}.ed-block{{grid-template-columns:auto minmax(0,1fr) auto auto}}.ed-block label{{grid-column:2/3}}}}
    </style></head><body><main class="ed">
      <div class="top"><div><small class="muted">8046 CONTROL TOOL</small><h1>จัดหน้า AD Market</h1></div><a href="/tower/ad-market">ดูหน้าจริง</a></div>{notice}
      <form method="post" action="/tower/ad-market/editor/save" enctype="multipart/form-data" id="layoutForm">
        <section class="panel"><h2>1. เรียงลำดับและเปิด–ปิด</h2><p class="muted">ใช้ลูกศรย้ายบล็อก ไม่ต้องแก้โค้ด เมื่อบันทึกแล้วหน้าจริงเปลี่ยนทันที</p><ul class="ed-blocks" id="blockList">{''.join(rows)}</ul><input type="hidden" name="order" id="orderInput" value="{_esc(','.join(cfg['order']))}"></section>
        <section class="panel"><h2>2. รูปใหญ่และลิงก์ในภาพ</h2><label>เปลี่ยนรูปใหญ่</label><input type="file" name="hero_image" accept="image/*"><div class="media-now">รูปปัจจุบัน: {_esc(cfg.get('image') or 'ยังไม่มี')}</div><div class="two"><div><label>ความสูงรูปใหญ่</label><input type="range" name="hero_height" min="200" max="760" value="{cfg['hero_height']}" oninput="this.nextElementSibling.textContent=this.value+' px'"><small>{cfg['hero_height']} px</small></div><div><label>การแสดงรูป</label><select name="hero_fit"><option value="cover"{_selected('cover',cfg['hero_fit'])}>เต็มกรอบ (ตัดขอบ)</option><option value="contain"{_selected('contain',cfg['hero_fit'])}>เห็นครบทั้งรูป</option></select></div></div><div class="two"><div><label>ลิงก์ซ้าย / Earn</label><input name="earn_link" value="{_esc(cfg.get('earn_link'))}"></div><div><label>ลิงก์กลาง / Enter</label><input name="enter_link" value="{_esc(cfg.get('enter_link'))}"></div></div><label>ลิงก์ขวา / Reward</label><input name="reward_link" value="{_esc(cfg.get('reward_link'))}"><label><input type="checkbox" name="delete_image" value="1" style="width:auto"> ลบรูปใหญ่ปัจจุบัน</label></section>
        <section class="panel"><h2>3. แถบหัวข้อแนวนอน</h2><label>หัวข้อ</label><input name="title" value="{_esc(cfg.get('title'))}"><label>ข้อความไทย</label><textarea name="subtitle">{_esc(cfg.get('subtitle'))}</textarea><label>ความสูงแถบหัวข้อ</label><input type="range" name="title_height" min="72" max="180" value="{cfg['title_height']}" oninput="this.nextElementSibling.textContent=this.value+' px'"><small>{cfg['title_height']} px</small></section>
        <section class="panel"><h2>4. วิดีโอเล่าเรื่อง</h2><label>อัปโหลด MP4 / WEBM / MOV / M4V</label><input type="file" name="story_video" accept="video/mp4,video/webm,video/quicktime,.m4v"><div class="media-now">วิดีโอปัจจุบัน: {_esc(cfg.get('video') or 'ยังไม่มี')}</div><label>ข้อความใต้วิดีโอ</label><input name="video_title" value="{_esc(cfg.get('video_title'))}"><label>คำอธิบายสั้น</label><input name="video_subtitle" value="{_esc(cfg.get('video_subtitle'))}"><label>ลิงก์เมื่อแตะวิดีโอ (เว้นว่างได้)</label><input name="video_link" value="{_esc(cfg.get('video_link'))}"><div class="two"><div><label>ความสูงวิดีโอ</label><input type="range" name="video_height" min="130" max="460" value="{cfg['video_height']}" oninput="this.nextElementSibling.textContent=this.value+' px'"><small>{cfg['video_height']} px</small></div><div><label>การแสดงวิดีโอ</label><select name="video_fit"><option value="cover"{_selected('cover',cfg['video_fit'])}>เต็มกรอบ</option><option value="contain"{_selected('contain',cfg['video_fit'])}>เห็นครบ</option></select></div></div><label><input type="checkbox" name="delete_video" value="1" style="width:auto"> ลบวิดีโอปัจจุบัน</label></section>
        <section class="panel"><h2>5. ข้อความส่วนรายการ</h2><label>หัวข้อการ์ดหมวด</label><input name="category_title" value="{_esc(cfg.get('category_title'))}"><label>ข้อความด้านขวา</label><input name="category_note" value="{_esc(cfg.get('category_note'))}"><div class="two"><div><label>สีพื้นหลัง</label><input type="color" name="background" value="{cfg['background']}"></div><div><label>สีเน้น</label><input type="color" name="accent" value="{cfg['accent']}"></div></div></section>
        <div class="actions"><a class="secondary" href="/tower/ad-market">ยกเลิก</a><button type="submit">บันทึกและใช้งาน</button></div>
      </form>
      <form method="post" action="/tower/ad-market/editor/reset" onsubmit="return confirm('คืนค่าการจัดหน้าเริ่มต้นใช่ไหม')"><button style="width:100%;margin-top:12px;padding:12px;border:1px solid #5b2937;border-radius:13px;background:#12070a;color:#ff9bad">คืนค่าเริ่มต้น</button></form>
    </main><script>
      const list=document.getElementById('blockList'),order=document.getElementById('orderInput');function sync(){{order.value=[...list.children].map(x=>x.dataset.block).join(',')}}list.addEventListener('click',e=>{{const row=e.target.closest('.ed-block');if(!row)return;if(e.target.classList.contains('up')&&row.previousElementSibling)list.insertBefore(row,row.previousElementSibling);if(e.target.classList.contains('down')&&row.nextElementSibling)list.insertBefore(row.nextElementSibling,row);sync();}});document.getElementById('layoutForm').addEventListener('submit',sync);
    </script></body></html>"""


async def _save_upload(upload, allowed: set[str], max_bytes: int, prefix: str) -> str | None:
    if upload is None or not getattr(upload, "filename", ""):
        return None
    ext = Path(upload.filename).suffix.lower()
    if ext not in allowed:
        return None
    raw = await upload.read()
    if not raw or len(raw) > max_bytes:
        return None
    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(raw)
    return filename


def setup_ad_market_layout_editor(app) -> None:
    if getattr(app.state, "infini_ad_market_layout_editor", False):
        return
    app.state.infini_ad_market_layout_editor = True

    @app.get("/tower/ad-market-layout-media/{filename}")
    def ad_market_layout_media(filename: str):
        target = _file_path(filename)
        if not target:
            return Response(status_code=404)
        return FileResponse(target, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})

    @app.get("/tower/ad-market/editor", response_class=HTMLResponse)
    def ad_market_editor(saved: int = 0):
        return HTMLResponse(editor_html(bool(saved)))

    @app.post("/tower/ad-market/editor/save")
    async def ad_market_editor_save(request: Request):
        form = await request.form()
        cfg = load_config()

        order = [x for x in str(form.get("order") or "").split(",") if x in BLOCKS]
        order.extend(name for name in BLOCKS if name not in order)
        cfg["order"] = order
        cfg["enabled"] = {name: bool(form.get(f"enable_{name}")) for name in BLOCKS}

        for field in ["title", "subtitle", "video_title", "video_subtitle", "video_link", "category_title", "category_note", "enter_link", "earn_link", "reward_link"]:
            cfg[field] = str(form.get(field) or "").strip()

        cfg["hero_height"] = _clamp_int(form.get("hero_height"), 200, 760, 520)
        cfg["title_height"] = _clamp_int(form.get("title_height"), 72, 180, 102)
        cfg["video_height"] = _clamp_int(form.get("video_height"), 130, 460, 220)
        cfg["hero_fit"] = _safe_fit(form.get("hero_fit"))
        cfg["video_fit"] = _safe_fit(form.get("video_fit"))
        cfg["background"] = _safe_color(form.get("background"), "#000000")
        cfg["accent"] = _safe_color(form.get("accent"), "#a83cff")

        if form.get("delete_image"):
            cfg["image"] = ""
        if form.get("delete_video"):
            cfg["video"] = ""

        image_name = await _save_upload(form.get("hero_image"), {".jpg", ".jpeg", ".png", ".webp", ".gif"}, 25 * 1024 * 1024, "hero")
        if image_name:
            cfg["image"] = image_name

        video_name = await _save_upload(form.get("story_video"), {".mp4", ".webm", ".mov", ".m4v"}, 120 * 1024 * 1024, "story")
        if video_name:
            cfg["video"] = video_name

        save_config(cfg)
        return RedirectResponse("/tower/ad-market/editor?saved=1", status_code=303)

    @app.post("/tower/ad-market/editor/reset")
    def ad_market_editor_reset():
        current = load_config()
        fresh = _default_config()
        # Keep uploaded media and old hotspot links while resetting visual layout.
        for key in ["image", "video", "enter_link", "earn_link", "reward_link"]:
            fresh[key] = current.get(key, fresh.get(key, ""))
        save_config(fresh)
        return RedirectResponse("/tower/ad-market/editor?saved=1", status_code=303)
