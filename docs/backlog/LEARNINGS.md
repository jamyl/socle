# {{PROJET}} — ce qu'on ne refait plus

Lu **avant** chaque story par `/deliver-story` et par les agents de stack. Une
leçon écrite ici évite que la story suivante retombe dans la même impasse : la
mémoire d'une session ne survit pas à la suivante, ce fichier si.

Shopify Helix fait la même chose : le retour de l'ingénieur est gardé en mémoire
pour tous les checkpoints suivants, et c'est ce qui fait grandir l'autonomie au
fil du projet.

## Ce qui entre ici

- Une **impasse abandonnée** : `eval-run.mjs retro` propose la ligne.
- Un **écart trouvé à la recette** : ce que tu as vu en utilisant le produit.
- Un **finding de revue qui revient** d'une story à l'autre.

Ce qui n'entre pas : une décision à valider (c'est `DECISIONS.md`), l'historique
des livraisons (c'est `JOURNAL.md`).

## Format

Une ligne par leçon, la plus récente en bas. La leçon est **à l'impératif** et
**vérifiable sur un diff** : « ne pas X », « toujours Y avant Z ».

`- [YYYY-MM-DD] <leçon> — source : <retro US-XXX | recette | revue PR #n>`

## Péremption

Une leçon vieillit quand son objet disparaît : la commande, le module ou
l'écran dont elle parle n'existe plus. Elle ne s'efface pas, elle se raye, avec
la date et la raison :

`- ~~[2026-03-02] ne pas X~~ — périmée le 2026-06-10 : le module Y est retiré`

L'historique reste lisible, et la leçon rayée ne se lit plus comme une règle.
La relecture se fait à la clôture de chaque epic (`/deliver-story` §5).

## Leçons

