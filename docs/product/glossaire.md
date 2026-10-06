# {{PROJET}} — glossaire

Un mot par notion métier, et une seule notion par mot. Lu **avant** chaque story
par `/deliver-story`, et par l'agent `domain-expert`. Le code, les tests et les
stories reprennent ces mots tels quels : un nom de classe, de table ou de test
qui s'en écarte est un défaut de revue.

Pourquoi : un agent qui découvre le jargon en cours de route met vingt mots là où
un suffit, et nomme la même chose de trois façons dans trois fichiers. « Un
problème quand une leçon devient réelle, c'est-à-dire qu'elle a une place sur le
disque » devient « un problème dans la matérialisation ». Idée reprise de
`mattpocock/skills`.

## Ce qui entre ici

- Chaque mot métier nouveau d'une story : `/cadrer-story` l'ajoute.
- Un mot ambigu qu'une story a tranché (« compte » : le client ou l'utilisateur ?).

Un mot qui contredit une ligne existante ne s'ajoute pas à côté : la divergence
se tranche, dans `DECISIONS.md`, et la ligne est corrigée.

## Format

Une ligne par terme, par ordre alphabétique. La définition dit **ce que c'est**,
pas comment c'est codé. « Ne pas confondre avec » nomme le voisin le plus proche.

| Terme | Définition | Ne pas confondre avec | Introduit par |
|---|---|---|---|
