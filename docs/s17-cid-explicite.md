# S17 : CID de localisation explicite — 6 octobre 2026

La PR106 a établi une voie ID→CID par sommaire officiel, mais la sonde
originale après livraison a refusé le sommaire réel supérieur à 2 Mo.
Ce refus est conservé. Un diagnostic séparé par le CID observé dans le lien
officiel a confirmé l'ID de version original et son parent daté ; il ne
qualifiait pas à lui seul l'appel original.

Évolution autorisée : `get_section(id, text_id, date=None, cid=None)`.
Sans `cid`, le contrat existant est conservé. Avec `cid`, il sert seulement
de localisateur pour `CodeConsultRequest.sctCid` et `SectionCidRequest.cid`.
**La version active retournée doit être exactement `id`, pas seulement ce CID.**
Le parent, les bornes de date et la complétude sont contrôlés à la source.
Un CID mal lié, une autre version applicable ou un parent différent sont
refusés ; aucune nouvelle résolution automatique ni repli au sommaire
n'est autorisé dans cette voie explicite. Aucun identifiant S17 codé en dur.

PISTE Swagger public Légifrance 2.4.2 relu : `/consult/getSectionByCid`
requiert `SectionCidRequest.cid` ; `/consult/code` accepte
`CodeConsultRequest.sctCid`. Context7 consulté pour la documentation officielle
et le SDK MCP ; paramètre Python nullable à valeur par défaut, donc facultatif
dans le schéma généré. Toujours huit outils en lecture, aucun nouvel outil.

Après un refus de volumétrie du parent, seul son ID/version/titre est gardé
et la structure est relue, bornée, via ce CID. Le corps parent refusé n'est
ni normalisé, ni tronqué, ni réutilisé. Les articles sont relus suivant les
liens officiels, avec contrôle du contexte parent daté et de la section.
Plafonds 2 Mo, 5 000 nœuds, profondeur 32, 67 consultations, 90 secondes et
cadence 1,1 seconde inchangés, pour S01 comme pour S17.

`requested_id` conserve l'ID demandé ; `requested_cid` conserve le localisateur.
`section_identity_resolution` enregistre les deux, parent/version/date,
endpoint et liaison `explicit_locator_and_exact_dated_version_id`. Cette
provenance ne certifie pas la provenance de l'entrée fournie par l'appelant :
celui-ci doit conserver sa preuve officielle séparée. Le serveur confirme
la correspondance actuelle dans la réponse native, pas depuis un cache local.

Les tests couvrent les deux voies, identité exacte, ambiguïté, parents,
dates, limites, absence de sommaire et schéma MCP facultatif. Une sonde neuve
sous nouveau gel doit vérifier l'appel original avec ce transport explicite.
Pas de modification du corpus DPM, de requalification de S01, de campagne
comportementale ou de qualification juridique/humaine par ces seuls tests.
