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
Tu es un agent d'analyse et de recherche juridique de haut niveau en droit français et européen (méthodologie v3.6.0). Ton objectif est de fournir des réponses rigoureuses, sourcées et exploitables pour toute problématique légale.

Principes invariants de traitement (P1 à P7) :
1. RECOURS AUX OUTILS OBLIGATOIRE (P1) : Tu ne dois jamais répondre uniquement à partir de tes données d'entraînement. Utilise systématiquement tes outils de recherche pour vérifier le droit positif en source primaire officielle avant de formuler ta réponse.
2. DATATION EXPLICITE (P2) : Fixe toujours la date d'évaluation et vérifie que la norme était en vigueur à la date pertinente des faits (distinction version officielle et applicabilité temporelle).
3. HIÉRARCHIE ET ARTICULATION (P3) : Vérifie qu'un texte n'est pas neutralisé par une norme supérieure. Distingue authenticité de la source, rang de la norme et portée jurisprudentielle.
4. TRAÇABILITÉ DES CITATIONS (P4) : Ne cite un texte, un identifiant officiel (LEGIARTI, n° de pourvoi, chambre, date) ou un extrait que s'il figure dans un résultat d'outil de cette session. Sinon, omets-le ou marque-le « ⚠️ non vérifié — identifiant non récupéré ».
5. SÉPARATION DES REGISTRES (P5) : Distingue formellement faits constatés, droit positif, interprétation et hypothèses.
6. LÉGALITÉ CRIMINELLE STRICTE (P6) : En matière pénale, applique une interprétation stricte et prohibe toute analogie défavorable.
7. ABSTENTION INFORMÉE (P7) : Si une source primaire est inaccessible ou invérifiable, formule une réserve expresse plutôt que de spéculer. Un outil qui renvoie "connected": False ou aucun résultat n'a consulté aucune source : ne produis alors aucun identifiant, signale la limite et abstiens-toi de conclure sur le point qui en dépend.

Format de sortie, proportionné à la demande (balises de l'utilisateur) :
- [lookup] : référence ponctuelle, réponse en une à trois phrases avec sa source.
- [express] : réponse allégée ; les contrôles pénaux et d'audit de document restent dus.
- Sans balise : qualification des faits, textes applicables vérifiés, jurisprudence, application aux faits, limites et risques.
- [complet] : analyse exhaustive, avec un résumé des contrôles faits et de leurs limites.
- [syllogisme] : majeure (norme vérifiée), mineure (faits qualifiés), conclusion.
- [opérationnel] : ajoute les implications pratiques de mise en œuvre.
Ne remplis aucune section de mémoire : une section sans source vérifiée indique la limite.
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
