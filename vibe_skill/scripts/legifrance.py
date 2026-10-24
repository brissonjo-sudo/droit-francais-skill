#!/usr/bin/env python3
"""legifrance.py — récupération fiable en source primaire via les API PISTE.

Objet
-----
Matérialise le « Palier 3 » du skill *recherche-juridique*. Convertit
l'exigence P1 (primarité / lecture documentée) et la **règle de provenance**
en appel d'outil déterministe : tout identifiant ``LEGIARTI``, toute date de
version en vigueur et tout statut (en vigueur / modifié / abrogé) provient
d'une réponse officielle de l'API Légifrance, et non de la mémoire du modèle.

Trois couvertures, sur deux API :

* **Légifrance** (DILA) — textes : codes, lois, décrets, arrêtés
  → ``article``, ``search`` ;
* **Légifrance** — jurisprudence administrative et constitutionnelle :
  Conseil d'État (fond ``CETAT``) et Conseil constitutionnel (fond
  ``CONSTIT``) → ``ceta``, ``constit`` ;
* **Judilibre** (Cour de cassation) — jurisprudence judiciaire : Cour de
  cassation, cours d'appel, tribunaux judiciaires et de commerce
  → ``juri``, ``decision``, ``taxonomy``.

**Judilibre ne couvre ni le Conseil d'État ni le Conseil constitutionnel** :
ces deux juridictions passent par les fonds Légifrance ``CETAT`` et
``CONSTIT``. Supprimer ``ceta``/``constit`` en croyant Judilibre exhaustif
retire au skill toute voie outillée vers la jurisprudence administrative et
constitutionnelle — c'est exactement ce qui s'est produit en v3.0.0→#6.

La même exigence de provenance s'applique aux trois : une décision ne se cite
qu'après récupération réussie, jamais sur la seule foi d'un résultat de
recherche.

Authentification
----------------
OAuth2 *client_credentials* sur PISTE. Le script lit ses identifiants dans
l'environnement (jamais en clair dans le dépôt) :

    LEGIFRANCE_CLIENT_ID         (obligatoire)
    LEGIFRANCE_CLIENT_SECRET     (obligatoire)
    LEGIFRANCE_ENV               "prod" (défaut) | "sandbox"   (optionnel)
    JUDILIBRE_KEY_ID             (optionnel — voir ci-dessous)
    JUDILIBRE_ENV                "prod" | "sandbox"            (optionnel :
                                 à défaut, reprend LEGIFRANCE_ENV)

Judilibre accepte deux modes d'authentification selon la façon dont
l'application PISTE a été déclarée : l'en-tête ``KeyId`` documenté par la
Cour de cassation, ou le jeton OAuth2 ``Authorization: Bearer`` commun aux
API PISTE. Le script essaie ``KeyId`` en premier si ``JUDILIBRE_KEY_ID`` est
défini, puis bascule automatiquement sur le jeton OAuth. Aucune
configuration supplémentaire n'est nécessaire si l'application est abonnée
à l'API « Judilibre » avec les mêmes identifiants que Légifrance.

Obtention des identifiants : créer un compte sur https://piste.gouv.fr,
y déclarer une application abonnée à l'API « Légifrance », récupérer le
*client id* et le *client secret*. Voir scripts/README.md.

Plus simple que `export` : copier ``.env.example`` en ``.env`` (déjà
gitignoré), y coller les deux identifiants — le script charge
automatiquement un ``.env`` présent dans le dossier courant ou à côté du
script (variable ``LEGIFRANCE_DOTENV`` pour pointer un autre fichier).
Les variables déjà définies dans l'environnement ont la priorité.

Dépendances
-----------
Aucune : bibliothèque standard Python 3.8+ uniquement (urllib, json, argparse).

Usage
-----
    python legifrance.py ping
    python legifrance.py article LEGIARTI000006419288
    python legifrance.py article --date 2024-01-01 LEGIARTI000006419288
    python legifrance.py search "2212-2" --code CGCT
    python legifrance.py search "2212-2" --code CGCT --date 2010-01-01
    python legifrance.py article --json LEGIARTI000006419288   # sortie brute JSON

    # Jurisprudence administrative / constitutionnelle (Légifrance)
    python legifrance.py ceta "440258"           # Conseil d'État (fond CETAT)
    python legifrance.py constit "2021-940 QPC"  # Conseil constitutionnel (CONSTIT)

    # Jurisprudence judiciaire (Judilibre)
    python legifrance.py juri "soins psychiatriques sans consentement"
    python legifrance.py juri "police municipale" --jurisdiction cc --date-start 2020-01-01
    python legifrance.py juri "mainlevée" --publication b --sort date --order desc
    python legifrance.py decision 5fca...            # texte intégral d'une décision
    python legifrance.py taxonomy chamber --jurisdiction cc

Codes de sortie
---------------
    0  succès
    2  identifiants d'environnement manquants / mauvais usage
    3  échec d'authentification PISTE
    4  échec de la requête API (HTTP non-2xx, contenu illisible)
    5  ressource introuvable (article, décision ou recherche sans résultat)

Le code 4/5 est, côté skill, un **déclencheur d'abstention** (§7) : pas de
citation sans récupération réussie.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Le CLI est aussi importé directement par les contrôles statiques. Dans ce
# cas, importlib ne place pas automatiquement son dossier dans ``sys.path``.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from droit_francais.config import (
    judilibre_base as _judilibre_base,
    legifrance_environment as _env,
    load_dotenv,
)
from droit_francais.errors import LegifranceError
from droit_francais.judilibre import (
    _TOKEN_CACHE,
    auth_modes as _judilibre_auth_modes,
    get_token_cached,
    judilibre_get,
)
from droit_francais.legifrance import api_call, get_token

# Judilibre — valeurs de référence (spécification OpenAPI JUDILIBRE-public.json).
# Les listes dépendantes de la juridiction (chamber, formation, theme) se
# récupèrent à la demande via la commande `taxonomy`.
JURIDICTIONS = {
    "cc": "Cour de cassation",
    "ca": "Cour d'appel",
    "tj": "Tribunal judiciaire",
    "tcom": "Tribunal de commerce",
}
PUBLICATIONS = {
    "b": "Bulletin",
    "r": "Rapport annuel",
    "l": "Lettre de chambre",
    "c": "Communiqué",
}
SOLUTIONS = (
    "annulation", "avis", "cassation", "decheance", "designation",
    "irrecevabilite", "nonlieu", "qpc", "rabat",
)
DECISION_TYPES = ("arret", "qpc", "ordonnance", "saisie")
SEARCH_FIELDS = (
    "expose", "moyens", "motivations", "dispositif",
    "annexes", "sommaire", "titrage",
)

# Codes fréquents : clé CLI -> (identifiant LEGITEXT, libellé officiel).
#
# Les deux colonnes servent à deux choses distinctes, à ne pas intervertir :
# le **LEGITEXT** adresse la fiche du code par URL (voie web, miroir de
# gabarits-requetes.md) ; le **libellé** est ce qu'attend la facette
# `NOM_CODE` du moteur `/search`, qui ignore silencieusement un LEGITEXT
# (zéro résultat, sans erreur — voir `cmd_search`). Les libellés sont ceux
# renvoyés par `/consult/legiPart`, vérifiés par aller-retour sur la facette.
CODES = {
    "CGCT": ("LEGITEXT000006070633", "Code général des collectivités territoriales"),
    "CP": ("LEGITEXT000006070719", "Code pénal"),
    "CODE_PENAL": ("LEGITEXT000006070719", "Code pénal"),
    "CPP": ("LEGITEXT000006071154", "Code de procédure pénale"),
    "CSI": ("LEGITEXT000025503132", "Code de la sécurité intérieure"),
    "CDR": ("LEGITEXT000006074228", "Code de la route"),
    "CODE_ROUTE": ("LEGITEXT000006074228", "Code de la route"),
    "CRPA": (
        "LEGITEXT000031366350",
        "Code des relations entre le public et l'administration",
    ),
    "GFP": ("LEGITEXT000044416551", "Code général de la fonction publique"),
    "CENV": ("LEGITEXT000006074220", "Code de l'environnement"),
    "CSP": ("LEGITEXT000006072665", "Code de la santé publique"),
    "CURBA": ("LEGITEXT000006074075", "Code de l'urbanisme"),
}

# Parties d'un code : lettre précédant le numéro d'article (L législative,
# R réglementaire en Conseil d'État, D décret simple, A arrêté). Le moteur
# n'accepte que la forme collée « L2212-2 » ; quand l'utilisateur ne donne
# pas la lettre, elles sont toutes proposées en alternative (voir
# `_num_variantes`).
PARTIES_CODE = ("L", "R", "D", "A")

# Fonds de jurisprudence Légifrance — juridictions NON couvertes par Judilibre.
# Judilibre (constantes plus haut) couvre le judiciaire : Cass., CA, TJ, tcom.
# Le Conseil d'État et le Conseil constitutionnel n'y figurent pas et restent
# accessibles par le moteur /search de Légifrance. Ne pas fusionner ces deux
# ensembles : c'est leur confusion qui a fait disparaître `ceta` et `constit`.
# Les clés sont les noms de sous-commandes (cf. build_parser / args.command).
FONDS_JURIS = {
    "ceta": {"fond": "CETAT", "prefix": "CETATEXT", "label": "Conseil d'État"},
    "constit": {"fond": "CONSTIT", "prefix": "CONSTEXT",
                "label": "Conseil constitutionnel"},
}


# --------------------------------------------------------------------------- #
# Commandes
# --------------------------------------------------------------------------- #
def cmd_ping(args) -> int:
    """Vérifie l'authentification et la disponibilité de l'API."""
    token = get_token()
    print("✅ Authentification PISTE réussie (jeton obtenu).")
    print(f"   Environnement : {os.environ.get('LEGIFRANCE_ENV', 'prod')}")
    print(f"   API : {_env()['api']}")
    # Sonde légère : récupération d'un article connu et stable (art. 1 CP-like).
    try:
        api_call("/consult/getArticle", {"id": "LEGIARTI000006419288"}, token)
        print("✅ Endpoint /consult/getArticle joignable.")
    except LegifranceError as exc:
        print(f"⚠️  Jeton OK mais endpoint en erreur : {exc}", file=sys.stderr)
        return 4

    # Sonde Judilibre — non bloquante : l'application PISTE peut n'être
    # abonnée qu'à Légifrance. Le fond jurisprudence est alors indisponible,
    # ce qui doit être visible sans faire échouer le ping. Le jeton obtenu
    # ci-dessus est déjà en cache : Judilibre le réutilise en repli OAuth.
    print(f"   Judilibre : {_judilibre_base()}")
    try:
        judilibre_get("/taxonomy", {"id": "jurisdiction"})
        print("✅ Endpoint Judilibre /taxonomy joignable.")
    except LegifranceError as exc:
        print(
            f"⚠️  Judilibre indisponible ({exc}).\n"
            "   Vérifier l'abonnement à l'API « Judilibre » sur piste.gouv.fr, "
            "ou renseigner JUDILIBRE_KEY_ID.\n"
            "   Légifrance reste utilisable ; la jurisprudence non.",
            file=sys.stderr,
        )
    return 0


def _extract_article(data: dict) -> dict | None:
    """Normalise la charge utile de getArticle, robuste aux variantes de schéma."""
    art = data.get("article")
    if art is None and isinstance(data.get("listArticle"), list) and data["listArticle"]:
        art = data["listArticle"][0]
    return art


def cmd_article(args) -> int:
    """Récupère un article par identifiant LEGIARTI et restitue ses métadonnées."""
    art_id = args.id.strip()
    if not art_id.upper().startswith("LEGIARTI"):
        raise LegifranceError(
            f"Identifiant attendu LEGIARTI… (reçu {art_id!r}). "
            "Pour rechercher par numéro d'article, utiliser la commande 'search'.",
            exit_code=2,
        )
    token = get_token()
    body: dict = {"id": art_id}
    if args.date:
        body["date"] = args.date  # AAAA-MM-JJ — version applicable à cette date
    data = api_call("/consult/getArticle", body, token)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    art = _extract_article(data)
    if not art:
        raise LegifranceError(
            f"Article {art_id} introuvable (réponse vide).", exit_code=5
        )

    etat = art.get("etat") or art.get("etatJuridique") or "?"
    num = art.get("num") or "?"
    date_debut = _fmt_date(art.get("dateDebut"))
    date_fin = _fmt_date(art.get("dateFin"))
    texte = (art.get("texte") or art.get("texteHtml") or "").strip()
    texte_plein = _strip_html(texte)

    print("─" * 60)
    print(f"Article            : {num}")
    print(f"Identifiant        : {art.get('id', art_id)}   (← provenance vérifiée)")
    print(f"Statut             : {etat}")
    print(f"En vigueur depuis  : {date_debut}")
    if date_fin and date_fin not in ("?", "2999-01-01", "9999-12-31"):
        print(f"En vigueur jusqu'au: {date_fin}")
    if args.date:
        print(f"Version demandée au: {args.date}")
    print("─" * 60)
    if texte_plein:
        print(texte_plein)
    else:
        print("(texte non renvoyé par l'API — consulter la fiche manuellement)")
    print("─" * 60)

    if str(etat).upper() not in ("VIGUEUR", "VIGUEUR_DIFF"):
        print(
            f"⚠️  Statut « {etat} » : ne pas citer comme droit positif sans "
            "vérification (voir checklist-vigueur.md).",
            file=sys.stderr,
        )
    # Citation prête à coller (gabarit format-citation.md).
    print()
    print("Citation normalisée (à compléter avec la date de consultation) :")
    print(
        f"  Art. {num}, [code], version en vigueur depuis le "
        f"{_fr_date(date_debut)}, identifiant Légifrance {art.get('id', art_id)}, "
        f"consulté le JJ/MM/AAAA"
    )
    return 0


def _num_variantes(numero: str) -> list[str]:
    """Formes canoniques du numéro à soumettre à `NUM_ARTICLE`, en une requête.

    Le moteur n'indexe qu'une seule écriture : la lettre de partie collée au
    numéro, sans point ni espace (« L2212-2 »). Les écritures usuelles à
    l'écrit juridique — « L. 2212-2 », « L 2212-2 » — n'y renvoient rien, pas
    plus que le numéro nu « 2212-2 » d'un code divisé en parties.

    Quand l'utilisateur donne la lettre, une seule forme suffit. Quand il ne
    la donne pas, le numéro nu est tenté tel quel — c'est l'écriture des
    codes non divisés, tel le code civil — puis préfixé de chaque partie
    usuelle ; les critères sont ensuite combinés par OU dans le même champ,
    ce qui coûte un seul appel.
    """
    import re

    compact = "".join(numero.split())
    # Le chiffre exigé après la lettre évite de prendre pour une partie
    # l'initiale d'un mot (« Annexe 1 » n'est pas l'article A-nnexe 1).
    m = re.match(r"^([LRDA])\.?(\d\S*)$", compact, flags=re.IGNORECASE)
    if m:
        return [f"{m.group(1).upper()}{m.group(2)}"]
    return [compact] + [f"{p}{compact}" for p in PARTIES_CODE]


def _articles_trouves(data: dict, variantes: list[str]) -> list[dict]:
    """Aplatit une réponse `/search` du fond CODE_DATE en liste d'articles.

    Sur ce fond, `results[i]["id"]` vaut `None` : les identifiants d'articles
    ne vivent que dans `results[].sections[].extracts[]`. Un extrait dont le
    numéro ne correspond à aucune variante demandée est écarté — une section
    pertinente en rapporte d'autres au passage, qu'il serait faux de
    présenter comme le résultat de la recherche.
    """
    attendus = {v.upper() for v in variantes}
    trouves: list[dict] = []
    vus: set[str] = set()
    for resultat in data.get("results") or []:
        titres = resultat.get("titles") or []
        code_titre = (titres[0].get("title") if titres else None) or "?"
        for section in resultat.get("sections") or []:
            for extrait in section.get("extracts") or []:
                art_id = extrait.get("id") or ""
                num = (extrait.get("num") or extrait.get("title") or "").strip()
                if not art_id.startswith("LEGIARTI") or art_id in vus:
                    continue
                if num.upper() not in attendus:
                    continue
                vus.add(art_id)
                trouves.append(
                    {
                        "num": num,
                        "id": art_id,
                        "code": code_titre,
                        "section": (section.get("title") or "").strip(),
                        "etat": extrait.get("legalStatus") or "?",
                        "date_debut": _fmt_date(extrait.get("dateDebut")),
                    }
                )
    return trouves


def cmd_search(args) -> int:
    """Recherche un article par numéro, optionnellement filtré sur un code.

    Payload du fond CODE_DATE. Trois contraintes de l'API, établies contre
    l'environnement de production et non déduites de la documentation :

    * la facette ``NOM_CODE`` attend le **libellé** du code, jamais son
      identifiant LEGITEXT — un LEGITEXT y renvoie zéro résultat *sans
      erreur*, panne silencieuse dont on ne peut pas distinguer l'absence
      réelle de résultat ;
    * les facettes ``TEXT_LEGAL_STATUS``, ``ARTICLE_LEGAL_STATUS`` et
      ``CODE`` déclenchent un **HTTP 500** sur ce fond : ne pas les y
      remettre pour restreindre à ce qui est en vigueur ;
    * ``DATE_VERSION`` n'est pas facultative en pratique : sans elle, le
      moteur rend une entrée par version historique du code — près de 900
      doublons pour un seul article — et la restriction à la version
      applicable est justement ce que le skill exige (§ vigueur).
    """
    nom_code = None
    if args.code:
        key = args.code.upper().replace(" ", "_")
        entree = CODES.get(key)
        if not entree:
            raise LegifranceError(
                f"Code inconnu : {args.code!r}. Codes connus : "
                f"{', '.join(sorted(CODES))}.",
                exit_code=2,
            )
        nom_code = entree[1]

    date_version = args.date or _aujourdhui()
    variantes = _num_variantes(args.numero)
    # Borne unique, appliquée à la fois à la requête et à l'affichage : un
    # --limit nul ou négatif tronquerait sinon la liste affichée à vide tout
    # en annonçant des résultats. 100 est le plafond de pageSize.
    limite = max(1, min(args.limit, 100))
    # Un critère isolé se combine en ET ; plusieurs formes concurrentes du
    # même numéro s'excluent mutuellement, donc OU.
    operateur = "OU" if len(variantes) > 1 else "ET"

    filtres: list[dict] = [
        {"facette": "DATE_VERSION", "singleDate": _epoch_ms(date_version)}
    ]
    if nom_code:
        filtres.append({"facette": "NOM_CODE", "valeurs": [nom_code]})

    body = {
        "fond": "CODE_DATE",
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": valeur,
                            "operateur": operateur,
                        }
                        for valeur in variantes
                    ],
                    "operateur": operateur,
                }
            ],
            "filtres": filtres,
            "pageNumber": 1,
            # La pagination porte sur les codes, pas sur les articles : un
            # même code peut rendre plusieurs articles (L… et R… homonymes).
            "pageSize": limite,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE",
        },
    }

    token = get_token()
    data = api_call("/search", body, token)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    articles = _articles_trouves(data, variantes)
    if not articles:
        print(
            f"Aucun article « {args.numero} »"
            + (f" dans {args.code}" if args.code else "")
            + f" dans la version en vigueur au {_fr_date(date_version)}.\n"
            "Vérifier le numéro (forme attendue : « 2212-2 » ou « L2212-2 »), "
            "élargir en retirant --code, ou interroger une autre date avec "
            "--date. Si l'identifiant est déjà connu, passer par "
            "« article <LEGIARTI> ».",
            file=sys.stderr,
        )
        return 5

    affiches = articles[:limite]
    print(
        f"{len(articles)} article(s) trouvé(s) au {_fr_date(date_version)} "
        f"— confirmer avec « article <LEGIARTI> » :"
    )
    for art in affiches:
        print("─" * 60)
        print(f"  Article     : {art['num']}")
        print(f"  Identifiant : {art['id']}")
        print(f"  Code        : {art['code']}")
        if art["section"]:
            print(f"  Emplacement : {art['section']}")
        print(f"  Statut      : {art['etat']}   (depuis le {art['date_debut']})")
    print("─" * 60)
    if len(articles) > len(affiches):
        print(f"({len(articles) - len(affiches)} autre(s) non affiché(s) — "
              "augmenter --limit.)")

    hors_vigueur = [a for a in affiches if str(a["etat"]).upper() != "VIGUEUR"]
    if hors_vigueur:
        print(
            "⚠️  "
            + ", ".join(f"{a['num']} ({a['etat']})" for a in hors_vigueur)
            + " : ne pas citer comme droit positif sans vérification "
            "(voir checklist-vigueur.md).",
            file=sys.stderr,
        )

    print(
        "\nNote : un résultat de recherche ne vaut pas lecture. Récupérer "
        "l'article par « article <LEGIARTI> » avant toute citation "
        "(règle de provenance)."
    )
    return 0


def cmd_jurisprudence(args) -> int:
    """Recherche une décision par numéro dans un fond de jurisprudence Légifrance.

    Alias : `ceta` (Conseil d'État, fond CETAT), `constit` (Conseil
    constitutionnel, fond CONSTIT). Pour la jurisprudence judiciaire
    (Cass., CA, TJ), utiliser `juri` puis `decision` — Judilibre.

    Best-effort (comme `search`) : renvoie l'identifiant officiel de la
    décision (CETATEXT / CONSTEXT), à confirmer avant citation.
    """
    cfg = FONDS_JURIS[args.command]
    token = get_token_cached()
    champ = {
        "typeChamp": "ALL",
        "criteres": [
            {"typeRecherche": "EXACTE", "valeur": args.numero, "operateur": "ET"}
        ],
        "operateur": "ET",
    }
    recherche = {
        "champs": [champ],
        "pageNumber": 1,
        "pageSize": args.limit,
        "operateur": "ET",
        "sort": "PERTINENCE",
        "typePagination": "DEFAUT",
    }
    body = {"recherche": recherche, "fond": cfg["fond"]}
    data = api_call("/search", body, token)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    results = data.get("results") or []
    if not results:
        print(
            f"Aucune décision pour « {args.numero} » dans le fond {cfg['fond']} "
            f"({cfg['label']}). Affiner le numéro ou vérifier via la source "
            "officielle.",
            file=sys.stderr,
        )
        return 5
    print(f"{len(results)} résultat(s) — {cfg['label']} — fond {cfg['fond']} :")
    for r in results[: args.limit]:
        dec_id = _first_id_with_prefix(r, (cfg["prefix"],)) or r.get("id") or "?"
        titles = r.get("titles") or []
        # Les titres renvoyés par /search contiennent le balisage <mark> de
        # surlignage des termes recherchés : le retirer avant affichage.
        title = _strip_html(
            (titles[0].get("title") if titles else None) or r.get("title") or ""
        )
        print(f"  • {dec_id}  {title}".rstrip())
    print(
        "\nNote (best-effort) : la recherche jurisprudence dépend du fond et du "
        "format du numéro. L'identifiant ci-dessus est une source de "
        "provenance ; confirmer la décision (formation, date, publication au "
        "Lebon / au recueil) sur la source officielle avant citation "
        "(règle de provenance)."
    )
    return 0


# --------------------------------------------------------------------------- #
# Commandes Judilibre
# --------------------------------------------------------------------------- #
def cmd_juri(args) -> int:
    """Recherche de jurisprudence sur Judilibre (Cour de cassation et fonds CA/TJ)."""
    params = {
        "query": args.query,
        "operator": args.operator,
        "field": args.field,
        "type": args.type,
        "jurisdiction": args.jurisdiction,
        "chamber": args.chamber,
        "formation": args.formation,
        "theme": args.theme,
        "publication": args.publication,
        "solution": args.solution,
        "date_start": args.date_start,
        "date_end": args.date_end,
        "sort": args.sort,
        "order": args.order,
        "page": args.page,
        "page_size": min(args.limit, 50),  # plafond imposé par l'API
        "resolve_references": "true" if args.resolve_references else None,
    }
    data = judilibre_get("/search", params)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    results = data.get("results") or []
    total = data.get("total", len(results))
    if not results:
        print(
            f"Aucune décision pour « {args.query} ». Élargir la requête, "
            "vérifier les filtres, ou utiliser --operator or.",
            file=sys.stderr,
        )
        return 5

    print(f"{total} décision(s) trouvée(s), {len(results)} affichée(s) :")
    print("─" * 72)
    for r in results:
        jur = JURIDICTIONS.get(r.get("jurisdiction"), r.get("jurisdiction") or "?")
        chambre = r.get("chamber") or ""
        date = _fmt_date(r.get("decision_date"))
        num = r.get("number") or "?"
        ecli = r.get("ecli") or ""
        sol = r.get("solution") or ""
        pub = r.get("publication") or []
        pub_lbl = ", ".join(PUBLICATIONS.get(p, p) for p in pub) if pub else ""
        print(f"• {jur} {chambre}, {date}, n° {num}".rstrip())
        if ecli:
            print(f"  ECLI      : {ecli}")
        if sol:
            print(f"  Solution  : {sol}")
        if pub_lbl:
            print(f"  Publication: {pub_lbl}")
        print(f"  Identifiant: {r.get('id', '?')}")
        summary = (r.get("summary") or "").strip()
        if summary:
            print(f"  Sommaire  : {_truncate(_strip_html(summary), 300)}")
        highlights = r.get("highlights") or {}
        for zone, extracts in list(highlights.items())[:2]:
            if extracts:
                print(f"  [{zone}] {_truncate(_strip_html(str(extracts[0])), 220)}")
        print("─" * 72)

    print(
        "\nRègle de provenance : ne citer une décision qu'après récupération "
        "de son texte via « decision <identifiant> ». Un résultat de "
        "recherche ne vaut pas lecture."
    )
    return 0


def cmd_decision(args) -> int:
    """Récupère le texte intégral et les métadonnées d'une décision Judilibre."""
    params = {
        "id": args.id.strip(),
        "resolve_references": "true",
        "query": args.query,
        "operator": args.operator if args.query else None,
    }
    data = judilibre_get("/decision", params)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if not data or not data.get("id"):
        raise LegifranceError(
            f"Décision {args.id} introuvable (réponse vide).", exit_code=5
        )

    jur = JURIDICTIONS.get(data.get("jurisdiction"), data.get("jurisdiction") or "?")
    chambre = data.get("chamber") or ""
    date = _fmt_date(data.get("decision_date"))
    num = data.get("number") or "?"
    pub = data.get("publication") or []
    pub_lbl = ", ".join(PUBLICATIONS.get(p, p) for p in pub) if pub else "non publiée"

    print("─" * 72)
    print(f"Juridiction        : {jur} {chambre}".rstrip())
    print(f"Date               : {date}")
    print(f"Numéro             : {num}")
    print(f"ECLI               : {data.get('ecli') or '?'}")
    print(f"Formation          : {data.get('formation') or '?'}")
    print(f"Solution           : {data.get('solution') or '?'}")
    print(f"Publication        : {pub_lbl}")
    print(f"Identifiant        : {data.get('id')}   (← provenance vérifiée)")
    print("─" * 72)

    summary = _strip_html(data.get("summary") or "")
    if summary:
        print("SOMMAIRE")
        print(summary)
        print("─" * 72)

    if args.zones:
        zones = data.get("zones") or {}
        text = data.get("text") or ""
        if zones and text:
            for name, spans in zones.items():
                if not isinstance(spans, list):
                    continue
                chunk = " ".join(
                    text[s.get("start", 0): s.get("end", 0)]
                    for s in spans
                    if isinstance(s, dict)
                ).strip()
                if chunk:
                    print(f"[{name.upper()}]")
                    print(_strip_html(chunk))
                    print()
        else:
            print("(zonage non disponible pour cette décision)")
    else:
        text = _strip_html(data.get("text") or "")
        print(text if text else "(texte non renvoyé par l'API)")
    print("─" * 72)

    if not pub:
        print(
            "⚠️  Décision non publiée au Bulletin : portée doctrinale limitée, "
            "à ne pas présenter comme un arrêt de principe.",
            file=sys.stderr,
        )

    print()
    print("Citation normalisée (à compléter avec la date de consultation) :")
    print(
        f"  {jur} {chambre}, {_fr_date(date)}, n° {num}"
        f"{', ' + data.get('ecli') if data.get('ecli') else ''}"
        f", {pub_lbl}, identifiant Judilibre {data.get('id')}, "
        "consulté le JJ/MM/AAAA".replace(" ,", ",")
    )
    return 0


