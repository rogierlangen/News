"""
Nieuwsaggregator
Haalt nieuwskoppen op van AD, FD en NOS via RSS feeds.
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

# Kleuren per nieuwsbron (voor de styling)
BRON_KLEUREN = {
    "NOS": "#f26522",  # NOS oranje
    "AD": "#ee3124",   # AD rood
    "FD": "#c9a66b"    # FD goud/bruin
}

# Demo data met beschrijvingen
DEMO_DATA = {
    "NOS": [
        ("Kabinet presenteert nieuwe klimaatplannen",
         "https://nos.nl/artikel/1",
         "Het kabinet heeft vandaag nieuwe plannen gepresenteerd om de klimaatdoelen te halen. Minister Van der Wal sprak van een historisch moment."),
        ("Ajax wint met 3-0 van Feyenoord",
         "https://nos.nl/artikel/2",
         "In een spectaculaire Klassieker heeft Ajax met 3-0 gewonnen van Feyenoord. Brobbey scoorde twee keer."),
        ("Zware storm verwacht in het weekend",
         "https://nos.nl/artikel/3",
         "Het KNMI waarschuwt voor zware windstoten dit weekend. Code oranje is afgekondigd voor de kustprovincies."),
    ],
    "AD": [
        ("Huizenprijzen stijgen verder in grote steden",
         "https://ad.nl/artikel/1",
         "De gemiddelde huizenprijs in Amsterdam is voor het eerst boven de 600.000 euro gestegen. Starters hebben het steeds moeilijker."),
        ("Nieuwe attractie opent in de Efteling",
         "https://ad.nl/artikel/2",
         "De Efteling opent volgende maand een gloednieuwe achtbaan. Het wordt de snelste attractie van het park."),
        ("Supermarkten verlagen prijzen basisproducten",
         "https://ad.nl/artikel/3",
         "Albert Heijn en Jumbo hebben aangekondigd de prijzen van basisproducten te verlagen na aanhoudende kritiek."),
    ],
    "FD": [
        ("AEX sluit hoger na positieve kwartaalcijfers",
         "https://fd.nl/artikel/1",
         "De Amsterdamse beurs sloot vandaag 1,2% hoger. Met name techfondsen presteerden goed na meevallende cijfers uit de VS."),
        ("ING verhoogt hypotheekrente",
         "https://fd.nl/artikel/2",
         "ING verhoogt per 1 februari de hypotheekrente met 0,15 procentpunt. Andere banken overwegen te volgen."),
        ("Tech-sector groeit ondanks onzekerheid",
         "https://fd.nl/artikel/3",
         "Nederlandse techbedrijven blijven groeien ondanks economische onzekerheid. ASML rapporteerde recordomzet."),
    ],
}


def strip_html_tags(text):
    """Verwijdert HTML tags uit tekst."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return html.unescape(clean).strip()


def verkort_tekst(text, max_lengte=200):
    """Verkort tekst tot maximale lengte, breekt af bij woordgrens."""
    if not text or len(text) <= max_lengte:
        return text
    verkort = text[:max_lengte].rsplit(' ', 1)[0]
    return verkort + "..."


def haal_nieuws_op(naam, url, demo_modus=False):
    """Haalt nieuwsartikelen op van een RSS feed en geeft ze terug als lijst."""
    artikelen = []

    # Demo modus: gebruik voorbeelddata
    if demo_modus:
        return DEMO_DATA.get(naam, [])

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


