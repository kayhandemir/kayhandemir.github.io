"""Builds the UKGames static site (English at /, Turkish at /tr/) for GitHub Pages.

Run from the repository root:  python tools/build.py
Edit the texts in STRINGS / GAMES below, then rebuild and commit the generated HTML.
Legal texts live in tools/content/*.html (moved over unchanged from the previous site).
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "tools" / "content"
SITE = "https://ukgames.net"
EMAIL = "ugka81@gmail.com"
GA_ID = "G-E5WFC0MHFP"
YEAR = 2026

FONTS = ("https://fonts.googleapis.com/css2?family=Bungee&family=DM+Mono:wght@500"
         "&family=Rethink+Sans:wght@400;600;700;800&display=swap")

SOCIALS = [
    ("Instagram", "https://www.instagram.com/ugurkayhandemir",
     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>'),
    ("LinkedIn", "https://www.linkedin.com/in/u%C4%9Fur-kayhandemir",
     '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.6 8.65 21 11.2 21 14.5V21h-4v-5.8c0-1.4-.03-3.2-1.95-3.2-1.95 0-2.25 1.52-2.25 3.1V21H9z"/></svg>'),
    ("GitHub", "https://github.com/kayhandemir",
     '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.46-1.1-1.46-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.89 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/></svg>'),
]

PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4.2 2.4c-.3.3-.4.7-.4 1.2v16.8c0 .5.1.9.4 1.2l9.3-9.6zM14.7 13.2l2.6 2.7-11 6.3zm0-2.4L6.3 1.8l11 6.3zm3.9 4.4 2.9-1.7c.8-.5.8-1.6 0-2.1l-2.9-1.7-2.8 2.8z"/></svg>'

GAMES = [
    {
        "id": "zigzag-mix", "name": "ZigZag Mix", "css": "",
        "url": "https://play.google.com/store/apps/details?id=com.UGame.ZigZagMix",
        "icon": "/img/zigzag-icon.jpg", "shots": [f"/img/zigzag-{i}.jpg" for i in range(1, 5)],
        "en": {
            "tags": ["Arcade", "Endless runner", "3D"],
            "text": "Tap to switch direction and keep your runner on a zigzag path that keeps getting faster. "
                    "Eat fruit for energy and a higher score, then spend it on new characters.",
            "stats": [("15K+", "downloads"), ("Free", "to play"), ("Android", "Google Play")],
        },
        "tr": {
            "tags": ["Arcade", "Sonsuz koşu", "3D"],
            "text": "Ekrana dokunarak yön değiştir ve koşucunu gittikçe hızlanan zikzak yolda tut. "
                    "Enerji ve daha yüksek skor için meyveleri topla, sonra onlarla yeni karakterler aç.",
            "stats": [("15K+", "indirme"), ("Ücretsiz", "oyna"), ("Android", "Google Play")],
        },
    },
    {
        "id": "color-blocks", "name": "Color Blocks", "css": "console",
        "url": "https://play.google.com/store/apps/details?id=com.UKGames.ColorBlocks",
        "icon": "/img/colorblocks-icon.jpg", "shots": [f"/img/colorblocks-{i}.jpg" for i in range(1, 4)],
        "en": {
            "tags": ["Puzzle", "Retro", "Offline"],
            "text": "The classic brick game from the handheld consoles of your childhood. Move and rotate the falling "
                    "blocks, clear full lines and push your score higher, offline and anywhere.",
            "stats": [("100+", "downloads"), ("Free", "to play"), ("Offline", "no internet needed")],
        },
        "tr": {
            "tags": ["Bulmaca", "Retro", "Çevrimdışı"],
            "text": "Çocukluğunun el konsollarındaki klasik tuğla oyunu. Düşen blokları çevir ve yerleştir, dolu "
                    "satırları temizle ve skorunu yükselt. İnternet olmadan, her yerde.",
            "stats": [("100+", "indirme"), ("Ücretsiz", "oyna"), ("Çevrimdışı", "internet gerekmez")],
        },
    },
]

STRINGS = {
    "en": {
        "lang": "en", "prefix": "", "other": "tr", "other_label": "TR", "other_name": "Türkçe",
        "title": "UKGames | Indie games made with Unity",
        "description": "UKGames is an indie studio in Bursa, Turkey. Play ZigZag Mix and Color Blocks on Google Play, "
                       "and follow SmashJeeps, an online vehicle combat game in development.",
        "nav": ["Games", "SmashJeeps", "About", "Contact"],
        "eyebrow": "Indie studio · Bursa, Turkey",
        "h1": 'Small studio.<br><span class="hl">Loud games.</span>',
        "lede": "UKGames is Uğur Kayhandemir's one-person studio. I build arcade and puzzle games with Unity and C#, "
                "tuned to run smoothly on everyday phones.",
        "cta_games": "See the games", "cta_smash": "What's SmashJeeps?",
        "facts": [("2", "games on Google Play"), ("15K+", "ZigZag Mix downloads"), ("Unity", "C# · URP")],
        "poster_tag": "In development", "poster_title": "SmashJeeps",
        "poster_alt": "SmashJeeps artwork: jeeps racing through rockets and explosions",
        "games_h": "Games", "games_p": "Free to play on Google Play.",
        "shots_alt": "{name} screenshot {n}",
        "play_small": "Get it on", "play_big": "Google Play",
        "smash_label": "In development",
        "smash_intro": "An online vehicle combat arena for 2 to 4 players. Pick a jeep, grab weapons from mystery boxes "
                       "and smash your friends before the timer runs out.",
        "smash_features": [
            ("R", "Rockets, mines, spikes, shields and fake boxes", "Every weapon has its own tricks, and fake boxes explode on whoever grabs them."),
            ("+", "Health packs fall from the sky", "A new pack drops every 40 seconds. Everyone hears it coming."),
            ("⇄", "Play with friends online", "Host a match, share the join code, and set the match length from 30 seconds to 10 minutes."),
            ("✓", "Your profile follows you", "Start as a guest, link an account later. Stats, coins and settings are saved."),
        ],
        "economy_h": "Coin economy",
        "economy_rows": [("Starting coins", "100", ""), ("Every minute you play", "+10", "plus"),
                         ("Smash another jeep", "+50", "plus"), ("Respawn", "−5", "minus"),
                         ("Shield · Mine · Rocket", "30 · 40 · 70", "")],
        "economy_note": "Values from the current test build. They may change before release.",
        "jeep_alt": "Red SmashJeeps jeep",
        "about_h": "About",
        "about_p": [
            "Hi, I'm <strong>Uğur Kayhandemir</strong>. I make games with the <strong>Unity</strong> engine, and I care about clean C# code, optimized graphics and controls that feel right.",
            "UKGames started with small mobile games on Google Play. Now I'm building my first online multiplayer game, SmashJeeps.",
        ],
        "about_facts": [("Based in", "Bursa", "Yıldırım, Türkiye"), ("Engine", "Unity", "C#, URP, Netcode"),
                        ("Published", "2 games", "Google Play"), ("Next up", "SmashJeeps", "Online multiplayer")],
        "contact_h": "Say hello",
        "contact_p": "Questions about a game, a bug report, a collaboration idea or anything else: send me an email and I'll get back to you.",
        "copy": "Copy", "copied": "Copied",
        "privacy": "Privacy Policy", "terms": "Terms of Use",
        "rights": f"© {YEAR} UKGames",
        "notfound_h": "Page not found", "notfound_p": "This page doesn't exist or has moved.", "home": "Back to home",
        "redirect": "This page has moved.", "redirect_link": "Continue",
        "legal_alt": ("Türkçe", "tr"),
    },
    "tr": {
        "lang": "tr", "prefix": "/tr", "other": "en", "other_label": "EN", "other_name": "English",
        "title": "UKGames | Unity ile geliştirilen bağımsız oyunlar",
        "description": "UKGames, Bursa'da bağımsız bir oyun stüdyosu. ZigZag Mix ve Color Blocks'u Google Play'de oyna, "
                       "geliştirme aşamasındaki online araç savaşı oyunu SmashJeeps'i takip et.",
        "nav": ["Oyunlar", "SmashJeeps", "Hakkımda", "İletişim"],
        "eyebrow": "Bağımsız stüdyo · Bursa",
        "h1": 'Küçük stüdyo.<br><span class="hl">Gürültülü oyunlar.</span>',
        "lede": "UKGames, Uğur Kayhandemir'in tek kişilik stüdyosu. Unity ve C# ile, her telefonda akıcı çalışan "
                "arcade ve bulmaca oyunları geliştiriyorum.",
        "cta_games": "Oyunlara bak", "cta_smash": "SmashJeeps nedir?",
        "facts": [("2", "oyun Google Play'de"), ("15K+", "ZigZag Mix indirmesi"), ("Unity", "C# · URP")],
        "poster_tag": "Geliştiriliyor", "poster_title": "SmashJeeps",
        "poster_alt": "SmashJeeps görseli: roketler ve patlamalar arasında yarışan cipler",
        "games_h": "Oyunlar", "games_p": "Google Play'de ücretsiz.",
        "shots_alt": "{name} ekran görüntüsü {n}",
        "play_small": "Hemen indir", "play_big": "Google Play",
        "smash_label": "Geliştiriliyor",
        "smash_intro": "2 ila 4 oyunculu online araç savaşı arenası. Cipini seç, gizemli kutulardan silah topla ve "
                       "süre bitmeden arkadaşlarını ez.",
        "smash_features": [
            ("R", "Roket, mayın, diken, kalkan ve sahte kutu", "Her silahın kendi numarası var. Sahte kutu onu alanın yüzünde patlar."),
            ("+", "Gökten can paketi düşer", "Her 40 saniyede bir yeni paket iner. Geldiğini herkes duyar."),
            ("⇄", "Arkadaşlarınla online oyna", "Maçı kur, katılım kodunu paylaş, maç süresini 30 saniye ile 10 dakika arasında seç."),
            ("✓", "Profilin seninle gelir", "Misafir olarak başla, hesabını sonra bağla. İstatistik, coin ve ayarların kaydedilir."),
        ],
        "economy_h": "Coin ekonomisi",
        "economy_rows": [("Başlangıç coini", "100", ""), ("Oynadığın her dakika", "+10", "plus"),
                         ("Başka bir cipi ez", "+50", "plus"), ("Yeniden doğma", "−5", "minus"),
                         ("Kalkan · Mayın · Roket", "30 · 40 · 70", "")],
        "economy_note": "Değerler şu anki test sürümünden. Çıkıştan önce değişebilir.",
        "jeep_alt": "Kırmızı SmashJeeps cipi",
        "about_h": "Hakkımda",
        "about_p": [
            "Merhaba, ben <strong>Uğur Kayhandemir</strong>. <strong>Unity</strong> motoruyla oyun geliştiriyorum. Temiz C# kodu, optimize grafikler ve eline iyi oturan kontroller benim için öncelik.",
            "UKGames, Google Play'deki küçük mobil oyunlarla başladı. Şimdi ilk online çok oyunculu oyunum SmashJeeps'i geliştiriyorum.",
        ],
        "about_facts": [("Konum", "Bursa", "Yıldırım, Türkiye"), ("Motor", "Unity", "C#, URP, Netcode"),
                        ("Yayında", "2 oyun", "Google Play"), ("Sırada", "SmashJeeps", "Online çok oyunculu")],
        "contact_h": "Merhaba de",
        "contact_p": "Bir oyun hakkında soru, hata bildirimi, iş birliği fikri ya da başka bir şey: e-posta gönder, sana dönerim.",
        "copy": "Kopyala", "copied": "Kopyalandı",
        "privacy": "Gizlilik Politikası", "terms": "Kullanım Şartları",
        "rights": f"© {YEAR} UKGames",
        "notfound_h": "Sayfa bulunamadı", "notfound_p": "Bu sayfa yok ya da taşındı.", "home": "Ana sayfaya dön",
        "redirect": "Bu sayfa taşındı.", "redirect_link": "Devam et",
        "legal_alt": ("English", "en"),
    },
}

LEGAL = {
    # slug: (lang, title, content file, alternate slug)
    "privacy-policy": ("en", "Privacy Policy", "privacy-policy.html", "privacy-policy-tr"),
    "privacy-policy-tr": ("tr", "Gizlilik Politikası", "privacy-policy-tr.html", "privacy-policy"),
    "terms": ("en", "Terms of Use", "terms.html", "terms-tr"),
    "terms-tr": ("tr", "Kullanım Şartları", "terms-tr.html", "terms"),
}


def e(text):
    return html.escape(text, quote=True)


def head(s, title, description, path, alternates=None, noindex=False):
    canonical = SITE + path
    alt = ""
    if alternates:
        alt = "".join(f'\n<link rel="alternate" hreflang="{lang}" href="{SITE}{href}">' for lang, href in alternates)
    robots = '\n<meta name="robots" content="noindex">' if noindex else ""
    return f"""<!doctype html>
