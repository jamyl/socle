# Template — Audit adversarial

> Usage : audit critique du produit, par quelqu'un qui n'a aucun intérêt à ce
> qu'il soit bon. Deux fenêtres d'emploi :
> (1) **pré-build**, une fois, avant d'écrire du code → `docs/product/audit-pre-build.md` ;
> (2) **pré-release**, quand le produit existe réellement.
>
> 🔧 Remplace les `[…]` par le contexte du projet avant de lancer.

## Contexte à injecter dans l'audit

- **Produit** : `[une phrase — ce qu'il fait, pour qui, et ce qu'il ne fait pas]`
- **Cibles et canaux** : `[personas · plateformes de distribution · langues et sens d'écriture]`
- **Contraintes légales ou sectorielles** : `[textes applicables, ou « aucune »]`

## Sources de vérité à lire d'abord

`docs/product/vision.md`, les epics `docs/backlog/` pertinents,
`docs/engineering/stack.md` et `testing-strategy.md`.

## Garde-fous — sans eux, l'audit produit du bruit

- **Chaque finding cite un document ou une story précis** (ex. « E07 US-702 »).
  Une généralité qu'on ne peut pas rattacher n'est pas actionnable.
- **Ne pas halluciner une règle** de plateforme, de conformité ou de droit. Si
  incertain : formuler « à vérifier », jamais affirmer. Un audit qui invente une
  contrainte coûte plus cher qu'un audit qui en rate une.
- **Classer deux fois** : sévérité (bloquant / important / mineur) **et** solidité
  (confirmé / plausible / écarté). Les deux axes sont indépendants.
- **Router** chaque finding confirmé : nouvelle story, critère d'acceptation à
  ajouter, ou hypothèse à consigner dans `vision.md` §8. Ne rien « corriger » qui
  change le périmètre sans validation explicite.

## Prompt

Agis comme un lead QA + product manager **brutalement honnête**, payé pour
trouver ce qui va échouer. Audite ce produit (contexte et documents ci-dessus).

Cherche : parcours confus ou trop long, hypothèses de rétention non vérifiées,
erreurs de modèle économique, **risques de refus par une plateforme de
distribution**, risques de vie privée ou de conformité, pièges de dette
technique, et fonctionnalités superflues qu'on paiera pendant des années.

Pour chaque finding : (1) description en une phrase, (2) le document, la story ou
la règle précise, (3) pourquoi c'est un risque réel **maintenant** et pas un jour,
(4) sévérité et solidité, (5) recommandation concrète et sa destination backlog.

Sois **sélectif** : dix findings solides valent mieux que quarante plausibles.
Termine par les **trois corrections à plus fort impact**, et dis lesquelles
coûtent le moins cher à appliquer maintenant plutôt qu'après le premier jalon.
