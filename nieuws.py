"""
Nieuwsaggregator - Stap 1
Haalt nieuwskoppen op van AD, FD en NOS via RSS feeds.

Gebruik:
    python3 nieuws.py          # Normale modus (haalt echte feeds op)
    python3 nieuws.py --demo   # Demo modus (toont voorbeelddata)
"""

import urllib.request
import xml.etree.ElementTree as ET
import sys

# RSS feed URLs van de nieuwssites
FEEDS = {
    "NOS": "https://feeds.nos.nl/nosnieuwsalgemeen",
    "AD": "https://www.ad.nl/rss.xml",
    "FD": "https://fd.nl/rss/fd-nieuws"
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
    """Haalt nieuwsartikelen op van een RSS feed."""
    print(f"\n{'='*50}")
    print(f"  {naam}")
    print('='*50)

    # Demo modus: toon voorbeelddata
    if demo_modus:
        for i, (titel, link) in enumerate(DEMO_DATA.get(naam, []), 1):
            print(f"\n{i}. {titel}")
            print(f"   Link: {link}")
        return

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
        # RSS feeds hebben meestal deze structuur: rss > channel > item
        items = root.findall('.//item')

        if not items:
            print("Geen artikelen gevonden")
            return

        # Toon de eerste 5 artikelen
        for i, item in enumerate(items[:5], 1):
            titel = item.find('title')
            link = item.find('link')

            if titel is not None:
                print(f"\n{i}. {titel.text}")
                if link is not None:
                    print(f"   Link: {link.text}")

    except Exception as e:
        print(f"Fout bij ophalen: {e}")
        print("Tip: Probeer 'python3 nieuws.py --demo' voor een demonstratie")

def main():
    # Check of we in demo modus zijn
    demo_modus = "--demo" in sys.argv

    print("\n" + "="*50)
    print("   NIEUWSOVERZICHT")
    if demo_modus:
        print("   (Demo modus)")
    print("="*50)

    for naam, url in FEEDS.items():
        haal_nieuws_op(naam, url, demo_modus)

    print("\n" + "="*50)
    print("Klaar!")
    print("="*50 + "\n")

# Start het programma
if __name__ == "__main__":
    main()