def cmd_taxonomy(args) -> int:
    """Liste les valeurs acceptées par un filtre Judilibre (chambre, formation, thème…)."""
    params = {"id": args.key, "context_value": args.jurisdiction}
    data = judilibre_get("/taxonomy", params)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    result = data.get("result", data)
    if isinstance(result, dict):
        for key, label in result.items():
            print(f"  {key:<24} {label}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _first_id_with_prefix(obj, prefixes) -> str | None:
    """Cherche récursivement un identifiant commençant par l'un des préfixes.

    Nécessaire côté jurisprudence Légifrance : dans les réponses de /search,
    ``results[i]["id"]`` vaut ``None`` et l'identifiant officiel n'existe que
    sous ``results[i]["titles"][0]["id"]``.
    """
    prefixes = tuple(prefixes)
    if isinstance(obj, str):
        return obj if obj.startswith(prefixes) else None
    if isinstance(obj, dict):
        for v in obj.values():
            found = _first_id_with_prefix(v, prefixes)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = _first_id_with_prefix(v, prefixes)
            if found:
                return found
    return None


def _aujourdhui() -> str:
    """Date civile locale (AAAA-MM-JJ), défaut des recherches par version.

    Date **locale** et non UTC : une réforme entre en vigueur à une date du
    calendrier français, et un poste à Paris interrogé en soirée obtiendrait
    en UTC la version de la veille — soit, le jour même d'une entrée en
    vigueur, le texte que le skill a précisément pour objet de ne plus citer.
    """
    import datetime

    return datetime.date.today().strftime("%Y-%m-%d")


def _epoch_ms(iso_date: str) -> int:
    """AAAA-MM-JJ -> millisecondes epoch UTC, format attendu par `singleDate`.

    La conversion est ancrée à minuit UTC, comme les dates de version
    renvoyées par l'API (``dateDebut`` : ``…T00:00:00.000+0000``) : une même
    date rend ainsi la même version quel que soit le fuseau de la machine.
    """
    import datetime

    try:
        jour = datetime.datetime.strptime(iso_date, "%Y-%m-%d")
    except (ValueError, TypeError) as exc:
        raise LegifranceError(
            f"Date invalide : {iso_date!r} (format attendu AAAA-MM-JJ).",
            exit_code=2,
        ) from exc
    return int(jour.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)


def _fmt_date(value) -> str:
    """Les dates Légifrance sont souvent des timestamps ms epoch ou des chaînes."""
    if value in (None, "", 0):
        return "?"
    if isinstance(value, (int, float)):
        # epoch millisecondes -> AAAA-MM-JJ
        import datetime

        try:
            return datetime.datetime.utcfromtimestamp(value / 1000).strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            return str(value)
    return str(value)[:10]


def _fr_date(iso: str) -> str:
    """AAAA-MM-JJ -> JJ/MM/AAAA (laisse tel quel si format inattendu)."""
    parts = iso.split("-")
    if len(parts) == 3 and all(parts):
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return iso


def _strip_html(text: str) -> str:
    """Suppression minimale des balises HTML, sans dépendance externe."""
    if "<" not in text:
        return text
    import re

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return _unescape(text).strip()


def _unescape(text: str) -> str:
    import html

    return html.unescape(text)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="legifrance.py",
        description=(
            "Récupération fiable en source primaire via les API PISTE : "
            "Légifrance (textes) et Judilibre (jurisprudence)."
        ),
        epilog=(
            "Règle de provenance : ne jamais citer un article ou une décision "
            "sans récupération réussie (commandes 'article' et 'decision')."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp_ping = sub.add_parser("ping", help="Vérifier l'authentification PISTE.")
    sp_ping.set_defaults(func=cmd_ping)

    sp_art = sub.add_parser("article", help="Récupérer un article par LEGIARTI.")
    sp_art.add_argument("id", help="Identifiant LEGIARTI… de l'article.")
    sp_art.add_argument("--date", help="Version applicable à cette date (AAAA-MM-JJ).")
    sp_art.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_art.set_defaults(func=cmd_article)

    sp_search = sub.add_parser(
        "search",
        help="Rechercher un article par numéro.",
        description="Recherche par numéro d'article dans les codes (fond "
                    "CODE_DATE), à la version en vigueur à une date donnée. "
                    "La lettre de partie est facultative : « 2212-2 » teste "
                    "aussi L/R/D/A.",
    )
    sp_search.add_argument("numero", help="Numéro d'article, ex. '2212-2' ou 'L2212-2'.")
    sp_search.add_argument(
        "--code",
        help="Restreindre à un code : " + ", ".join(sorted(CODES)) + ".",
    )
    sp_search.add_argument(
        "--date",
        help="Version en vigueur à cette date (AAAA-MM-JJ ; défaut : aujourd'hui).",
    )
    sp_search.add_argument("--limit", type=int, default=10, help="Nb de résultats (défaut 10).")
    sp_search.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_search.set_defaults(func=cmd_search)

    # ----- Légifrance : jurisprudence administrative / constitutionnelle -- #
    for name, cfg in FONDS_JURIS.items():
        sp = sub.add_parser(name, help=f"Rechercher une décision — {cfg['label']}.")
        sp.add_argument("numero", help="N° de requête / décision.")
        sp.add_argument("--limit", type=int, default=10, help="Nb de résultats (défaut 10).")
        sp.add_argument("--json", action="store_true", help="Sortie JSON brute.")
        sp.set_defaults(func=cmd_jurisprudence)

    # ----- Judilibre : jurisprudence judiciaire --------------------------- #
    sp_juri = sub.add_parser(
        "juri",
        help="Rechercher de la jurisprudence (Judilibre).",
        description="Recherche plein texte dans les décisions de la Cour de "
                    "cassation, des cours d'appel et des tribunaux.",
    )
    sp_juri.add_argument("query", help="Termes de recherche.")
    sp_juri.add_argument(
        "--operator", choices=("and", "or", "exact"), default="and",
        help="Combinaison des termes (défaut : and).",
    )
    sp_juri.add_argument(
        "--field", action="append", choices=SEARCH_FIELDS,
        help="Restreindre la recherche à une zone du texte (répétable).",
    )
    sp_juri.add_argument(
        "--type", action="append", choices=DECISION_TYPES,
        help="Type de décision (répétable).",
    )
    sp_juri.add_argument(
        "--jurisdiction", action="append", choices=tuple(JURIDICTIONS),
        help="Juridiction : cc, ca, tj, tcom (répétable).",
    )
    sp_juri.add_argument("--chamber", action="append", help="Chambre (voir 'taxonomy chamber').")
    sp_juri.add_argument("--formation", action="append", help="Formation de jugement.")
    sp_juri.add_argument("--theme", action="append", help="Thème (matière).")
    sp_juri.add_argument(
        "--publication", action="append", choices=tuple(PUBLICATIONS),
        help="Niveau de publication : b (Bulletin), r, l, c.",
    )
    sp_juri.add_argument(
        "--solution", action="append", choices=SOLUTIONS,
        help="Sens de la décision (répétable).",
    )
    sp_juri.add_argument("--date-start", dest="date_start", help="Date minimale (AAAA-MM-JJ).")
    sp_juri.add_argument("--date-end", dest="date_end", help="Date maximale (AAAA-MM-JJ).")
    sp_juri.add_argument(
        "--sort", choices=("score", "scorepub", "date"), default="score",
        help="Tri des résultats (défaut : score).",
    )
    sp_juri.add_argument(
        "--order", choices=("asc", "desc"), default="desc",
        help="Sens du tri (défaut : desc).",
    )
    sp_juri.add_argument("--page", type=int, default=0, help="Page de résultats (défaut 0).")
    sp_juri.add_argument(
        "--limit", type=int, default=10,
        help="Nb de résultats par page, plafonné à 50 par l'API (défaut 10).",
    )
    sp_juri.add_argument(
        "--resolve-references", dest="resolve_references", action="store_true",
        help="Remplacer les codes internes par leurs libellés.",
    )
    sp_juri.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_juri.set_defaults(func=cmd_juri)

    sp_dec = sub.add_parser(
        "decision",
        help="Récupérer le texte intégral d'une décision (Judilibre).",
    )
    sp_dec.add_argument("id", help="Identifiant de décision renvoyé par 'juri'.")
    sp_dec.add_argument("--query", help="Termes à mettre en évidence dans le texte.")
    sp_dec.add_argument(
        "--operator", choices=("and", "or", "exact"), default="and",
        help="Combinaison des termes de --query.",
    )
    sp_dec.add_argument(
        "--zones", action="store_true",
        help="Afficher le texte découpé par zones (moyens, motivations, dispositif…).",
    )
    sp_dec.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_dec.set_defaults(func=cmd_decision)

    sp_tax = sub.add_parser(
        "taxonomy",
        help="Lister les valeurs acceptées par un filtre Judilibre.",
    )
    sp_tax.add_argument(
        "key",
        help="Clé de taxonomie : chamber, formation, theme, jurisdiction, "
             "publication, solution, type…",
    )
    sp_tax.add_argument(
        "--jurisdiction", choices=tuple(JURIDICTIONS),
        help="Contexte de juridiction pour les clés qui en dépendent.",
    )
    sp_tax.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_tax.set_defaults(func=cmd_taxonomy)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    try:
        return args.func(args)
    except LegifranceError as exc:
        # Le code 2 (identifiants absents) n'est pas une panne : c'est la
        # bascule normale vers la voie de repli web. Le signaler comme telle,
        # sans le registre d'erreur qui pousserait à interrompre l'analyse.
        prefix = "⚠️" if exc.exit_code == 2 else "❌"
        print(f"{prefix} {exc}", file=sys.stderr)
        # Usage local, par le titulaire des clés : le détail amont (URL,
        # fragment de réponse) aide à dépanner et n'a ici aucun destinataire
        # tiers. Le serveur MCP, lui, le réserve au journal.
        if getattr(exc, "detail", None):
            print(f"   Détail : {exc.detail}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
