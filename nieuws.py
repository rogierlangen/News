"""
Nieuwsaggregator
Haalt nieuwskoppen op van AD, FD en NOS via RSS feeds.
Scrapt ook de "meest gelezen" artikelen van de websites.
Slaat het resultaat op in NIEUWS.md en index.html

Gebruik:
    python3 nieuws.py          # Normale modus (haalt echte feeds op)
    python3 nieuws.py --demo   # Demo modus (toont voorbeelddata)
"""

import urllib.request
import xml.etree.ElementTree as ET
import sys
import html
import re
from datetime import datetime

# RSS feed URLs van de nieuwssites
FEEDS = {
    "NOS": "https://feeds.nos.nl/nosnieuwsalgemeen",
    "AD": "https://www.ad.nl/rss.xml",
    "FD": "https://fd.nl/laatste-nieuws?rss"
}

# URLs voor het scrapen van meest gelezen
MEEST_GELEZEN_URLS = {
    "NOS": "https://nos.nl",
    "AD": "https://www.ad.nl",
    "FD": "https://fd.nl"
}

# Kleuren per nieuwsbron (voor de styling)
BRON_KLEUREN = {
    "NOS": "#f26522",  # NOS oranje
    "AD": "#ee3124",   # AD rood
    "FD": "#c9a66b"    # FD goud/bruin
}

# Demo data voor laatste nieuws
DEMO_LAATSTE = {
    "NOS": [
        ("Kabinet presenteert nieuwe klimaatplannen",
         "https://nos.nl/artikel/1",
         "Het kabinet heeft vandaag nieuwe plannen gepresenteerd om de klimaatdoelen te halen."),
        ("Ajax wint met 3-0 van Feyenoord",
         "https://nos.nl/artikel/2",
         "In een spectaculaire Klassieker heeft Ajax gewonnen van Feyenoord."),
        ("Zware storm verwacht in het weekend",
         "https://nos.nl/artikel/3",
         "Het KNMI waarschuwt voor zware windstoten dit weekend."),
    ],
    "AD": [
        ("Huizenprijzen stijgen verder in grote steden",
         "https://ad.nl/artikel/1",
         "De gemiddelde huizenprijs in Amsterdam is gestegen."),
        ("Nieuwe attractie opent in de Efteling",
         "https://ad.nl/artikel/2",
         "De Efteling opent volgende maand een gloednieuwe achtbaan."),
        ("Supermarkten verlagen prijzen basisproducten",
         "https://ad.nl/artikel/3",
         "Albert Heijn en Jumbo verlagen prijzen na kritiek."),
    ],
    "FD": [
        ("AEX sluit hoger na positieve kwartaalcijfers",
         "https://fd.nl/artikel/1",
         "De Amsterdamse beurs sloot vandaag 1,2% hoger."),
        ("ING verhoogt hypotheekrente",
         "https://fd.nl/artikel/2",
         "ING verhoogt per 1 februari de hypotheekrente."),
        ("Tech-sector groeit ondanks onzekerheid",
         "https://fd.nl/artikel/3",
         "Nederlandse techbedrijven blijven groeien."),
    ],
}

# Demo data voor meest gelezen
DEMO_POPULAIR = {
    "NOS": [
        ("Waarom de benzineprijs zo hoog blijft",
         "https://nos.nl/artikel/10",
         "Analyse: dit zijn de factoren achter de hoge brandstofprijzen."),
        ("Live: Tweede Kamer debatteert over begroting",
         "https://nos.nl/artikel/11",
         "Volg hier het begrotingsdebat in de Tweede Kamer."),
        ("Dit is waarom je salaris niet stijgt",
         "https://nos.nl/artikel/12",
         "Economen leggen uit waarom lonen achterblijven bij inflatie."),
    ],
    "AD": [
        ("'Ik verdiende 3000 euro per maand bij OnlyFans'",
         "https://ad.nl/artikel/10",
         "Studente vertelt over haar bijverdienste op het platform."),
        ("Dit zijn de goedkoopste supermarkten van Nederland",
         "https://ad.nl/artikel/11",
         "Onderzoek toont aan welke supermarkt het voordeligst is."),
        ("Buurt in shock na vondst lichaam",
         "https://ad.nl/artikel/12",
         "Politie doet onderzoek naar verdacht overlijden."),
    ],
    "FD": [
        ("Column: Waarom de huizenmarkt niet zal crashen",
         "https://fd.nl/artikel/10",
         "Analyse van de Nederlandse woningmarkt."),
        ("De beste aandelen voor 2026",
         "https://fd.nl/artikel/11",
         "Beleggingsexperts delen hun favorieten."),
        ("Miljonair op je 30e: zo deed zij het",
         "https://fd.nl/artikel/12",
         "Interview met jonge ondernemer over haar succes."),
    ],
}