<html lang="{s['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">{alt}{robots}
<meta name="theme-color" content="#14213d">
<meta property="og:type" content="website">
<meta property="og:site_name" content="UKGames">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/img/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/img/icon-512.png" type="image/png">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/site.css">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
"""


def header(s, other_href):
    p = s["prefix"]
    home = p + "/"
    links = "".join(
        f'<a class="nav-section" href="{home}#{anchor}">{e(label)}</a>'
        for anchor, label in zip(["games", "smashjeeps", "about", "contact"], s["nav"]))
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="{home}" aria-label="UKGames home">UK<b>GAMES</b></a>
    <nav class="nav" aria-label="Main">
      {links}
      <a class="lang" href="{other_href}" hreflang="{s['other']}" lang="{s['other']}" title="{e(s['other_name'])}">{s['other_label']}</a>
    </nav>
  </div>
</header>
"""


def footer(s):
    p = s["prefix"]
    privacy = "/page/privacy-policy" + ("-tr" if s["lang"] == "tr" else "")
    terms = "/page/terms" + ("-tr" if s["lang"] == "tr" else "")
    return f"""<footer class="site-footer">
  <div class="wrap">
    <a class="wordmark" href="{p}/">UK<b>GAMES</b></a>
    <nav aria-label="Footer">
      <a href="{p}/#games">{e(s['nav'][0])}</a>
      <a href="{privacy}">{e(s['privacy'])}</a>
      <a href="{terms}">{e(s['terms'])}</a>
      <a href="{p}/#contact">{e(s['nav'][3])}</a>
    </nav>
    <span>{e(s['rights'])}</span>
  </div>
</footer>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""


def play_button(s, url, name):
    return (f'<a class="btn btn-play" href="{url}" rel="noopener" target="_blank" '
            f'aria-label="{e(name)}: {e(s["play_small"])} {e(s["play_big"])}">{PLAY_ICON}'
            f'<span><small>{e(s["play_small"])}</small>{e(s["play_big"])}</span></a>')


def game_card(s, g):
    t = g[s["lang"]]
    tags = "".join(f'<span class="tag">{e(x)}</span>' for x in t["tags"])
    stats = "".join(f"<li><b>{e(v)}</b><span>{e(k)}</span></li>" for v, k in t["stats"])
    shots = "".join(
        f'<img src="{src}" alt="{e(s["shots_alt"].format(name=g["name"], n=i))}" width="360" height="800" loading="lazy">'
        for i, src in enumerate(g["shots"], 1))
    return f"""<article class="game {g['css']}" id="{g['id']}">
  <div class="game-body">
    <div class="game-title">
      <img src="{g['icon']}" alt="" width="76" height="76" loading="lazy">
      <div><h3>{e(g['name'])}</h3><div class="tags">{tags}</div></div>
    </div>
    <p>{e(t['text'])}</p>
    <ul class="stats">{stats}</ul>
    <div>{play_button(s, g['url'], g['name'])}</div>
  </div>
  <div class="shots" tabindex="0" aria-label="{e(g['name'])}">{shots}</div>
