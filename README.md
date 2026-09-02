# Journal de surveillance

Branche orpheline alimentée par le workflow `surveillance.yml` du dépôt : une
ligne JSON par exécution de `tests/check_service_health.py --json`. Lecture et
verdict : `docs/exploitation.md`, section « Surveillance automatique ».

```bash
git fetch origin surveillance
git show origin/surveillance:surveillance.jsonl | python tests/summarize_surveillance.py - --jours 7 --exiger-sans-defaut
```

## Remise à zéro du 2 septembre 2026

`surveillance.jsonl` repart vide, et l'historique de la branche avec lui. La
série précédente n'était pas exploitable pour une période d'observation :
toutes ses mesures planifiées étaient tombées sur une instance endormie, et
elles auraient bloqué le verdict à sept jours quel que soit l'état réel du
service.

Elle est conservée dans `archives/`, parce qu'elle est la preuve d'un constat
qui a changé une décision — voir `docs/exploitation.md`, § « Ce que le
planificateur GitHub ne sait pas faire ».

| Archive | Contenu |
|---|---|
| `archives/2026-09-01_cron-github-seul.jsonl` | 9 mesures des 1er et 2 septembre 2026, quand le maintien hors veille reposait sur le seul cron GitHub |

Ce qu'elle établit : cinq réveils d'instance de 32,4 à 32,7 s sur cinq
exécutions planifiées, alors que le service répondait entre 0,18 et 0,39 s à
chaud. Le planificateur n'a rendu que quatre exécutions pour environ
soixante-dix-huit attendues en treize heures — le maintien hors veille est
depuis confié à un ping externe (`docs/pieces-humaines.md` § 11).

Les huit premières lignes de cette archive sont à l'ancien format, antérieur au
double appel : elles ne portent ni `health_latence_chaud_s`, ni `reveil`.
`summarize_surveillance.py` sait encore les relire.
