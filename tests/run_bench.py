#!/usr/bin/env python3
"""run_bench.py — benchmark agentique du skill recherche-juridique.

Ce que `run_eval.py` ne peut pas mesurer. Celui-ci appelle le modèle **sans
outils** et le dit lui-même : ses sondes de provenance testent l'instinct de
refus, pas la boucle outillée réelle. Or la promesse du skill — « aucune
référence ne se produit de mémoire » — ne se vérifie qu'avec les outils
branchés, en regardant si l'identifiant cité vient bien d'un appel.

D'où trois bras, joués sur le même corpus :

    A — modèle seul, aucun skill, aucun outil     (témoin)
    B — skill appliqué, aucun outil               (méthode seule)
    C — skill appliqué, connecteur MCP disponible (production)

Le verdict combine deux sources qui ne peuvent pas se substituer l'une à
l'autre : des **contrôles déterministes sur la trace** (l'identifiant cité
figure-t-il dans un résultat d'outil ? l'outil attendu a-t-il été appelé ? la
date de référence a-t-elle été passée ?) et un **juge-modèle** sur la réponse
augmentée du résumé de trace. Un cas passe s'il satisfait les deux : un juge
indulgent ne peut pas faire réussir une sonde à lui seul.

Usage
-----
    python tests/run_bench.py --verifier-corpus        # hors réseau, joué en CI
    python tests/run_bench.py --only L-1 --bras C --sans-juge --garder-flux
    python tests/run_bench.py --bras A,B,C --repeats 3 --sortie bench/runs/x.jsonl
    python tests/run_bench.py --reprendre bench/runs/x.jsonl

Prérequis du bras C : `AUTH0_CLIENT_ID` et `AUTH0_CLIENT_SECRET` (ou un
`MCP_ACCESS_TOKEN` déjà valide) dans l'environnement. Rien n'est écrit sur
disque ni passé en ligne de commande.

Stdlib uniquement, comme le reste des sondes du dépôt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

TESTS = Path(__file__).resolve().parent
RACINE = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "skill" / "scripts"))

from droit_francais.config import load_dotenv  # noqa: E402

# Deux fichiers, deux usages, tous deux ignorés par Git :
#   - `.env` à la racine : identifiants Auth0 du connecteur MCP (bras C) ;
#   - `skill/scripts/.env` : clés PISTE, utiles au seul mode `--mcp-local`.
# `load_dotenv` n'écrase jamais une variable déjà exportée : l'environnement
# explicite garde la priorité, y compris en CI où rien n'est lu sur disque.
load_dotenv(script_dir=RACINE)
load_dotenv()

from bench import agents, cases, juge as juge_mod, verdicts  # noqa: E402
from bench.cadence import Cadence  # noqa: E402
from bench.jeton import JetonIndisponible, obtenir, secrets_surveilles  # noqa: E402
from bench.journal import Journal, deja_faits  # noqa: E402

CORPUS = TESTS / "bench-cases.csv"
DOCUMENTS = TESTS / "fixtures" / "bench" / "corpus"
SKILL = RACINE / "skill" / "SKILL.md"
RUNS = TESTS / "bench" / "runs"


def outils_connus() -> frozenset[str]:
    """Noms d'outils du serveur MCP — source unique, sans dépendance au SDK."""
    try:
        from mcp_server.catalog import EXPECTED_TOOLS

        return frozenset(EXPECTED_TOOLS)
    except ImportError:  # pragma: no cover — le catalogue est en stdlib pure
        return frozenset()


def empreinte_skill() -> str:
    if not SKILL.is_file():
        return ""
    return hashlib.sha256(SKILL.read_bytes()).hexdigest()


def version_skill() -> str:
    if not SKILL.is_file():
        return ""
    trouve = re.search(r"^\s+version:\s*(\d+\.\d+\.\d+)", SKILL.read_text(encoding="utf-8"), re.M)
    return trouve.group(1) if trouve else ""


def composer_prompt(cas: cases.Cas) -> str:
    """Question de la sonde, augmentée des documents à auditer s'il y en a.

    Les documents sont injectés dans le message : aucun bras ne dispose d'outil
    de lecture de fichiers, et le corpus DOC-AUDIT doit rester identique d'un
    bras à l'autre pour que la comparaison ait un sens.
    """
    if not cas.documents:
        return cas.question
    morceaux = [cas.question, ""]
    for nom in cas.documents:
        chemin = DOCUMENTS / nom
        contenu = chemin.read_text(encoding="utf-8") if chemin.is_file() else "(document introuvable)"
        morceaux += [f"--- DÉBUT DOCUMENT : {nom} ---", contenu, f"--- FIN DOCUMENT : {nom} ---", ""]
    return "\n".join(morceaux)