</article>"""


def structured_data(s):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": SITE + "/#org", "name": "UKGames", "url": SITE + "/",
             "logo": SITE + "/img/icon-512.png", "email": EMAIL,
             "founder": {"@type": "Person", "name": "Uğur Kayhandemir"},
             "address": {"@type": "PostalAddress", "addressLocality": "Bursa", "addressCountry": "TR"},
             "sameAs": [url for _, url, _ in SOCIALS]},
        ] + [
            {"@type": "MobileApplication", "name": g["name"], "operatingSystem": "Android",
             "applicationCategory": "GameApplication", "url": g["url"],
             "image": SITE + g["icon"], "publisher": {"@id": SITE + "/#org"},
             "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}
            for g in GAMES
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n'


def home_page(s):
    p = s["prefix"]
    other = "/" if s["lang"] == "tr" else "/tr/"
    facts = "".join(f"<span><strong>{e(v)}</strong> {e(k)}</span>" for v, k in s["facts"])
    features = "".join(
        f'<li><span class="ic" aria-hidden="true">{e(ic)}</span><div><b>{e(t)}</b><span>{e(d)}</span></div></li>'
        for ic, t, d in s["smash_features"])
    rows = "".join(f'<tr><td>{e(k)}</td><td class="{c}">{e(v)}</td></tr>' for k, v, c in s["economy_rows"])
    about_p = "".join(f"<p>{x}</p>" for x in s["about_p"])
    about_facts = "".join(
        f'<div class="fact"><dt>{e(k)}</dt><dd>{e(v)}<small>{e(sub)}</small></dd></div>'
        for k, v, sub in s["about_facts"])
    socials = "".join(f'<a href="{url}" rel="noopener" target="_blank">{icon}{e(name)}</a>' for name, url, icon in SOCIALS)
    games = "\n".join(game_card(s, g) for g in GAMES)
    out = head(s, s["title"], s["description"], p + "/", [("en", "/"), ("tr", "/tr/"), ("x-default", "/")])
    out += structured_data(s) + "</head>\n<body>\n" + header(s, other)
    out += f"""<main>
