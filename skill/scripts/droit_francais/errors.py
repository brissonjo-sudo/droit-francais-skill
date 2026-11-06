"""Erreurs communes aux clients Légifrance et Judilibre."""

from __future__ import annotations


class LegifranceError(Exception):
    """Erreur métier avec code de sortie et éventuel statut HTTP.

    Le nom historique est conservé car le CLI et sa documentation l'utilisent
    déjà. L'exception couvre aussi Judilibre.
    """

    def __init__(
        self,
        message: str,
        exit_code: int,
        http_status: int | None = None,
        *,
        detail: str | None = None,
        upstream: dict | None = None,
    ):
        super().__init__(message)
        self.exit_code = exit_code
        self.http_status = http_status
        #: Détail technique — URL amont complète, fragment de corps de réponse.
        #: Réservé au journal du serveur et à la sortie d'erreur du CLI ; ne
        #: figure jamais dans le message rendu à un client MCP.
        self.detail = detail
        #: Diagnostic structuré d'un refus HTTP amont (statut, hôte, chemin sans
        #: paramètres, ``Retry-After``, en-têtes de limitation, tentatives,
        #: attente cumulée, extrait de corps). Aucune donnée personnelle :
        #: journalisable tel quel, contrairement à ``detail``.
        self.upstream = upstream
