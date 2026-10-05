# S10 — récupération structurée après refus de réponse CODE trop volumineuse

Correctif du 5 octobre 2026, préparé depuis le merge S01 `c13bd05`.

Le préflight DPM v4 a confirmé S01, puis refusé la section S10
`LEGISCTA000028286049`, parent `LEGITEXT000025503132`, au 2026-10-05 :
réponse CODE d'au moins 2 000 011 octets pour un plafond de 2 000 000.
Aucun contenu tronqué retourné. L'ancre exigée reste `LEGIARTI000033899705`.

Le déclenchement de la voie officielle structurée est étendu aux refus
`consultation_limit`, périmètre `response`, métrique `bytes_json`, en plus
de `nodes`. Les autres refus sont propagés : profondeur, incomplétude,
structure sélectionnée ou cumul ne deviennent pas des invitations à relire.
Le corps parent refusé n'est ni rendu ni tronqué ; seuls son identité et son
titre contrôlés sont retenus avant lectures des liens officiels datés.

Les plafonds de contenu (2 Mo, 5 000 nœuds, profondeur 32), les budgets
structurés (67 consultations, 90 secondes), les contrôles de parent/version,
d'identité, de dates et de complétude restent inchangés. Aucun nouvel endpoint,
outil, secret, dépendance, pagination inventée ou source alternative.

Les tests ajoutés sont synthétiques et hors réseau. Ils ne prouvent pas que
S10 tient dans ces budgets : seule une nouvelle sonde native post-déploiement,
préenregistrée avec la cible originale et le vérificateur DPM inchangé,
permettra de qualifier sa récupération. Les refus antérieurs et S01 restent
conservés. Aucun nouveau verdict métier ni release DPM qualifiée.

Le test historique interdisant de normaliser un petit sous-arbre du parent
refusé garde cette interdiction. Il attend désormais une consultation
indépendante de structure, elle aussi refusée dans sa fixture volumineuse :
aucun appel d'article et aucun résultat partiel. Ce changement de trace
attendue ne relaxe pas le plafond ni la complétude.