<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">{e(s['eyebrow'])}</span>
      <h1>{s['h1']}</h1>
      <p class="lede">{e(s['lede'])}</p>
      <div class="actions">
        <a class="btn btn-blast" href="#games">{e(s['cta_games'])}</a>
        <a class="btn" href="#smashjeeps">{e(s['cta_smash'])}</a>
      </div>
      <div class="hero-facts">{facts}</div>
    </div>
    <figure class="poster">
      <img src="/img/smashjeeps-art-820.jpg" srcset="/img/smashjeeps-art-820.jpg 820w, /img/smashjeeps-art.jpg 1456w"
           sizes="(max-width: 860px) 92vw, 540px" width="1456" height="816" alt="{e(s['poster_alt'])}" fetchpriority="high">
      <figcaption><span>{e(s['poster_tag'])}</span>{e(s['poster_title'])}</figcaption>
    </figure>
  </div>
</section>

<section class="section games" id="games">
  <div class="wrap">
    <div class="section-head"><h2>{e(s['games_h'])}</h2><p>{e(s['games_p'])}</p></div>
    <div class="game-list">
{games}
    </div>
  </div>
</section>

<section class="section smash" id="smashjeeps">
  <div class="wrap">
    <div>
      <span class="label">{e(s['smash_label'])}</span>
      <h2>SmashJeeps</h2>
      <p class="intro">{e(s['smash_intro'])}</p>
      <ul class="features">{features}</ul>
    </div>
    <aside class="economy">
      <img src="/img/smashjeeps-jeep.png" alt="{e(s['jeep_alt'])}" width="420" height="295" loading="lazy">
      <h3>{e(s['economy_h'])}</h3>
      <table class="coin-table"><tbody>{rows}</tbody></table>
      <p class="note">{e(s['economy_note'])}</p>
    </aside>
  </div>
