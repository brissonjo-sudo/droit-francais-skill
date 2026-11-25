"""Saisie des clés PISTE d'un compte : deux outils MCP et la page ``/compte``.

Le secret ne transite jamais par la conversation : l'outil
``configurer_cles_piste`` (appelé sous OAuth) renvoie un lien signé, valable
10 minutes et à usage unique, vers un formulaire servi par ce serveur. Les
clés saisies sont vérifiées auprès de PISTE avant d'être chiffrées et
enregistrées. La page ne réaffiche jamais une valeur saisie.
"""

from __future__ import annotations

import html
import re
import urllib.parse
from typing import Any, Callable

import anyio
from mcp.types import ToolAnnotations

from droit_francais.errors import LegifranceError
from droit_francais.legifrance import caller_credentials, get_token
from mcp_server.credential_store import LINK_TTL_SECONDS, CredentialStore, CredentialStoreError

MAX_FORM_BYTES = 4096
_VALUE = re.compile(r"[A-Za-z0-9._~+/=-]{8,256}")
_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'none'"
    ),
}
_PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clés PISTE</title><style>body{{font-family:system-ui,sans-serif;max-width:32rem;
margin:2rem auto;padding:0 1rem;line-height:1.5}}label{{display:block;margin-top:1rem}}
input{{width:100%;padding:.5rem;font-size:1rem;box-sizing:border-box}}
button{{margin-top:1.5rem;padding:.6rem 1.2rem;font-size:1rem}}</style></head>
<body><h1>Clés PISTE</h1>{body}</body></html>"""
_FORM = """<p>Saisissez l'identifiant et le secret de <strong>votre</strong> application
PISTE (piste.gouv.fr). Ils seront vérifiés auprès de PISTE, puis chiffrés et
rattachés à votre compte.</p>
<form method="post" action="/compte" autocomplete="off">
<p>Compte : <code>{hint}</code>. Si ce n'est pas le vôtre, n'utilisez pas ce lien.</p>
<input type="hidden" name="t" value="{token}">
<label for="id">Identifiant (client_id)</label>
<input id="id" name="client_id" required minlength="8" maxlength="256">
<label for="secret">Secret (client_secret)</label>
<input id="secret" name="client_secret" type="password" required minlength="8" maxlength="256">
<button type="submit">Enregistrer</button></form>"""


def _page(message: str, status: int = 200) -> Any:
    from starlette.responses import HTMLResponse

    return HTMLResponse(_PAGE.format(body=message), status_code=status, headers=_HEADERS)


def _expired() -> Any:
    return _page("<p>Lien expiré ou déjà utilisé. Redemandez un lien avec l'outil "
                 "<code>configurer_cles_piste</code>.</p>", 400)


def account_hint(subject: str) -> str:
    """Indice lisible du compte, sans révéler le sujet complet."""
    provider, _, rest = subject.partition("|")
    return f"{provider}|…{rest[-4:]}" if rest else f"…{subject[-4:]}"


def _check_with_piste(client_id: str, client_secret: str) -> None:
    with caller_credentials(client_id, client_secret):
        get_token(force_refresh=True)


def register(
    server: Any,
    store: CredentialStore,
    public_url: str,
    current_principal: Callable[[], str],
) -> None:
    """Déclare les deux outils et la page ``/compte`` sur ``server``."""
    from mcp.server.mcpserver.exceptions import ToolError
    from starlette.requests import Request

    @server.tool(
        name="configurer_cles_piste",
        title="Enregistrer mes clés PISTE",
        description=(
            "Renvoie un lien personnel, valable 10 minutes et à usage unique, vers "
            "la page où l'utilisateur saisit l'identifiant et le secret de SA "
            "propre application PISTE. Ne jamais demander ces valeurs dans la "
            "conversation : transmettre le lien à l'utilisateur."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                                    idempotentHint=False, openWorldHint=False),
    )
    def configurer_cles_piste() -> dict[str, Any]:
        subject = current_principal()
        if subject == "anonyme":
            raise ToolError("Connexion requise.")
        token = store.issue_link_token(subject)
        return {
            "lien": f"{public_url}/compte?t={token}",
            "compte": account_hint(subject),
            "expire_dans_minutes": LINK_TTL_SECONDS // 60,
            "consigne": ("Ouvrir ce lien dans un navigateur et y saisir les clés PISTE. "
                         "Lien personnel : ne pas le transmettre à un tiers."),
        }

    @server.tool(
        name="oublier_cles_piste",
        title="Supprimer mes clés PISTE",
        description="Supprime définitivement les clés PISTE enregistrées pour ce compte.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                    idempotentHint=True, openWorldHint=False),
    )
    def oublier_cles_piste() -> dict[str, Any]:
        subject = current_principal()
        if subject == "anonyme":
            raise ToolError("Connexion requise.")
        try:
            store.delete(subject)
        except CredentialStoreError as exc:
            raise ToolError(f"Suppression impossible : {exc}") from None
        return {"supprime": True}

    @server.custom_route("/compte", methods=["GET"], include_in_schema=False)
    async def compte_form(request: Request) -> Any:
        token = request.query_params.get("t", "")
        subject = store.read_link_token(token, consume=False)
        if subject is None:
            return _expired()
        return _page(_FORM.format(token=html.escape(token, quote=True),
                                  hint=html.escape(account_hint(subject))))

    @server.custom_route("/compte", methods=["POST"], include_in_schema=False)
    async def compte_submit(request: Request) -> Any:
        raw = await request.body()
        if len(raw) > MAX_FORM_BYTES:
            return _page("<p>Formulaire trop volumineux.</p>", 413)
        form = urllib.parse.parse_qs(raw.decode("utf-8", "replace"))
        token = (form.get("t") or [""])[0]
        client_id = (form.get("client_id") or [""])[0].strip()
        client_secret = (form.get("client_secret") or [""])[0].strip()
        if store.read_link_token(token, consume=False) is None:
            return _expired()
        if not (_VALUE.fullmatch(client_id) and _VALUE.fullmatch(client_secret)):
            return _page("<p>Identifiant ou secret mal formé (8 à 256 caractères, sans "
                         "espace). Revenez en arrière pour corriger.</p>", 400)
        try:
            await anyio.to_thread.run_sync(_check_with_piste, client_id, client_secret)
        except LegifranceError:
            return _page("<p>PISTE a refusé ces clés. Vérifiez-les sur piste.gouv.fr "
                         "(application abonnée à Légifrance et Judilibre), puis revenez "
                         "en arrière pour corriger.</p>", 400)
        subject = store.read_link_token(token, consume=True)
        if subject is None:
            return _expired()
        try:
            await anyio.to_thread.run_sync(store.save, subject, client_id, client_secret)
        except CredentialStoreError:
            return _page("<p>Enregistrement impossible pour le moment : réessayez plus "
                         "tard avec un nouveau lien.</p>", 503)
        return _page("<p><strong>Clés enregistrées.</strong> Vous pouvez fermer cette page "
                     "et utiliser l'outil depuis tous vos appareils connectés à ce compte.</p>")
