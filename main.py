import requests
import json
import re
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_SEARCH_URL = "https://www.ugap.fr/bff/bff-searchcatalogue-prod/api/v1/menus/111/_search"
PRODUCT_BASE_URL = "http://ugap.fr"
OUTPUT_FOLDER = "json_extraits"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HEADERS = {"Content-Type": "application/json"}

def extract_json_from_html(html_content):
    pattern = r'<script type="application/json"[^>]*><!--(.*?)--></script>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    results = []
    for match in matches:
        try:
            json_data = json.loads(match)
            results.append(json_data)
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON: {e}")
            results.append({"raw_text": match, "error": str(e)})
    return results

def get_product_urls():
    urls = []
    #page = 1
    for page in range(1, 121):
        print(f"Requête pour la page {page}...")
        payload = {
            "selectedFacets": [],
            "sort": "PERTINENCE",
            "page": {
                "page": page,
                "sizeIndex": 0,
                "layout": "GRID",
                "totalNews": 6,
                "totalProducts": 1789
            }
        }
        response = requests.post(BASE_SEARCH_URL, json=payload, headers=HEADERS)
        sleep(0.1)  # Pause pour éviter de surcharger le serveur
        if response.status_code != 200:
            print(f"Erreur lors de la récupération de la page {page}: {response.status_code}")


        data = response.json()
        docs = data.get("documents", [])
        if not docs:
            #page += 1
            continue

        for doc in docs:
            if doc.get("documentType") == "product":
                route = doc.get("route")
                if route:
                    urls.append(f"{PRODUCT_BASE_URL}{route}")
        #page += 1

    print(f"Total URLs collectées : {len(urls)}")
    return urls
"""
def process_url(url):
    request = requests.get(url)
    if request.status_code != 200:
        print(f"Erreur lors de la récupération de l'URL {url}: statut {request.status_code}")
        return

    html_content = request.content.decode()
    json_results = extract_json_from_html(html_content)

    # save json_results to file
    #file_id = url.split('-')[-1].split('.')[0]
    #json_file = os.path.join("raw_extract", f"json_{file_id}.json")
    #with open(json_file, 'w', encoding='utf-8') as f:
    #    json.dump(json_results, f, indent=2, ensure_ascii=False)


    if not json_results:
        return

    try:
        product = json_results[0]['data']['productData']
        li_elements = BeautifulSoup(product.get('strongPoints', '').replace('&gt;', '>'), 'html.parser').find_all('li')
        title = product.get('title', '')
        conditionnement = title.split('-')[-1] if '-' in title else ''

        caracteristiques = []
        features = product.get('features', [])
        if features and isinstance(features[0], dict):
            caracteristiques = features[0].get('features', [])

        slider_images = json_results[0]['data'].get('sliderImages', [])
        photo_sources = slider_images[0].get('sources', {}) if slider_images else {}
        photo_url = (
            photo_sources.get('l') or
            photo_sources.get('m') or
            photo_sources.get('s') or
            photo_sources.get('xs')
        )

        extracted_data = {
            "url": url,
            "designation": title,
            "conditionnement": conditionnement,
            "description": BeautifulSoup("<div>" + product.get('description', '').replace("&gt;", ">") + "</div>", "html.parser").get_text(),
            "prix_hors_taxe": product.get('exclTaxesPrice'),
            "delai_livraison": product.get('deliveryTime'),
            "pack_service": product.get('coreOffer', {}).get('text'),
            "strongPoints": [li.get_text() for li in li_elements],
            "photo": f"{PRODUCT_BASE_URL}{photo_url}" if photo_url else None,
            "documents_annexes": [
                {"url": f"{PRODUCT_BASE_URL}{doc['url']}", "description": doc["description"]}
                for doc in product.get('relatedDocuments', [])
            ],
            "caracteristiques": caracteristiques,
            "prix_degressifs": product.get('pricingPlans'),
            "fournisseur": product.get('supplier', {}).get('name'),
        }

        file_id = url.split('-')[-1].split('.')[0]
        extracted_file = os.path.join(OUTPUT_FOLDER, f"extracted_{file_id}.json")
        with open(extracted_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)

        for i, result in enumerate(json_results):
            file_name = os.path.join(OUTPUT_FOLDER, f"resultat_{file_id}_{i+1}.json")
            with open(file_name, 'w', encoding='utf-8') as f:
                if isinstance(result, dict) and "raw_text" in result:
                    f.write(result["raw_text"])
                else:
                    json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors du traitement de {url} : {e}")
"""

