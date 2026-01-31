"""
Nieuwsaggregator
Haalt nieuwskoppen op van AD, FD en NOS via RSS feeds.
Slaat het resultaat op in NIEUWS.md

Gebruik:
    python3 nieuws.py          # Normale modus (haalt echte feeds op)
    python3 nieuws.py --demo   # Demo modus (toont voorbeelddata)
"""

import urllib.request
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

# RSS feed URLs van de nieuwssites
FEEDS = {
    "NOS": "https://feeds.nos.nl/nosnieuwsalgemeen",
    "AD": "https://www.ad.nl/rss.xml",
    "FD": "https://fd.nl/laatste-nieuws?rss"
}

# Demo data om te laten zien hoe het werkt
DEMO_DATA = {
    "NOS": [
        ("Kabinet presenteert nieuwe klimaatplannen", "https://nos.nl/artikel/1"),
        ("Ajax wint met 3-0 van Feyenoord", "https://nos.nl/artikel/2"),
        ("Zware storm verwacht in het weekend", "https://nos.nl/artikel/3"),
        ("NS kondigt nieuwe dienstregeling aan", "https://nos.nl/artikel/4"),
        ("Koningspaar bezoekt Limburg", "https://nos.nl/artikel/5"),
    ],
    "AD": [
        ("Huizenprijzen stijgen verder in grote steden", "https://ad.nl/artikel/1"),
        ("Nieuwe attractie opent in de Efteling", "https://ad.nl/artikel/2"),
        ("Supermarkten verlagen prijzen basisproducten", "https://ad.nl/artikel/3"),
        ("Files verwacht door werkzaamheden A2", "https://ad.nl/artikel/4"),
        ("Restaurant in Rotterdam krijgt Michelinster", "https://ad.nl/artikel/5"),
    ],
    "FD": [
        ("AEX sluit hoger na positieve kwartaalcijfers", "https://fd.nl/artikel/1"),
        ("ING verhoogt hypotheekrente", "https://fd.nl/artikel/2"),
        ("Tech-sector groeit ondanks onzekerheid", "https://fd.nl/artikel/3"),
        ("Shell investeert in duurzame energie", "https://fd.nl/artikel/4"),
        ("Pensioenfondsen zien vermogen groeien", "https://fd.nl/artikel/5"),
    ],
}


def haal_nieuws_op(naam, url, demo_modus=False):
    """Haalt nieuwsartikelen op van een RSS feed en geeft ze terug als lijst."""
    artikelen = []

    # Demo modus: gebruik voorbeelddata
    if demo_modus:
        return DEMO_DATA.get(naam, [])

    try:
        # Maak een request met een User-Agent (sommige sites blokkeren anders)
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NieuwsBot/1.0)'}
        )

        # Haal de RSS feed op
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()

        # Parse de XML
        root = ET.fromstring(data)

        # Zoek alle items (artikelen) in de feed
        items = root.findall('.//item')

        # Verzamel de eerste 5 artikelen
        for item in items[:5]:
            titel = item.find('title')
            link = item.find('link')

            if titel is not None and titel.text:
                artikel_link = link.text if link is not None else ""
                artikelen.append((titel.text, artikel_link))

    except Exception as e:
        artikelen.append((f"Fout bij ophalen: {e}", ""))

    return artikelen


def maak_markdown(alle_artikelen, demo_modus=False):
    """Maakt een markdown bestand met alle nieuwsartikelen."""

    # Huidige datum en tijd
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

        for titel, link in artikelen:
            if link:
                md.append(f"- [{titel}]({link})")
            else:
                md.append(f"- {titel}")

    md.append("")
    md.append("---")
    md.append("*Automatisch gegenereerd door nieuws.py*")

    return "\n".join(md)


def main():
    # Check of we in demo modus zijn
    demo_modus = "--demo" in sys.argv

    print("Nieuws ophalen...")

    # Verzamel nieuws van alle bronnen
    alle_artikelen = {}
    for naam, url in FEEDS.items():
        print(f"  - {naam}...")
        alle_artikelen[naam] = haal_nieuws_op(naam, url, demo_modus)

    # Maak markdown en sla op
    markdown = maak_markdown(alle_artikelen, demo_modus)

    with open("NIEUWS.md", "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\nKlaar! Nieuws opgeslagen in NIEUWS.md")

    # Toon ook in terminal
    print("\n" + "="*50)
    print(markdown)


# Start het programma
if __name__ == "__main__":
    main()
