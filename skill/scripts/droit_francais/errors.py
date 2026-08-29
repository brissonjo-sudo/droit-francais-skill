"""Erreurs communes aux clients Légifrance et Judilibre."""

from __future__ import annotations


class LegifranceError(Exception):
    """Erreur métier avec code de sortie et éventuel statut HTTP.

    Le nom historique est conservé car le CLI et sa documentation l'utilisent
    déjà. L'exception couvre aussi Judilibre.
    """

    def __init__(self, message: str, exit_code: int, http_status: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.http_status = http_status