def strip_html_tags(text):
    """Verwijdert HTML tags uit tekst."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return html.unescape(clean).strip()


def verkort_tekst(text, max_lengte=150):
    """Verkort tekst tot maximale lengte, breekt af bij woordgrens."""
    if not text or len(text) <= max_lengte:
        return text
    verkort = text[:max_lengte].rsplit(' ', 1)[0]
    return verkort + "..."


def haal_pagina_op(url):
    """Haalt een webpagina op en retourneert de HTML."""
    try:
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
            }
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    Fout bij ophalen pagina: {e}")
        return None


def scrape_nos_meest_gelezen(html_content):
    """Scrapt de meest gelezen artikelen van NOS."""
    artikelen = []
    if not html_content:
        return artikelen

    # Zoek naar meest gelezen sectie - NOS gebruikt vaak "mostread" of "meestgelezen"
    # Probeer verschillende patronen
    patterns = [
        r'<a[^>]*href="(/artikel/[^"]+)"[^>]*>([^<]+)</a>',
        r'<a[^>]*href="(https://nos\.nl/artikel/[^"]+)"[^>]*>([^<]+)</a>',
        r'<h3[^>]*><a[^>]*href="(/l/[^"]+)"[^>]*>([^<]+)</a></h3>',
    ]

    # Zoek naar de meest gelezen sectie
    meest_gelezen_match = re.search(r'(?:meest.?gelezen|most.?read|populair)(.*?)(?:</section>|</aside>|</div>\s*</div>\s*</div>)', html_content, re.IGNORECASE | re.DOTALL)

    if meest_gelezen_match:
        sectie = meest_gelezen_match.group(1)
        links = re.findall(r'<a[^>]*href="(/(?:artikel|l)/[^"]+)"[^>]*>.*?</a>', sectie, re.DOTALL)
        titels = re.findall(r'>([^<]{10,100})</a>', sectie)

        for i, (link, titel) in enumerate(zip(links[:5], titels[:5])):
            full_link = f"https://nos.nl{link}" if link.startswith('/') else link
            artikelen.append((strip_html_tags(titel), full_link, ""))

    return artikelen[:5]


def scrape_ad_meest_gelezen(html_content):
    """Scrapt de meest gelezen artikelen van AD."""
    artikelen = []
    if not html_content:
        return artikelen

    # AD heeft vaak een "meest gelezen" widget
    meest_gelezen_match = re.search(r'(?:meest.?gelezen|most.?read|trending)(.*?)(?:</section>|</aside>|</ul>)', html_content, re.IGNORECASE | re.DOTALL)

    if meest_gelezen_match:
        sectie = meest_gelezen_match.group(1)
        # Zoek naar artikel links
        matches = re.findall(r'<a[^>]*href="(https://www\.ad\.nl/[^"]+)"[^>]*>([^<]+)</a>', sectie)

        for link, titel in matches[:5]:
            if len(titel) > 10:  # Filter korte teksten
                artikelen.append((strip_html_tags(titel), link, ""))

    return artikelen[:5]


def scrape_fd_meest_gelezen(html_content):
    """Scrapt de meest gelezen artikelen van FD."""
    artikelen = []
    if not html_content:
        return artikelen

    # FD heeft vaak een "meest gelezen" of "trending" sectie
    meest_gelezen_match = re.search(r'(?:meest.?gelezen|trending|populair)(.*?)(?:</section>|</aside>|</div>\s*</div>)', html_content, re.IGNORECASE | re.DOTALL)

    if meest_gelezen_match:
        sectie = meest_gelezen_match.group(1)
        matches = re.findall(r'<a[^>]*href="(https://fd\.nl/[^"]+)"[^>]*>([^<]+)</a>', sectie)

        for link, titel in matches[:5]:
            if len(titel) > 10:
                artikelen.append((strip_html_tags(titel), link, ""))

    return artikelen[:5]


def haal_meest_gelezen_op(naam, demo_modus=False):
    """Haalt de meest gelezen artikelen op door de website te scrapen."""
    if demo_modus:
        return DEMO_POPULAIR.get(naam, [])

    url = MEEST_GELEZEN_URLS.get(naam)
    if not url:
        return []

    print(f"    Scrapen meest gelezen van {naam}...")
    html_content = haal_pagina_op(url)

    if not html_content:
        return []

    if naam == "NOS":
        return scrape_nos_meest_gelezen(html_content)
    elif naam == "AD":
        return scrape_ad_meest_gelezen(html_content)
    elif naam == "FD":
        return scrape_fd_meest_gelezen(html_content)

    return []


def haal_nieuws_op(naam, url, demo_modus=False):
    """Haalt nieuwsartikelen op van een RSS feed en geeft ze terug als lijst."""
    artikelen = []

    if demo_modus:
        return DEMO_LAATSTE.get(naam, [])

    try:
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NieuwsBot/1.0)'}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()

        root = ET.fromstring(data)
        items = root.findall('.//item')

        for item in items[:5]:
            titel = item.find('title')
            link = item.find('link')
            beschrijving = item.find('description')

            if titel is not None and titel.text:
                artikel_titel = strip_html_tags(titel.text)
                artikel_link = link.text if link is not None else ""
                artikel_beschrijving = ""

                if beschrijving is not None and beschrijving.text:
                    artikel_beschrijving = verkort_tekst(strip_html_tags(beschrijving.text))

                artikelen.append((artikel_titel, artikel_link, artikel_beschrijving))

    except Exception as e:
        artikelen.append((f"Fout bij ophalen: {e}", "", ""))

    return artikelen


def maak_artikel_html(titel, link, beschrijving):
    """Maakt HTML voor een enkel artikel."""
    escaped_titel = html.escape(titel)
    escaped_beschrijving = html.escape(beschrijving) if beschrijving else ""

    if link:
        return f'''
        <article class="artikel">
            <a href="{html.escape(link)}" target="_blank" class="artikel-link">
                <h3>{escaped_titel}</h3>
                {f'<p class="beschrijving">{escaped_beschrijving}</p>' if escaped_beschrijving else ''}
            </a>
        </article>
        '''
    else:
        return f'''
        <article class="artikel">
            <h3>{escaped_titel}</h3>
            {f'<p class="beschrijving">{escaped_beschrijving}</p>' if escaped_beschrijving else ''}
        </article>
        '''


def maak_html(alle_laatste, alle_populair, demo_modus=False):
    """Maakt een HTML pagina met professionele nieuwssite styling."""

    nu = datetime.now().strftime("%d-%m-%Y om %H:%M")
    demo_tekst = '<span class="demo-badge">Demo</span>' if demo_modus else ''

    # Bouw de artikelen HTML per bron
    bronnen_html = ""
    for naam in FEEDS.keys():
        kleur = BRON_KLEUREN.get(naam, "#333")
        laatste = alle_laatste.get(naam, [])
        populair = alle_populair.get(naam, [])

        # Laatste nieuws artikelen
        laatste_html = ""
        if laatste:
            for titel, link, beschrijving in laatste:
                laatste_html += maak_artikel_html(titel, link, beschrijving)
        else:
            laatste_html = '<p class="geen">Geen artikelen gevonden</p>'

        # Populaire artikelen
        populair_html = ""
        if populair:
            for titel, link, beschrijving in populair:
                populair_html += maak_artikel_html(titel, link, beschrijving)
        else:
            populair_html = '<p class="geen">Niet beschikbaar</p>'

        bronnen_html += f'''
        <section class="bron">
            <div class="bron-header" style="border-left-color: {kleur}">
                <h2 style="color: {kleur}">{naam}</h2>
            </div>
            <div class="kolommen">
                <div class="kolom">
                    <h4 class="kolom-titel">Laatste nieuws</h4>
                    <div class="artikelen">
                        {laatste_html}
                    </div>
                </div>
                <div class="kolom populair">
                    <h4 class="kolom-titel">Meest gelezen</h4>
                    <div class="artikelen">
                        {populair_html}
                    </div>
                </div>
            </div>
        </section>
        '''

    html_output = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nieuwsoverzicht - NOS, AD, FD</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif;
            background: #f0f2f5;
            color: #1a1a1a;
            line-height: 1.5;
        }}

        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 25px 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}

        .header .update-tijd {{
            font-size: 0.85em;
            opacity: 0.8;
        }}

        .demo-badge {{
            background: #ffc107;
            color: #000;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin-left: 10px;
            vertical-align: middle;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 25px 15px;
        }}

        .bron {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }}

        .bron-header {{
            padding: 15px 20px;
            border-left: 4px solid;
            background: #fafafa;
        }}

        .bron-header h2 {{
            font-size: 1.2em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .kolommen {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }}

        .kolom {{
            padding: 0;
            border-right: 1px solid #f0f0f0;
        }}

        .kolom:last-child {{
            border-right: none;
        }}

        .kolom-titel {{
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
            padding: 12px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #f0f0f0;
        }}

        .kolom.populair .kolom-titel {{
            color: #e74c3c;
        }}

        .artikelen {{
            padding: 5px 0;
        }}

        .artikel {{
            border-bottom: 1px solid #f0f0f0;
        }}

        .artikel:last-child {{
            border-bottom: none;
        }}

        .artikel-link {{
            display: block;
            padding: 12px 20px;
            text-decoration: none;
            color: inherit;
            transition: background 0.15s ease;
        }}

        .artikel-link:hover {{
            background: #f8f9fa;
        }}

        .artikel h3 {{
            font-size: 0.9em;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 4px;
            line-height: 1.4;
        }}

        .artikel-link:hover h3 {{
            color: #0066cc;
        }}

        .beschrijving {{
            font-size: 0.8em;
            color: #666;
            line-height: 1.4;
        }}

        .geen {{
            padding: 15px 20px;
            color: #999;
            font-style: italic;
            font-size: 0.85em;
        }}

        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: #888;
            font-size: 0.8em;
        }}

        @media (max-width: 768px) {{
            .kolommen {{
                grid-template-columns: 1fr;
            }}

            .kolom {{
                border-right: none;
                border-bottom: 1px solid #f0f0f0;
            }}

            .kolom:last-child {{
                border-bottom: none;
            }}

            .header h1 {{
                font-size: 1.4em;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>Nieuwsoverzicht {demo_tekst}</h1>
        <p class="update-tijd">Laatst bijgewerkt: {nu}</p>
    </header>

    <main class="container">
        {bronnen_html}
    </main>

    <footer class="footer">
        Automatisch bijgewerkt elk uur
    </footer>
</body>
</html>'''

    return html_output


def maak_markdown(alle_laatste, alle_populair, demo_modus=False):
    """Maakt een markdown bestand met alle nieuwsartikelen."""

    nu = datetime.now().strftime("%d-%m-%Y om %H:%M")

    md = []
    md.append("# Nieuwsoverzicht")
    md.append("")
    md.append(f"*Laatst bijgewerkt: {nu}*")
    if demo_modus:
        md.append("*(Demo modus - voorbeelddata)*")
    md.append("")
    md.append("---")

    for naam in FEEDS.keys():
        md.append("")
        md.append(f"## {naam}")

        # Laatste nieuws
        md.append("")
        md.append("### Laatste nieuws")
        md.append("")
        laatste = alle_laatste.get(naam, [])
        if not laatste:
            md.append("*Geen artikelen gevonden*")
        else:
            for artikel in laatste:
                titel = artikel[0]
                link = artikel[1] if len(artikel) > 1 else ""
                beschrijving = artikel[2] if len(artikel) > 2 else ""
                if link:
                    md.append(f"- [{titel}]({link})")
                else:
                    md.append(f"- {titel}")
                if beschrijving:
                    md.append(f"  > {beschrijving}")

        # Meest gelezen
        md.append("")
        md.append("### Meest gelezen")
        md.append("")
        populair = alle_populair.get(naam, [])
        if not populair:
            md.append("*Niet beschikbaar*")
        else:
            for artikel in populair:
                titel = artikel[0]
                link = artikel[1] if len(artikel) > 1 else ""
                if link:
                    md.append(f"- [{titel}]({link})")
                else:
                    md.append(f"- {titel}")

    md.append("")
    md.append("---")
    md.append("*Automatisch gegenereerd door nieuws.py*")

    return "\n".join(md)


def main():
    demo_modus = "--demo" in sys.argv

    print("Nieuws ophalen...")

    # Haal laatste nieuws op via RSS
    alle_laatste = {}
    for naam, url in FEEDS.items():
        print(f"  - {naam} (RSS)...")
        alle_laatste[naam] = haal_nieuws_op(naam, url, demo_modus)

    # Haal meest gelezen op via scraping
    alle_populair = {}
    for naam in FEEDS.keys():
        print(f"  - {naam} (meest gelezen)...")
        alle_populair[naam] = haal_meest_gelezen_op(naam, demo_modus)

    # Genereer output
    markdown = maak_markdown(alle_laatste, alle_populair, demo_modus)
    with open("NIEUWS.md", "w", encoding="utf-8") as f:
        f.write(markdown)

    html_output = maak_html(alle_laatste, alle_populair, demo_modus)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"\nKlaar! Nieuws opgeslagen in NIEUWS.md en index.html")


if __name__ == "__main__":
    main()
