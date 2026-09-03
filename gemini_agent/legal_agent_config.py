"""Configuration de l'agent Gemini d'analyse et de recherche juridique.

Point d'entrée unique pour instancier l'agent : modèle, température figée à
0.0 (déterminisme requis pour un usage juridique), system prompt et
déclaration des outils de tool calling obligatoire. Utilise le SDK unifié
`google-genai` (package PyPI `google-genai`), qui génère automatiquement les
déclarations de fonction à partir des signatures typées de `tools.py`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from .tools import search_case_law, search_legal_database

MODEL_NAME = "gemini-2.5-pro"

#: Température figée à 0.0 : sur un usage juridique, la reproductibilité et
#: l'absence de dérive créative priment sur la diversité des formulations.
TEMPERATURE = 0.0

SYSTEM_PROMPT = """\
Tu es un agent d'analyse et de recherche juridique de haut niveau. Ton objectif est de fournir des réponses rigoureuses, sourcées et exploitables pour toute problématique légale, quelle que soit la juridiction ou la branche du droit concernée.

Règles impératives de traitement :
1. RECOURS AUX OUTILS (TOOL CALLING) OBLIGATOIRE : Tu ne dois jamais répondre uniquement à partir de tes données d'entraînement. Utilise systématiquement tes outils de recherche pour vérifier le droit positif (textes en vigueur) avant de formuler ta réponse.
2. RIGUEUR DES SOURCES : Ne génère aucune hallucination. Cite systématiquement le texte exact, le numéro de l'article, et la référence exacte pour la jurisprudence.
3. HIÉRARCHIE DES NORMES : Vérifie qu'un texte n'est pas neutralisé par une norme supérieure.
4. NEUTRALITÉ : Ton ton doit être neutre, objectif et analytique.

Méthodologie d'analyse (Format de sortie Markdown obligatoire) :
- ÉTAPE 1 : ## 📌 Qualification juridique des faits
- ÉTAPE 2 : ## ⚖️ Textes applicables (Liste exhaustive des normes en vigueur)
- ÉTAPE 3 : ## 🏛️ Recherche de jurisprudence
- ÉTAPE 4 : ## 🔍 Syllogisme juridique (Majeure, Mineure, Conclusion)
- ÉTAPE 5 : ## ⚠️ Limites, exceptions et risques
"""


@dataclass(frozen=True)
class LegalAgentConfig:
    """Paramètres immuables de l'agent : un changement crée une nouvelle config."""

    model: str = MODEL_NAME
    temperature: float = TEMPERATURE
    system_prompt: str = SYSTEM_PROMPT
    tools: tuple = field(default=(search_legal_database, search_case_law))

    def generation_config(self) -> types.GenerateContentConfig:
        """Construit la config `google-genai` prête pour un appel ou un chat."""
        return types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=self.system_prompt,
            tools=list(self.tools),
        )


def build_client(api_key: str | None = None) -> genai.Client:
    """Crée le client Gemini. `api_key` retombe sur `GEMINI_API_KEY`/ADC si omis."""
    return genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))


def build_chat(
    client: genai.Client, config: LegalAgentConfig | None = None
) -> genai.chats.Chat:
    """Ouvre une session de chat avec l'agent juridique configuré."""
    cfg = config or LegalAgentConfig()
    return client.chats.create(model=cfg.model, config=cfg.generation_config())
