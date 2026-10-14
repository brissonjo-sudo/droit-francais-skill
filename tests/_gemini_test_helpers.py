"""Contexte et budgets réels dans un état synthétique, aucun réseau Google."""
import time
import datetime as dt
import hashlib
import json
from pathlib import Path
from bench import etude_v2
from bench.contexte import ContexteExecution
from bench import profils_gemini, quotas_gemini


def reserver(root: Path, modele="gemini-3.8-flash", bras="A", *, secondes=300):
    meta = {"famille": "gemini", "id": "synthese", "bras": bras, "repetition": 1,
            "phase": "technique", "modele": modele, "moteur": "gemini-rest-v2", "output": str(root / "resultat.jsonl")}
    with etude_v2.verrou(root):
        r = etude_v2.reserver(root, "identite-synthetique", serie="serie-synthetique", meta=meta)
    return ContexteExecution("serie-synthetique", r["identite"], r["attempt_id"], r["tentative"], modele,
                            "gemini-rest-v2", time.monotonic()+secondes, r, root)


def ecrire_profil(root: Path, *, modele="gemini-3.8-flash", numero="123456789") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    piece = root / "preuve.txt"
    piece.write_text("PREUVE SYNTHETIQUE, AUCUN PROJET REEL", encoding="utf-8")
    data = json.loads(quotas_gemini.EXEMPLE.read_bytes())
    data.update(projet_ref="projet-synthetique", numero_projet=numero, rattachement_valide_par="Test uniquement",
                cle_projet_confirmee=True, modele=modele, observe_le=dt.datetime.now(dt.timezone.utc).isoformat(),
                autres_limites_verifiees=True, limites={"rpm": 100, "rpd": 100, "tpm_entree": 100000},
                preuve={"fichier": piece.name, "sha256": hashlib.sha256(piece.read_bytes()).hexdigest()})
    (root / "releve.json").write_text(json.dumps(data), encoding="utf-8")
    registry = {"schema": 2, "profils": [{"profil": "profil-01", "cle_env": "GEMINI_API_KEY",
                 "releve": "releve.json", "qualification": "qualification.json"}]}
    path = root / "profils.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return path