</section>

<section class="section about" id="about">
  <div class="wrap">
    <div>
      <h2>{e(s['about_h'])}</h2>
      <div class="prose">{about_p}</div>
    </div>
    <dl class="facts">{about_facts}</dl>
  </div>
</section>

<section class="section contact" id="contact">
  <div class="wrap">
    <div>
      <h2>{e(s['contact_h'])}</h2>
      <p>{e(s['contact_p'])}</p>
    </div>
    <div>
      <div class="mail">
        <a href="mailto:{EMAIL}">{EMAIL}</a>
        <button class="btn" type="button" id="copy-email" data-email="{EMAIL}" data-done="{e(s['copied'])}">{e(s['copy'])}</button>
      </div>
      <div class="socials">{socials}</div>
    </div>
  </div>
</section>
</main>
"""
    return out + footer(s)


def legal_page(slug):
    lang, title, file, alt_slug = LEGAL[slug]
    s = STRINGS[lang]
    body = (CONTENT / file).read_text(encoding="utf-8")
    body = body.replace("<strong>Profil Bilgileri:</strong> Username", "<strong>Profile Information:</strong> Username")
    if lang == "tr":
        body = body.replace('href="/#contact"', 'href="/tr/#contact"')
    body = body.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    alt_name, alt_lang = s["legal_alt"]
    path = f"/page/{slug}"
    out = head(s, f"{title} | UKGames", f"{title} for games and apps published by UKGames.", path,
               [(lang, path), (alt_lang, f"/page/{alt_slug}")])
    out += "</head>\n<body>\n" + header(s, f"/page/{alt_slug}")
    out += f"""<main class="legal-page">
  <div class="wrap">
    <article class="legal">
      <h1>{e(title)}</h1>
      <p class="alt"><a href="/page/{alt_slug}" hreflang="{alt_lang}">{e(alt_name)}</a></p>
{body}
    </article>
  </div>
