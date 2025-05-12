
import os
import json
from bs4 import BeautifulSoup

INPUT_FOLDER = "json_extraits"
OUTPUT_FOLDER = "output"
PRODUCT_BASE_URL = "https://www.societe.com"

def extract_product_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_results = json.load(f)

        product = (
            json_results[0].get('data', {}).get('productData')
            if json_results and isinstance(json_results[0], dict)
            else None
        )
        if not product:
            return f"[ERREUR] {file_path} : Données 'productData' manquantes ou incorrectes"

        name = product.get("name", "")
        ref = product.get("reference", "")
        price = product.get("price", "")
        stock = product.get("stock", "")
        brand = product.get("brand", {}).get("name", "")

        # Description
        desc_html = product.get("description", "")
        if not isinstance(desc_html, str):
            desc_html = ""
        description = BeautifulSoup(f"<div>{desc_html.replace('&gt;', '>')}</div>", "html.parser").get_text()

        # Strong points
        strong_points_html = product.get("strongPoints", "")
        if not isinstance(strong_points_html, str):
            strong_points_html = ""
        li_elements = BeautifulSoup(strong_points_html.replace('&gt;', '>'), 'html.parser').find_all('li')
        strong_points = [li.get_text(strip=True) for li in li_elements]

        # Images
        slider_images = product.get("sliderImages", [])
        photo_sources = (
            slider_images[0].get("sources", {}) if slider_images and isinstance(slider_images[0], dict) else {}
        )
        photos = list(photo_sources.values()) if isinstance(photo_sources, dict) else []

        # Documents annexes
        annexes = [
            {
                "url": f"{PRODUCT_BASE_URL}{doc['url']}",
                "description": doc.get("description", "")
            }
            for doc in product.get("relatedDocuments", [])
            if isinstance(doc, dict) and "url" in doc
        ]

        return {
            "fichier": os.path.basename(file_path),
            "nom": name,
            "reference": ref,
            "prix": price,
            "stock": stock,
            "marque": brand,
            "description": description,
            "points_forts": strong_points,
            "photos": photos,
            "documents_annexes": annexes,
        }

    except Exception as e:
        return f"[ERREUR] {file_path} : {str(e)}"

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_file = os.path.join(OUTPUT_FOLDER, "produits.json")
    results = []

    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".json"):
            file_path = os.path.join(INPUT_FOLDER, filename)
            result = extract_product_data(file_path)
            results.append(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Extraction terminée. Résultats enregistrés dans {output_file}")

if __name__ == "__main__":
    main()
