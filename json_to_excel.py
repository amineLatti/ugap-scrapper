import os
import json
import pandas as pd
from tqdm import tqdm

json_folder = "outputs"
records = []

for filename in tqdm(os.listdir(json_folder), desc="Traitement JSON"):
    if not filename.startswith("extracted_"):
        continue
    if not filename.endswith(".json"):
        continue
    path = os.path.join(json_folder, filename)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    rec = {
        # Champs simples
        "url": data.get("url"),
        "designation": data.get("designation"),
        "conditionnement": data.get("conditionnement"),
        "description": data.get("description"),
        "prix_hors_taxe": data.get("prix_hors_taxe"),
        "delai_livraison": data.get("delai_livraison"),
        "pack_service": data.get("pack_service"),
        "photo": data.get("photo"),
        # Listes regroupées en une seule colonne
        "strongPoints": " | ".join(data.get("strongPoints", [])),
        "documents_annexes": " | ".join(
            f"{doc.get('url')} ({doc.get('description','')})"
            for doc in data.get("documents_annexes", [])
        ),
        "caracteristiques": " | ".join(
            f"{c.get('label')}: {c.get('value')}"
            for c in data.get("caracteristiques", [])
        ),
        "prix_degressifs": " | ".join(
            f"{p['quantity']}u → {p['price']}"
            for p in sorted(data.get("prix_degressifs", []), key=lambda x: x["quantity"])
        ),
        "fournisseur": data.get("fournisseur"),
        "Marque": data.get("Marque"),
    }

    records.append(rec)

# Création du DataFrame et export Excel
df = pd.DataFrame(records)
df.to_excel("resultat_catalogue.xlsx", index=False)

print("✅ Fini : résultat dans resultat_catalogue.xlsx")