def process_url(url):
    request = requests.get(url)
    if request.status_code != 200:
        print(f"Erreur lors de la récupération de l'URL {url}: statut {request.status_code}")
        return

    html_content = request.content.decode()
    json_results = extract_json_from_html(html_content)

    if not json_results:
        return

    try:
        product = json_results[0]['data']['productData']
        li_elements = BeautifulSoup(product.get('strongPoints', '').replace('&gt;', '>'), 'html.parser').find_all('li')
        title = product.get('title', '')
        conditionnement = title.split('-')[-1] if '-' in title else ''

        caracteristiques = []
        features = product.get('features', [])
        if features and isinstance(features[0], dict):
            caracteristiques = features[0].get('features', [])

        slider_images = json_results[0]['data'].get('sliderImages', [])
        photo_sources = slider_images[0].get('sources', {}) if slider_images else {}
        photo_url = (
            photo_sources.get('l') or
            photo_sources.get('m') or
            photo_sources.get('s') or
            photo_sources.get('xs')
        )

        fournisseur = product.get('supplier', {}).get('name')
        marque = None
        for feature in caracteristiques:
            if feature.get("label", "").lower() == "marque":
                marque = feature.get("value")
                break

        extracted_data = {
            "url": url,
            "designation": title,
            "conditionnement": conditionnement,
            "description": BeautifulSoup("<div>" + product.get('description', '').replace("&gt;", ">") + "</div>", "html.parser").get_text(),
            "prix_hors_taxe": product.get('exclTaxesPrice'),
            "delai_livraison": product.get('deliveryTime'),
            "pack_service": product.get('coreOffer', {}).get('text'),
            "strongPoints": [li.get_text() for li in li_elements],
            "photo": f"{PRODUCT_BASE_URL}{photo_url}" if photo_url else None,
            "documents_annexes": [
                {"url": f"{PRODUCT_BASE_URL}{doc['url']}", "description": doc["description"]}
                for doc in product.get('relatedDocuments', [])
            ],
            "caracteristiques": caracteristiques,
            "prix_degressifs": product.get('pricingPlans'),
            "fournisseur": fournisseur,
            "Marque": marque if marque else fournisseur
        }

        file_id = url.split('-')[-1].split('.')[0]
        extracted_file = os.path.join(OUTPUT_FOLDER, f"extracted_{file_id}.json")
        with open(extracted_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)

        for i, result in enumerate(json_results):
            file_name = os.path.join(OUTPUT_FOLDER, f"resultat_{file_id}_{i+1}.json")
            with open(file_name, 'w', encoding='utf-8') as f:
                if isinstance(result, dict) and "raw_text" in result:
                    f.write(result["raw_text"])
                else:
                    json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors du traitement de {url} : {e}")


"""
if __name__ == "__main__":
    all_urls = get_product_urls()
    for url in tqdm(all_urls, desc="Traitement des produits"):
        process_url(url)
        sleep(0.1)  # Pause pour éviter de surcharger le serveur
"""

if __name__ == "__main__":
    all_urls = get_product_urls()
    max_threads = os.cpu_count() * 2
    print(f"Nombre de threads maximum : {max_threads}")

    def traiter_urls(urls):
        failed = []
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(process_url, url): url for url in urls}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Traitement des produits"):
                url = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Erreur avec {url}: {e}")
                    failed.append(url)
                sleep(0.1)
        return failed

    failed_urls = traiter_urls(all_urls)
    retries = 1
    while failed_urls:
        print(f"\nNouvelle tentative pour {len(failed_urls)} URL(s) (essai #{retries + 1})...")
        failed_urls = traiter_urls(failed_urls)
        retries += 1

    print("\nTraitement terminé.")


#process_url("https://www.ugap.fr/vetements-et-epi-111/vetement-epi-15255/vetements-et-equipements-de-police-municipale-41516/galonnage-11435/ecusson-plastifie-rf-mediation-p4082393")

