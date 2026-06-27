#!/usr/bin/env python3
"""legifrance.py — récupération fiable en source primaire via l'API Légifrance (PISTE).

Objet
-----
Matérialise le « Palier 3 » du skill *recherche-juridique*. Convertit
l'exigence P1 (primarité / lecture documentée) et la **règle de provenance**
en appel d'outil déterministe : tout identifiant ``LEGIARTI``, toute date de
version en vigueur et tout statut (en vigueur / modifié / abrogé) provient
d'une réponse officielle de l'API Légifrance, et non de la mémoire du modèle.

Authentification
----------------
OAuth2 *client_credentials* sur PISTE. Le script lit ses identifiants dans
l'environnement (jamais en clair dans le dépôt) :

    LEGIFRANCE_CLIENT_ID         (obligatoire)
    LEGIFRANCE_CLIENT_SECRET     (obligatoire)
    LEGIFRANCE_ENV               "prod" (défaut) | "sandbox"   (optionnel)

Obtention des identifiants : créer un compte sur https://piste.gouv.fr,
y déclarer une application abonnée à l'API « Légifrance », récupérer le
*client id* et le *client secret*. Voir scripts/README.md.

Dépendances
-----------
Aucune : bibliothèque standard Python 3.8+ uniquement (urllib, json, argparse).

Usage
-----
    python legifrance.py ping
    python legifrance.py article LEGIARTI000006419288
    python legifrance.py article --date 2024-01-01 LEGIARTI000006419288
    python legifrance.py search "2212-2" --code CGCT
    python legifrance.py article --json LEGIARTI000006419288   # sortie brute JSON

Codes de sortie
---------------
    0  succès
    2  identifiants d'environnement manquants / mauvais usage
    3  échec d'authentification PISTE
    4  échec de la requête API (HTTP non-2xx, contenu illisible)
    5  ressource introuvable (article inexistant)

Le code 4/5 est, côté skill, un **déclencheur d'abstention** (§7) : pas de
citation sans récupération réussie.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------- #
# Endpoints PISTE / Légifrance
# --------------------------------------------------------------------------- #
ENVS = {
    "prod": {
        "token": "https://oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app",
    },
    "sandbox": {
        "token": "https://sandbox-oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app",
    },
}

# Identifiants LEGITEXT des codes fréquents (miroir de gabarits-requetes.md).
CODE_IDS = {
    "CGCT": "LEGITEXT000006070633",
    "CP": "LEGITEXT000006070719",
    "CODE_PENAL": "LEGITEXT000006070719",
    "CPP": "LEGITEXT000006071154",
    "CSI": "LEGITEXT000025503132",
    "CDR": "LEGITEXT000006074228",
    "CODE_ROUTE": "LEGITEXT000006074228",
    "CRPA": "LEGITEXT000031367321",
    "GFP": "LEGITEXT000044416551",
    "CENV": "LEGITEXT000006074220",
    "CSP": "LEGITEXT000006072665",
    "CURBA": "LEGITEXT000006074075",
}

TIMEOUT = 30


class LegifranceError(Exception):
    """Erreur métier avec code de sortie associé."""

    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code


# --------------------------------------------------------------------------- #
# Couche HTTP (stdlib)
# --------------------------------------------------------------------------- #
def _http_post(url: str, data: bytes, headers: dict) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:  # 4xx / 5xx
        body = exc.read().decode("utf-8", "replace")[:500]
        raise LegifranceError(
            f"HTTP {exc.code} sur {url}\n{body}", exit_code=4
        ) from exc
    except urllib.error.URLError as exc:
        raise LegifranceError(
            f"Échec réseau vers {url} : {exc.reason}", exit_code=4
        ) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LegifranceError(
            f"Réponse non-JSON de {url} : {raw[:300]}", exit_code=4
        ) from exc


def _env() -> dict:
    name = os.environ.get("LEGIFRANCE_ENV", "prod").lower()
    if name not in ENVS:
        raise LegifranceError(
            f"LEGIFRANCE_ENV invalide : {name!r} (attendu 'prod' ou 'sandbox')",
            exit_code=2,
        )
    return ENVS[name]


def get_token() -> str:
    """Récupère un jeton OAuth2 client_credentials (scope openid)."""
    client_id = os.environ.get("LEGIFRANCE_CLIENT_ID")
    client_secret = os.environ.get("LEGIFRANCE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise LegifranceError(
            "Identifiants manquants : définir LEGIFRANCE_CLIENT_ID et "
            "LEGIFRANCE_CLIENT_SECRET (voir scripts/README.md).",
            exit_code=2,
        )
    payload = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        }
    ).encode("utf-8")
    try:
        data = _http_post(
            _env()["token"],
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
    except LegifranceError as exc:
        raise LegifranceError(
            f"Authentification PISTE échouée : {exc}", exit_code=3
        ) from exc
    token = data.get("access_token")
    if not token:
        raise LegifranceError(
            f"Réponse OAuth sans access_token : {data}", exit_code=3
        )
    return token


def api_call(path: str, body: dict, token: str) -> dict:
    url = _env()["api"] + path
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return _http_post(url, json.dumps(body).encode("utf-8"), headers)


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


def cmd_search(args) -> int:
    """Recherche un article par numéro, optionnellement filtré sur un code."""
    token = get_token()
    code_id = None
    if args.code:
        key = args.code.upper().replace(" ", "_")
        code_id = CODE_IDS.get(key)
        if not code_id:
            raise LegifranceError(
                f"Code inconnu : {args.code!r}. Codes connus : "
                f"{', '.join(sorted(CODE_IDS))}.",
                exit_code=2,
            )

    # Payload de recherche Légifrance (fond CODE_DATE, critère NUM_ARTICLE).
    champ = {
        "typeChamp": "NUM_ARTICLE",
        "criteres": [
            {"typeRecherche": "EXACTE", "valeur": args.numero, "operateur": "ET"}
        ],
        "operateur": "ET",
    }
    recherche: dict = {
        "champs": [champ],
        "pageNumber": 1,
        "pageSize": args.limit,
        "operateur": "ET",
        "sort": "PERTINENCE",
        "typePagination": "ARTICLE",
    }
    if code_id:
        recherche["filtres"] = [{"facette": "TEXT_LEGAL_STATUS", "valeurs": ["VIGUEUR"]}]
    body = {"recherche": recherche, "fond": "CODE_DATE"}
    if code_id:
        body["recherche"]["champs"][0]["criteres"][0]["valeur"] = args.numero

    data = api_call("/search", body, token)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    results = data.get("results") or []
    if not results:
        print(
            f"Aucun résultat pour « {args.numero} »"
            + (f" dans {args.code}" if args.code else "")
            + ". Affiner la requête ou utiliser l'accès direct par LEGIARTI.",
            file=sys.stderr,
        )
        return 5
    print(f"{len(results)} résultat(s) — utiliser l'identifiant avec la commande 'article' :")
    for r in results[: args.limit]:
        sections = r.get("sections") or []
        titles = r.get("titles") or []
        ref = (titles[0].get("id") if titles else None) or r.get("id") or "?"
        title = (titles[0].get("title") if titles else None) or r.get("title") or ""
        # Les ids d'articles sont souvent dans extracts/sections selon le fond.
        art_id = _first_legiarti(r)
        print(f"  • {art_id or ref}  {title}".rstrip())
    print(
        "\nNote : selon le fond interrogé, l'identifiant LEGIARTI exact peut "
        "devoir être confirmé via 'article <LEGIARTI>'. Ne jamais citer un "
        "identifiant non confirmé (règle de provenance)."
    )
    return 0


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def _first_legiarti(obj) -> str | None:
    """Cherche récursivement un identifiant LEGIARTI dans une structure JSON."""
    if isinstance(obj, str):
        return obj if obj.startswith("LEGIARTI") else None
    if isinstance(obj, dict):
        for v in obj.values():
            found = _first_legiarti(v)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = _first_legiarti(v)
            if found:
                return found
    return None


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
        description="Récupération fiable en source primaire via l'API Légifrance (PISTE).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp_ping = sub.add_parser("ping", help="Vérifier l'authentification PISTE.")
    sp_ping.set_defaults(func=cmd_ping)

    sp_art = sub.add_parser("article", help="Récupérer un article par LEGIARTI.")
    sp_art.add_argument("id", help="Identifiant LEGIARTI… de l'article.")
    sp_art.add_argument("--date", help="Version applicable à cette date (AAAA-MM-JJ).")
    sp_art.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_art.set_defaults(func=cmd_article)

    sp_search = sub.add_parser("search", help="Rechercher un article par numéro.")
    sp_search.add_argument("numero", help="Numéro d'article, ex. '2212-2'.")
    sp_search.add_argument("--code", help="Filtrer sur un code (CGCT, CP, CPP, CSI, CDR…).")
    sp_search.add_argument("--limit", type=int, default=10, help="Nb de résultats (défaut 10).")
    sp_search.add_argument("--json", action="store_true", help="Sortie JSON brute.")
    sp_search.set_defaults(func=cmd_search)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LegifranceError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