def verifier_corpus(arguments: argparse.Namespace) -> int:
    """Contrôle hors réseau du corpus — c'est l'étape jouée en CI."""
    try:
        corpus = cases.charger(CORPUS, outils_connus=outils_connus(), racine_documents=DOCUMENTS)
    except cases.CorpusInvalide as exc:
        print(f"❌ corpus invalide : {exc}", file=sys.stderr)
        return 1

    valides = [c for c in corpus if c.valide]
    modes = sorted({c.mode for c in corpus})
    print(f"✅ Corpus lisible : {len(corpus)} sonde(s), {len(modes)} axe(s) — {', '.join(modes)}.")
    print(f"   {len(valides)} validée(s) par un relecteur, {len(corpus) - len(valides)} brouillon(s).")

    couverts = {
        outil
        for cas in corpus
        for groupe in cas.outils_attendus.split(";")
        for outil in groupe.split("|")
        if outil.strip()
    }
    manquants = sorted(outils_connus() - couverts)
    if manquants:
        print(f"⚠️  outil(s) MCP non couvert(s) par le corpus : {', '.join(manquants)}")
    return 0


def executer(arguments: argparse.Namespace) -> int:
    try:
        corpus = cases.charger(CORPUS, outils_connus=outils_connus(), racine_documents=DOCUMENTS)
    except cases.CorpusInvalide as exc:
        print(f"❌ corpus invalide : {exc}", file=sys.stderr)
        return 2

    retenus = cases.filtrer(
        corpus,
        seulement=arguments.only,
        bras=arguments.bras,
        inclure_brouillons=arguments.inclure_brouillons,
    )
    if not retenus:
        print("❌ aucune sonde retenue (corpus non validé, ou filtres trop stricts)", file=sys.stderr)
        return 2

    bras_demandes = [b.strip() for b in arguments.bras.split(",") if b.strip()]
    besoin_mcp = "C" in bras_demandes

    secrets = secrets_surveilles()
    if besoin_mcp and not arguments.mcp_local:
        try:
            jeton = obtenir()
        except JetonIndisponible as exc:
            print(f"❌ bras C impossible : {exc}", file=sys.stderr)
            return 2
        import os

        os.environ["MCP_ACCESS_TOKEN"] = jeton.valeur
        secrets = secrets_surveilles()

    options = agents.Options(
        modele=arguments.model,
        url_mcp=arguments.url,
        timeout_s=arguments.timeout_cas,
        executable=arguments.executable,
        interpreteur_python=arguments.python,
        mcp_local=arguments.mcp_local,
        garder_flux=arguments.garder_flux,
    )
    backend = agents.backend(arguments.agent)

    sortie = Path(arguments.sortie) if arguments.sortie else RUNS / f"{_etiquette(arguments)}.jsonl"
    acquis = deja_faits(arguments.reprendre) if arguments.reprendre else set()
    if arguments.reprendre and Path(arguments.reprendre) == sortie and acquis:
        print(f"↻ reprise : {len(acquis)} run(s) déjà acquis, ignorés.")

    journal = Journal(sortie)
    cadence = Cadence()
    empreinte = empreinte_skill()
    version = version_skill()
    etiquette = _etiquette(arguments)

    total = sum(1 for _ in _programme(retenus, bras_demandes, arguments.repeats))
    fait = 0
    echecs_infra = 0

    for cas, bras, repetition in _programme(retenus, bras_demandes, arguments.repeats):
        fait += 1
        cle = (backend.nom, arguments.model, bras, cas.id, repetition)
        if cle in acquis:
            continue

        if bras == "C":
            cadence.reserver(cas.plafond_appels)

        prompt = composer_prompt(cas)
        execution = backend.executer(
            prompt=prompt, bras=bras, plafond=cas.plafond_appels, options=options
        )

        if bras == "C":
            cadence.corriger(cas.plafond_appels, len(execution.trace.appels))

        marqueur = "·"
        if execution.statut == "infra_error":
            echecs_infra += 1
            marqueur = "!"
            ligne = _ligne_infra(
                cas, bras, repetition, execution, backend.nom, arguments, empreinte, version, etiquette
            )
        else:
            ligne = _ligne_resultat(
                cas,
                bras,
                repetition,
                execution,
                backend.nom,
                arguments,
                empreinte,
                version,
                etiquette,
                secrets,
            )
            marqueur = "✓" if ligne["pass"] else "✗"

        journal.ajouter(ligne)
        print(f"[{fait}/{total}] {marqueur} {bras}/{cas.id} rep{repetition}", flush=True)

        if arguments.garder_flux and execution.flux_brut:
            brut = RUNS / "flux" / f"{etiquette}-{bras}-{cas.id}-{repetition}.jsonl"
            brut.parent.mkdir(parents=True, exist_ok=True)
            brut.write_text(execution.flux_brut, encoding="utf-8")

    print(f"\n{journal.ecrites} run(s) écrit(s) dans {sortie}")
    if echecs_infra:
        print(f"⚠️  {echecs_infra} panne(s) d'infrastructure — rejouer avec --reprendre {sortie}")
    return 0


def _programme(corpus, bras_demandes, repetitions):
    for repetition in range(1, max(1, repetitions) + 1):
        for cas in corpus:
            for bras in bras_demandes:
                if bras in cas.bras:
                    yield cas, bras, repetition


def _etiquette(arguments: argparse.Namespace) -> str:
    jour = dt.date.today().isoformat()
    return f"{version_skill() or 'inconnue'}-{arguments.agent}-{arguments.model}-{jour}"