</main>
"""
    return out + footer(s)


def redirect_page(target, lang="en"):
    s = STRINGS[lang]
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UKGames</title>
<link rel="canonical" href="{SITE}{target}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}" + location.hash);</script>
</head>
<body><p>{e(s['redirect'])} <a href="{target}">{e(s['redirect_link'])}</a></p></body>
</html>
"""


def language_switch_page():
    # Old site links: /set-language?lang=tr&redirect=/
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<title>UKGames</title>
<script>var l=new URLSearchParams(location.search).get("lang");location.replace(l==="tr"?"/tr/":"/");</script>
<meta http-equiv="refresh" content="1; url=/">
</head>
<body><p><a href="/">UKGames</a></p></body>
</html>
"""


def not_found_page():
    s = STRINGS["en"]
    out = head(s, "Page not found | UKGames", "This page doesn't exist.", "/404", noindex=True)
    out += "</head>\n<body>\n" + header(s, "/tr/")
    out += f"""<main class="center-page">
  <div class="wrap">
    <h1>404</h1>
    <p>{e(s['notfound_p'])}<br>{e(STRINGS['tr']['notfound_p'])}</p>
    <a class="btn btn-blast" href="/">{e(s['home'])}</a>
  </div>
</main>
"""
    return out + footer(s)


def sitemap():
    urls = ["/", "/tr/"] + [f"/page/{slug}" for slug in LEGAL]
    items = "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    write("index.html", home_page(STRINGS["en"]))
    write("tr/index.html", home_page(STRINGS["tr"]))
    for slug in LEGAL:
        write(f"page/{slug}.html", legal_page(slug))
    # Old URLs keep working: previous ukgames.net routes and the first GitHub Pages site.
    write("page/terms-of-service.html", redirect_page("/page/terms"))
    for slug in LEGAL:
        write(f"tr/page/{slug}.html", redirect_page(f"/page/{slug}", LEGAL[slug][0]))
    # The first site's policy URLs may still be registered in Google Play / AdMob, so they serve the full text.
    write("privacy-policy.html", legal_page("privacy-policy-tr"))
    write("terms.html", legal_page("terms-tr"))
    write("contact.html", redirect_page("/tr/#contact", "tr"))
    write("en/index.html", redirect_page("/"))
    write("set-language.html", language_switch_page())
    write("404.html", not_found_page())
    write("sitemap.xml", sitemap())
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print("Built", ROOT)


if __name__ == "__main__":
    main()
