"""
extraire_historique.py
Extrait les conversations Claude depuis les logs VS Code
et génère un fichier daté dans le dossier "Historique Claude" sur le bureau.
"""

import json
import re
import os
from datetime import datetime

# ── Chemins ────────────────────────────────────────────────────────────────
LOGS_DIR    = os.path.join(os.environ["APPDATA"], "Code", "logs")
OUTPUT_DIR  = os.path.join(os.path.expanduser("~"), "Desktop", "Historique Claude")

# ── Préparer le dossier de sortie ──────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

today       = datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(OUTPUT_DIR, f"historique_{today}.txt")

# ── Collecte des logs Claude VSCode ───────────────────────────────────────
log_files = []
for root, dirs, files in os.walk(LOGS_DIR):
    for f in files:
        if f == "Claude VSCode.log":
            log_files.append(os.path.join(root, f))
log_files.sort()

# ── Extraction ─────────────────────────────────────────────────────────────
output_lines = []
output_lines.append("=" * 70)
output_lines.append("HISTORIQUE DES CONVERSATIONS CLAUDE - VS CODE")
output_lines.append(f"Extrait le : {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
output_lines.append("=" * 70)

for log_path in log_files:
    session_match = re.search(r"(\d{8}T\d{6})", log_path)
    session_date  = session_match.group(1) if session_match else "inconnue"
    try:
        dt            = datetime.strptime(session_date, "%Y%m%dT%H%M%S")
        session_label = dt.strftime("%d/%m/%Y à %H:%M:%S")
    except Exception:
        session_label = session_date

    messages = []

    with open(log_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if '"role":"user"' not in line and '"role": "user"' not in line:
                continue

            ts_match  = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", line)
            timestamp = ts_match.group(1) if ts_match else ""

            json_match = re.search(r"\{.*\}", line)
            if not json_match:
                continue
            try:
                data = json.loads(json_match.group(0))
                msg  = None
                if "message" in data and isinstance(data["message"], dict) and "message" in data["message"]:
                    msg = data["message"]["message"]
                elif "message" in data:
                    msg = data["message"]

                if msg and "content" in msg:
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item["text"].strip()
                            skip = (
                                not text
                                or len(text) < 3
                                or text.startswith("<ide_")
                                or text.startswith("<button")
                            )
                            if not skip:
                                messages.append((timestamp, text))
            except Exception:
                pass

    if messages:
        output_lines.append("")
        output_lines.append("─" * 70)
        output_lines.append(f"SESSION DU {session_label}")
        output_lines.append("─" * 70)
        for ts, text in messages:
            output_lines.append(f"\n[{ts}] VOUS :")
            output_lines.append(text)

# ── Écriture ───────────────────────────────────────────────────────────────
with open(output_file, "w", encoding="utf-8") as fh:
    fh.write("\n".join(output_lines))

print(f"✓ Fichier créé : {output_file}")
print(f"  {len(output_lines)} lignes générées.")
