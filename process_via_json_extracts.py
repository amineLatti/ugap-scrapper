import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from bs4 import BeautifulSoup

INPUT_FOLDER = "json_extraits"
OUTPUT_FOLDER = "outputs"
PRODUCT_BASE_URL = "https://produits.bionatis.bio"

SKIP_LIST = []

printL = 0

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_json_file(filepath):
    try:

        with open(filepath, "r", encoding="utf-8") as f:
            json_results = json.load(f)

        #print(f"[DEBUG] Fichier: {filepath} - json_results: {json.dumps(json_results)[:300]}")

        if not json_results:
            SKIP_LIST.append(filepath)
            return f"[SKIPPED] Vide: {os.path.basename(filepath)}"

        product = json_results['data']['productData']
        #print(f"[DEBUG] Fichier: {filepath} - produit: {json.dumps(product)[:300]}")
        if not product:
            SKIP_LIST.append(filepath)
            return f"[SKIPPED] Vide No product: {os.path.basename(filepath)}"
        li_elements = BeautifulSoup(product.get('strongPoints', '').replace('&gt;', '>'), 'html.parser').find_all('li')
        ##print(f"[DEBUG] Fichier: {filepath} - li_elements: {li_elements}")
        #if not li_elements:
        #    return f"[SKIPPED] Vide no strongPoints: {os.path.basename(filepath)}"
        #if not isinstance(li_elements, list):
        #    li_elements = [li_elements]
        #    if not li_elements:
        #        return f"[SKIPPED] Vide no String points: {os.path.basename(filepath)}"
        title = product.get('title', '')    
        #print(f"[DEBUG] Fichier: {filepath} - title: {title}")
        conditionnement = title.split('-')[-1] if '-' in title else ''
        #print(f"[DEBUG] Fichier: {filepath} - conditionnement: {conditionnement}")
        crossSell = product['crossSelling']
        prix_HT = product.get('startPrice')
        if prix_HT == None:
            prix_HT = product.get('exclTaxesPrice')
        if prix_HT == None:
            print(f"[DEBUG] Fichier: {filepath} - prix_HT: {prix_HT}, title: {title}")



        if product.get('startPrice') != None and isinstance(product['startPrice'], (int, float)):
            if product.get('startPrice') < prix_HT:
                prix_HT = product.get('startPrice')

        if prix_HT == 0 or prix_HT == None:
            print(f"pric HT = {prix_HT} or none in {filepath}")
        caracteristiques = []
        features = product.get('features', [])
        if features and isinstance(features[0], dict):
            caracteristiques = features[0].get('features', [])
        #print(f"[DEBUG] Fichier: {filepath} - caracteristiques: {caracteristiques}")
        slider_images = json_results['data'].get('sliderImages', [])
        #print(f"[DEBUG] Fichier: {filepath} - slider_images: {slider_images}")
        photo_sources = slider_images[0].get('sources', {}) if slider_images else {}
        #print(f"[DEBUG] Fichier: {filepath} - photo_sources: {photo_sources}")
        photo_url = (
            photo_sources.get('l') or
            photo_sources.get('m') or
            photo_sources.get('s') or
            photo_sources.get('xs')
        )
        #print(f"[DEBUG] Fichier: {filepath} - photo_url: {photo_url}")

        fournisseur = product.get('supplier', {}).get('name')
        #print(f"[DEBUG] Fichier: {filepath} - fournisseur: {fournisseur}")
        marque = None
        for feature in caracteristiques:
            if feature.get("label", "").lower() == "marque":
                marque = feature.get("value")
                break
        #print(f"[DEBUG] Fichier: {filepath} - marque: {marque}")
        extracted_data = {
            "url": product.get("productSheetUrl", ""),
            "designation": title,
            "conditionnement": conditionnement,
            "description": BeautifulSoup("<div>" + product.get('description', '').replace("&gt;", ">") + "</div>", "html.parser").get_text(),
            "prix_hors_taxe": prix_HT,
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

        #print(f"[DEBUG] Fichier: {filepath} - extracted_data: {json.dumps(extracted_data)[:300]}")
        file_id = os.path.basename(filepath).split('_')[1]
        output_path = os.path.join(OUTPUT_FOLDER, f"extracted_{file_id}.json")
        with open(output_path, "w", encoding="utf-8") as f_out:
            json.dump(extracted_data, f_out, indent=2, ensure_ascii=False)

        return f"[OK] {os.path.basename(filepath)}"
    except Exception as e:
        return f"[ERREUR] {os.path.basename(filepath)}: {e}"

def main():
    # call the function to process all JSON files in the input folder
    json_files = [
        os.path.join(INPUT_FOLDER, f)
        for f in os.listdir(INPUT_FOLDER)
        if f.startswith("resultat") and f.endswith(".json")
    ]

    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_json_file, file): file for file in json_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Traitement"):
            results.append(future.result())
    print("\nRésumé :")
    for result in results:
        if result.startswith("[SKIPPED]") or result.startswith("[ERREUR]"):
            print(result)
    print(SKIP_LIST)

if __name__ == "__main__":
    main()
