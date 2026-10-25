# Skill juridique — déclinaison Gemini

Déclinaison **Gemini** (Google Antigravity et Gemini CLI) de la
méthodologie de recherche juridique en droit français portée par ce dépôt.

Cette déclinaison porte au standard **Agent Skills** l'ensemble des principes
invariants de la version **3.6.0** du noyau (`skill/`), en adaptant l'échelle
d'outils aux capacités de l'écosystème Gemini.

---

## Ce qui la distingue du noyau

Le noyau historique ([`skill/`](../skill)) est optimisé pour Claude Code et
l'utilisation directe des scripts PISTE (`skill/scripts/legifrance.py`).
La présente déclinaison **Gemini** adapte l'échelle de récupération aux
capacités et aux outils de l'écosystème Google / Gemini :

| Noyau (`skill/`) | Déclinaison Gemini (`gemini_skill/`) |
|---|---|
| Connecteur MCP Légifrance/Judilibre | **Identique (Priorité 1)** : support direct du serveur MCP du dépôt ([`mcp_server/`](../mcp_server)) sous Antigravity et Gemini CLI |
| `scripts/legifrance.py` (API PISTE) | Accessible via exécution de code Python ou via le package client [`gemini_agent/`](../gemini_agent) |
| Repli `web_search` / `web_fetch` | **Grounding Google Search / Outils Web** restreints strictement aux domaines institutionnels primaires (`site:legifrance.gouv.fr`, etc.) |
| Abstention (P7) | Règle absolue : refus de spéculer ou d'halluciner en l'absence de source vérifiée |

---

## Échelle d'outils à 4 voies

1. **Connecteur MCP dédié (Priorité 1)** :  
   Dans un environnement supportant le protocole MCP (Google Antigravity, Gemini CLI, Claude Code), le serveur du dépôt expose 12 outils officiels vérifiés dans [`mcp_server/server.py`](../mcp_server/server.py) :
   - `search(query)` : recherche générale (article, sinon jurisprudence judiciaire) ;
   - `fetch(id)` : lecture intégrale du document identifié (`LEGIARTI`, `LEGITEXT`, `CETATEXT`, `CONSTEXT`, `JUFITEXT`, décision Judilibre) ;
   - `search_articles(number, code, date, limit)` : article de code avec filtre de date ;
   - `get_article(id, date)` : lecture certifiée avec évaluation de `applicable_at_as_of_date` ;
   - `get_article_history(id, date)` : versions datées d'un article, textes modificateurs, version applicable ;
   - `get_section(id, text_id, date, cid)` et `get_text(id, date)` : section de code et texte consolidé ;
   - `search_case_law(query, jurisdiction, date_start, date_end, limit, sort)` et `get_decision(id)` : ordre judiciaire (Judilibre) ;
   - `search_admin_case_law(...)`, `search_constitutional_decisions(...)` et `search_financial_case_law(...)` : ordres administratif, constitutionnel et financier (Légifrance).

2. **Exécution de code Python / SDK `google-genai`** :  
   Sans serveur MCP actif, avec Python et des identifiants PISTE, les scripts du noyau (`skill/scripts/legifrance.py`) interrogent Légifrance et Judilibre. Le package compagnon [`gemini_agent/`](../gemini_agent) instancie un agent `google-genai` à température `0.0` avec le prompt système méthodologique ; ses fonctions-outils sont des squelettes non branchés, qui ne vérifient rien tant qu'ils ne sont pas connectés à une source.

3. **Recherche institutionnelle / Grounding (Repli Web)** :  
   À défaut, mobiliser le grounding Google Search en ciblant impérativement les domaines officiels listés dans [`references/sources-autorisees.md`](references/sources-autorisees.md). Ne jamais reconstituer un texte ou un numéro de pourvoi de mémoire.

4. **Abstention informée (P7)** :  
   Si la source primaire est inaccessible ou contradictoire, énoncer une réserve et s'abstenir de conclure.

---

## Ce qu'elle conserve

- Les **sept principes invariants P1 à P7**, dont la distinction entre authenticité de la source, rang de la norme et effet sur l'application (P3) ;
- La distinction entre **provenance officielle** et **applicabilité à la date évaluée** (`applicable_at_as_of_date`) ;
- La **procédure en 9 étapes** (cadrage, arbitrage des informations manquantes, récupération, version et fraîcheur, jurisprudence, triangulation, articulation, rédaction, auto-critique), avec l'historique d'article outillé et la lecture des états `VIGUEUR_DIFF`, `ABROGE_DIFF` et `_MORT_NE` ;
- La **voie spéciale DOC-AUDIT** ([`references/audit-documentaire.md`](references/audit-documentaire.md)) : registre, risque élevé vérifié à 100 %, exécution forcée d'office testée à part, montants répressifs distingués ;
- Les **modes d'erreur** à prévenir ([`references/modes-erreur.md`](references/modes-erreur.md)) ;
- Les **six modules métier activables** ([`references/modules.md`](references/modules.md)) ;
- Les balises d'exécution (`[complet]`, `[express]`, `[syllogisme]`, `[opérationnel]`, `[lookup]`) ;
- Les **profils métier** ([`profils/`](profils)), copiés à l'identique du noyau : copier le profil choisi en `profil.md`.

---

## Arborescence

```
gemini_skill/
├── SKILL.md                      ← instructions méthodologiques pour agents Gemini
├── references/
│   ├── sources-autorisees.md     ← hiérarchie des sources primaires et autorité (P3)
│   ├── modules.md                ← détail des six modules activables (PÉNAL, ACTE-ADMIN...)
│   ├── audit-documentaire.md     ← protocole DOC-AUDIT
│   └── modes-erreur.md           ← erreurs récurrentes à prévenir
└── README.md                     ← ce document
```

---

## Installation et utilisation

### Dans Google Antigravity

Placer le dossier dans le répertoire des skills Antigravity :
```powershell
Copy-Item -Recurse gemini_skill "$env:USERPROFILE\.gemini\antigravity\skills\recherche-juridique"
```

### Dans Gemini CLI

Gemini CLI découvre les skills par scan de répertoires dédiés :
```powershell
# Portée utilisateur
Copy-Item -Recurse gemini_skill "$env:USERPROFILE\.gemini\skills\recherche-juridique"

# Ou portée projet (répertoire de travail)
Copy-Item -Recurse gemini_skill ".\.gemini\skills\recherche-juridique"
```

### Dans Google AI Studio (Web)

Google AI Studio est une interface web de test qui ne prend pas en charge
nativement l'exécution de serveurs MCP locaux ni la découverte de dossiers
de skills. Pour y appliquer la méthodologie :
1. Copier les instructions de [`SKILL.md`](SKILL.md) dans les **System Instructions**
   du modèle (ex. `gemini-2.5-pro`) ;
2. Activer l'outil **Grounding with Google Search** pour permettre la vérification
   en source primaire.

### Articulation avec `gemini_agent/`

Pour une utilisation programmatique via l'API Google GenAI (`google-genai`), utiliser directement :
```python
from gemini_agent.legal_agent_config import LegalAgentConfig, build_chat, build_client

client = build_client()
chat = build_chat(client, LegalAgentConfig())
response = chat.send_message("Quelle est la définition légale du tapage nocturne ?")
print(response.text)
```

---

## Versionnement

Le frontmatter porte `version: 3.6.0-gemini` et `base_version: 3.6.0`. Le numéro suit fidèlement le noyau de méthodologie juridique du dépôt.