def maak_html(alle_artikelen, demo_modus=False):
    """Maakt een HTML pagina met professionele nieuwssite styling."""

    nu = datetime.now().strftime("%d-%m-%Y om %H:%M")

    # Bouw de artikelen HTML
    artikelen_html = ""
    for naam, artikelen in alle_artikelen.items():
        kleur = BRON_KLEUREN.get(naam, "#333")

        artikelen_html += f'''
        <section class="bron">
            <div class="bron-header" style="border-left-color: {kleur}">
                <h2 style="color: {kleur}">{naam}</h2>
            </div>
            <div class="artikelen">
        '''

        if not artikelen:
            artikelen_html += '<p class="geen">Geen artikelen gevonden</p>'
        else:
            for titel, link, beschrijving in artikelen:
                escaped_titel = html.escape(titel)
                escaped_beschrijving = html.escape(beschrijving) if beschrijving else ""

                if link:
                    artikelen_html += f'''
                    <article class="artikel">
                        <a href="{html.escape(link)}" target="_blank" class="artikel-link">
                            <h3>{escaped_titel}</h3>
                            {f'<p class="beschrijving">{escaped_beschrijving}</p>' if escaped_beschrijving else ''}
                        </a>
                    </article>
                    '''
                else:
                    artikelen_html += f'''
                    <article class="artikel">
                        <h3>{escaped_titel}</h3>
                        {f'<p class="beschrijving">{escaped_beschrijving}</p>' if escaped_beschrijving else ''}
                    </article>
                    '''

        artikelen_html += '</div></section>'

    demo_tekst = '<span class="demo-badge">Demo</span>' if demo_modus else ''

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
            max-width: 1000px;
            margin: 0 auto;
            padding: 25px 15px;
        }}

        .bronnen-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .bron {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }}

        .bron:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.08);
        }}

        .bron-header {{
            padding: 15px 20px;
            border-left: 4px solid;
            background: #fafafa;
        }}

        .bron-header h2 {{
            font-size: 1.1em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
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
            padding: 15px 20px;
            text-decoration: none;
            color: inherit;
            transition: background 0.15s ease;
        }}

        .artikel-link:hover {{
            background: #f8f9fa;
        }}

        .artikel h3 {{
            font-size: 0.95em;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 6px;
            line-height: 1.4;
        }}

        .artikel-link:hover h3 {{
            color: #0066cc;
        }}

        .beschrijving {{
            font-size: 0.85em;
            color: #666;
            line-height: 1.5;
        }}

        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: #888;
            font-size: 0.8em;
        }}

        .footer a {{
            color: #666;
        }}

        @media (max-width: 640px) {{
            .bronnen-grid {{
                grid-template-columns: 1fr;
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
        <div class="bronnen-grid">
            {artikelen_html}
        </div>
    </main>

    <footer class="footer">
        Automatisch bijgewerkt elk uur
    </footer>
</body>
</html>'''

    return html_output


def maak_markdown(alle_artikelen, demo_modus=False):
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

    for naam, artikelen in alle_artikelen.items():
        md.append("")
        md.append(f"## {naam}")
        md.append("")

        if not artikelen:
            md.append("*Geen artikelen gevonden*")
            continue

        for artikel in artikelen:
            titel = artikel[0]
            link = artikel[1] if len(artikel) > 1 else ""
            beschrijving = artikel[2] if len(artikel) > 2 else ""

            if link:
                md.append(f"### [{titel}]({link})")
            else:
                md.append(f"### {titel}")

            if beschrijving:
                md.append(f"> {beschrijving}")
            md.append("")

    md.append("---")
    md.append("*Automatisch gegenereerd door nieuws.py*")

    return "\n".join(md)


def main():
    demo_modus = "--demo" in sys.argv

    print("Nieuws ophalen...")

    alle_artikelen = {}
    for naam, url in FEEDS.items():
        print(f"  - {naam}...")
        alle_artikelen[naam] = haal_nieuws_op(naam, url, demo_modus)

    markdown = maak_markdown(alle_artikelen, demo_modus)
    with open("NIEUWS.md", "w", encoding="utf-8") as f:
        f.write(markdown)

    html_output = maak_html(alle_artikelen, demo_modus)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"\nKlaar! Nieuws opgeslagen in NIEUWS.md en index.html")

    print("\n" + "="*50)
    print(markdown)


if __name__ == "__main__":
    main()
