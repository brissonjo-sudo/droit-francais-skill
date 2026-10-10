"""Dossier lisible des corrigés ; aucune validation humaine automatique."""
from __future__ import annotations

import hashlib
import os
from datetime import date
from pathlib import Path

from bench import campaign


def lien_fixture(nom: str, sortie: Path) -> str:
    """Conserver un lien utilisable si l'export Windows change de volume."""
    cible = campaign.FIXTURES / nom
    try:
        return os.path.relpath(cible, sortie.parent).replace(os.sep, "/")
    except ValueError:
        return cible.as_posix()


def exporter(sortie: Path) -> int:
    """Afficher questions, critères et preuves sans modifier le corpus."""
    if sortie.resolve() == campaign.CORPUS.resolve():
        raise ValueError("le dossier de revue ne peut pas remplacer le corpus")
    cases = campaign.corpus()
    provenance = campaign.read_json(campaign.CORPUS).get("provenance_redaction", {})
    empreinte = hashlib.sha256(campaign.CORPUS.read_bytes()).hexdigest()
    lignes = [
        "# Dossier de revue des 36 corrigés",
        "",
        "Document généré depuis tests/campaign/cases.json avant toute collecte.",
        "Les propositions de correction restent des brouillons tant que la revue",
        "humaine n'est pas inscrite dans le corpus. Ce dossier ne les valide pas.",
        "",
        f"Empreinte SHA-256 du corpus : {empreinte}.",
        f"Corrigés humains validés : {sum(campaign.gold_pret(c) for c in cases)}/36.",
        "",
        f"Rédaction des brouillons : {provenance.get('outil', 'à préciser')} ; famille {provenance.get('famille', 'à préciser')}.",
        f"Modèle exact : {provenance.get('modele_exact', 'non attesté')}. Revue humaine : non effectuée.",
        "Les brouillons sont assistés par LLM ; une revue indépendante doit contrôler le biais de famille.",
        "",
        "## Consignes de revue",
        "",
        "Commencer par les modes 1, 3, 5 et 18 du pilote, puis traiter tous les",
        "autres cas avant la collecte. Confirmer les dates, le champ, les faits",
        "stipulés, les conséquences et les alternatives admissibles. Distinguer",
        "exactitude de fond, fidélité des citations et respect de la procédure.",
        "",
        "Les dates de droit sont propres à chaque cas : une consultation le",
        "10 octobre 2026 n'impose pas le droit de cette date à des faits anciens.",
        "Les pièces synthétiques ne constituent jamais du droit positif.",
        "",
        "Après correction et accord explicite, inscrire dans le JSON le statut",
        "valide, le nom du relecteur et la date de validation. Régénérer ce dossier",
        "puis commiter avant de figer. Une modification après gel exige une nouvelle",
        "série. Aucune réponse collectée dans la campagne n'a servi à établir ces brouillons.",
        "",
        "## Limites du corpus",
        "",
        "Deux cas par mode suffisent à explorer, pas à généraliser à tout le droit.",
        "Plusieurs modes réutilisent des sources : leurs résultats sont corrélés.",
        "Les contrôles documentaires et les cas où tous les faits sont stipulés",
        "isolent un raisonnement ; ils ne reproduisent pas tout un dossier réel.",
        "Le pilote doit détecter les cas trop faciles ou ambigus avant le gel",
        "de la campagne principale. Ses réponses restent séparées de celle-ci.",
        "",
    ]
    for c in cases:
        g = c["gold"]
        pilote = " — pilote" if c["mode"] in (1, 3, 5, 18) else ""
        lignes.extend([
            f"## {c['id']} — {c['intitule']}{pilote}",
            "",
            f"Type : {c['type']}. Date utile : {date.fromisoformat(c['date_reference']).strftime('%d/%m/%Y')}.",
            f"Criticité proposée : {g['criticite']}. Statut : {g['statut']}.",
            "",
            "### Question envoyée aux modèles",
            "",
            c["question"],
            "",
        ])
        if c["documents"]:
            lignes.extend(["Pièces fournies à tous les bras :", ""])
            for nom in c["documents"]:
                cible = lien_fixture(nom, sortie)
                lignes.append(f"- [{nom}]({cible})")
            lignes.append("")
        lignes.extend(["### Proposition de corrigé", "", g["conclusion_attendue"], "",
                       f"Abstention ciblée attendue : {g['abstention_attendue']}.",
                       f"Portée : {g.get('portee_abstention') or 'aucune abstention de fond si les sources sont accessibles'}.",
                       "", "Critères de fond :", ""])
        lignes.extend(f"- {t}" for t in g["criteres_communs"])
        if g.get("alternatives_admissibles"):
            lignes.extend(["", "Alternatives admissibles :", ""])
            lignes.extend(f"- {t}" for t in g["alternatives_admissibles"])
        lignes.extend(["", f"Refus excessif : {g.get('refus_excessif', 'à préciser')}.", "",
                       "Informations manquantes : " + (" ; ".join(g.get("informations_manquantes", [])) or "aucune pour le point circonscrit") + ".",
                       g.get("justification_informations_manquantes", "à préciser"), "",
                       "### Sources consultées pour la préparation", ""])
        for s in g["sources_verifiees"]:
            url = s["url"]
            if url.startswith("fixture:"):
                url = lien_fixture(url[8:], sortie)
            lignes.extend([
                f"- [{s.get('titre', s['url'])}]({url})",
                f"  - Consultation : {date.fromisoformat(s['date_consultation']).strftime('%d/%m/%Y')} ; voie : {s.get('mode_consultation', 'à préciser')}.",
                f"  - Version : {s['version_applicable']}",
                f"  - Type : {s.get('type_extrait', 'à préciser')} ; citation exacte vérifiée par : {s.get('citation_verifiee_par') or 'non attestée'}.",
                f"  - Résumé ou observation (ne vaut pas citation exacte) : {s['extrait_utile'].replace(chr(10), ' ')}",
                f"  - Limites : {s.get('limites', 'à confirmer en revue humaine')}",
            ])
        lignes.extend(["", "Revue humaine : à compléter dans le corpus après examen.", ""])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(lignes).rstrip() + "\n", encoding="utf-8", newline="\n")
    return len(cases)
