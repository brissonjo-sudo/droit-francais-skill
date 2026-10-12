# S28 — diagnostic d'intervalle, sans modification du droit ou des refus

L'instrumentation conserve la condition `lower >= upper`, les limites de
5 000 nœuds, 2 Mo, 67 appels et 90 secondes. Elle ne change ni la sélection
des versions, ni les identités, ni la lecture des liens historiques.

Le journal serveur existant reçoit, lors d'un intervalle inversé ou égal,
un détail `structured_consultation_refusal` contenant le dépassement du parent
et le détail `structure_interval`. Celui-ci comporte un rôle fixe, un chemin
de clés connues et indices bornés, éventuellement un identifiant public validé,
les types des bornes, leurs valeurs finies ou ISO strictes et dates normalisées.
Les valeurs numériques textuelles non ISO sont omises, sans changer leur
traitement par le lecteur. Les chaînes libres et payloads ne sont pas copiés.

Le message public reste inchangé ; les détails ne sont pas rendus au client
MCP. Un détail absent ou non conforme conserve le diagnostic parent initial.
Les bornes illisibles restent refusées, sans nouvelle qualification.

Cette instrumentation est un outil de diagnostic technique. Elle ne prouve
pas S28 positif et ne valide aucune campagne, T04 ou release du skill DPM.
