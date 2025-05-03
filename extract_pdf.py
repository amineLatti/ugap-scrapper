import pandas as pd
import re
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import csv

# === Paramètres ===
excel_file = "resultat_catalogue.xlsx"
col_annexes = "documents_annexes"
col_nom_fichier = "designation"  # ou "code_produit"
output_dir = "documents_annexes"
log_file = "log_telechargement.csv"

# === Chargement Excel ===
df = pd.read_excel(excel_file)
os.makedirs(output_dir, exist_ok=True)

# === Extraction de toutes les URLs ===
all_urls = []
for index, row in df.iterrows():
    nom = re.sub(r'[^\w\-]', '_', str(row.get(col_nom_fichier, f"Ligne{index}")).strip())[:50]
    urls = re.findall(r'https?://\S+', str(row.get(col_annexes, "")))
    for i, url in enumerate(urls):
        all_urls.append((index, nom, i, url))

# === Fonction de téléchargement ===
def download_file(index, nom, i, url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        ext = os.path.splitext(url)[-1].split("?")[0]
        ext = ext if ext else ".bin"
        filename = f"{nom}_{i+1}{ext}"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        return [index, filename, url, "OK"]
    except Exception as e:
        return [index, "", url, f"Erreur : {e}"]

# === Téléchargement multi-thread avec barre de progression ===
results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(download_file, idx, nom, i, url) for idx, nom, i, url in all_urls]
    for future in tqdm(as_completed(futures), total=len(futures), desc="Téléchargement"):
        results.append(future.result())

# === Écriture du log CSV ===
with open(log_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Ligne", "Nom du fichier", "URL", "Statut"])
    writer.writerows(results)

print(f"\n✅ Téléchargement terminé. Log enregistré dans {log_file}")