def _base(cas, bras, repetition, execution, agent, arguments, empreinte, version, etiquette) -> dict:
    return {
        "horodatage": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "run": etiquette,
        "skill_version": version,
        "skill_sha256": empreinte,
        "agent": agent,
        "modele": execution.trace.modele or arguments.model,
        "bras": bras,
        "id": cas.id,
        "mode": cas.mode,
        "repetition": repetition,
        "num_turns": execution.trace.num_turns,
        "duration_ms": execution.trace.duration_ms,
        "duration_api_ms": execution.trace.duration_api_ms,
        "total_cost_usd": execution.trace.total_cost_usd,
        "usage": execution.trace.usage,
    }


def _ligne_infra(cas, bras, repetition, execution, agent, arguments, empreinte, version, etiquette) -> dict:
    ligne = _base(cas, bras, repetition, execution, agent, arguments, empreinte, version, etiquette)
    ligne.update({"statut": "infra_error", "motif_infra": execution.motif_infra, "pass": False})
    return ligne


def _ligne_resultat(
    cas, bras, repetition, execution, agent, arguments, empreinte, version, etiquette, secrets
) -> dict:
    trace = execution.trace
    sans_outil = bras in agents.BRAS_SANS_OUTIL

    resultat = verdicts.evaluer(
        trace,
        question=cas.question,
        sans_outil=sans_outil,
        outils_attendus=cas.outils_attendus,
        appels_interdits=cas.appels_interdits,
        plafond=cas.plafond_appels,
        date_attendue=cas.date_attendue,
        falsification_attendue=cas.falsification_attendue,
        secrets=secrets,
    )

    avis = None
    if not arguments.sans_juge:
        avis = juge_mod.juger(
            bras=bras,
            comportement_attendu=cas.comportement_attendu,
            trace=trace,
            reponse=trace.texte_final,
            modele=arguments.juge_model,
            executable=arguments.executable,
        )

    ligne = _base(cas, bras, repetition, execution, agent, arguments, empreinte, version, etiquette)
    ligne.update(
        {
            "statut": "ok",
            "verdicts": resultat.par_nom(),
            "details_verdicts": {v.nom: v.detail for v in resultat.verdicts},
            "pass_deterministe": resultat.passe,
            "juge": (
                {
                    "verdict": avis.verdict,
                    "raison": avis.raison,
                    "axe_defaillant": avis.axe_defaillant,
                    "extrait": avis.extrait,
                    "modele": avis.modele,
                }
                if avis
                else None
            ),
            "pass": resultat.passe and (avis.passe if avis else True),
            "appels": [
                {
                    "outil": a.nom,
                    "arguments": a.arguments,
                    "erreur": a.is_error,
                    "identifiants": sorted(a.identifiants_renvoyes),
                }
                for a in trace.appels
            ],
            "identifiants_reponse": sorted(resultat.identifiants_reponse),
            "identifiants_non_traces": sorted(resultat.identifiants_non_traces),
            "identifiants_declares_non_verifies": sorted(resultat.identifiants_declares_non_verifies),
            "lignes_illisibles": trace.lignes_illisibles,
            "reponse": trace.texte_final,
        }
    )
    return ligne


def construire_analyseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--verifier-corpus", action="store_true", help="Valide le corpus hors réseau et sort.")
    p.add_argument("--bras", default="A,B,C", help="Bras à jouer (défaut : A,B,C).")
    p.add_argument("--only", help="Restreint à des identifiants ou des modes (séparés par des virgules).")
    p.add_argument("--repeats", type=int, default=1, help="Répétitions par cas (3 recommandé en baseline).")
    p.add_argument("--model", default="sonnet", help="Modèle évalué (défaut : sonnet).")
    p.add_argument("--juge-model", default="opus", help="Modèle juge (défaut : opus).")
    p.add_argument("--sans-juge", action="store_true", help="Verdicts déterministes seuls.")
    p.add_argument("--agent", default="claude", choices=sorted(agents.BACKENDS), help="Backend d'exécution.")
    p.add_argument("--sortie", help="Fichier JSONL de sortie.")
    p.add_argument("--reprendre", help="JSONL d'un run interrompu : les runs acquis sont sautés.")
    p.add_argument("--inclure-brouillons", action="store_true", help="Joue aussi les sondes non validées.")
    p.add_argument("--garder-flux", action="store_true", help="Conserve le flux brut de chaque run.")
    p.add_argument("--url", default=agents.Options.url_mcp, help="Endpoint MCP du bras C.")
    p.add_argument("--mcp-local", action="store_true", help="Bras C sur un serveur MCP local (stdio).")
    p.add_argument("--python", help="Interpréteur Python du serveur MCP local.")
    p.add_argument("--executable", help="Chemin de la CLI de l'agent.")
    p.add_argument("--timeout-cas", type=int, default=300, help="Délai maximal par cas, en secondes.")
    return p


def main(argv: list[str] | None = None) -> int:
    arguments = construire_analyseur().parse_args(argv)
    if arguments.verifier_corpus:
        return verifier_corpus(arguments)
    return executer(arguments)


if __name__ == "__main__":
    sys.exit(main())
