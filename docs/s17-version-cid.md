# S17 : ID de version et CID de section — 6 octobre 2026

Le diagnostic natif isolé retrouve l'ID `LEGISCTA000025508386` sous le CID
`LEGISCTA000025505127` du parent `LEGITEXT000025503132`, à la date demandée
du 05/10/2026. La cible originale, son identifiant et les refus historiques
restent conservés. Ce diagnostic par le lien de sommaire ne qualifie pas
l'appel original ; cet appel devra être rejoué après livraison.

Context7 (Légifrance) consulté, puis Swagger public PISTE Légifrance 2.4.2
relu directement le 06/10. Le contrat recommande `/consult/legi/tableMatieres`
avec `LegiSommaireConsultRequest(textId, date, nature=CODE)` ; la variante
`/consult/code/tableMatieres` est dépréciée. Réponse `ConsultTextResponse`,
sections `ConsultSection.id/cid/dateDebut/dateFin`. Le contenu de section
est toujours relu via `/consult/getSectionByCid`, `SectionCidRequest.cid`,
puis les articles via leurs liens officiels. Aucun nouvel outil MCP.

Une consultation CODE normale reste inchangée. Après refus initial de
volumétrie et échec de lookup CID de la racine seulement, un sommaire officiel
borné et daté peut établir un CID distinct : ID de version exact, occurrence
unique, chaîne d'ancêtres applicable, parent identique à la première réponse.
La section est relue par ce CID et **son ID de version doit encore être
exactement l'ID original demandé**. Une version historique/non applicable,
un CID ambigu, un parent différent, un enfant absent ou une limite dépassée
reste un refus. Pas de résolution de lien enfant ni deuxième résolution.

Le sommaire n'est jamais un corps de section complet et son texte n'est pas
servi. Ses octets/nœuds et ses requêtes entrent dans les budgets cumulés
existants. Plafonds 2 Mo / 5 000 nœuds / profondeur 32, 67 consultations,
90 secondes et cadence 1,1 s inchangés, y compris pour S01.

La provenance `section_identity_resolution` conserve ID demandé, CID résolu,
parent/version/date et endpoint. L'inventaire distingue sections, articles
et lectures d'identité ; `requested_id` n'est jamais remplacé par le CID.
Le statut absent reste `UNKNOWN`, pas une affirmation de vigueur.

Tests synthétiques : succès ID/CID, exactitude/ambiguïté/date/ancêtres,
parents, limites du sommaire, autre version active, seconde résolution,
budgets et non-régression des demandes par CID. Qualification métier,
stabilité de S01 et préflight complet restent des gates distincts.
