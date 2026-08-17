# {{PROJET}} — Stack technique & règles d'architecture

> Document de référence pour développer **sans écart**. Toute dérogation à ces
> choix se décide ici (PR sur ce fichier), jamais silencieusement dans le code.
> Stratégie de tests : voir [testing-strategy.md](testing-strategy.md).
>
> 🔧 Squelette. Le module `stack-laravel` en fournit une version **remplie** qui
> remplace ce fichier ; sans module, `/bootstrap-project` le rédige depuis
> l'interview.

## 1. Vue d'ensemble

| Couche | Technologie | Version | Rôle |
|---|---|---|---|
| Langage | À COMPLÉTER | | |
| Framework | | | |
| Base de données | | | Source de vérité unique |
| Cache / files d'attente | | | |
| Authentification | | | |
| Interface(s) | | | |
| Dev local | | | |
| CI/CD | | | Voir gates §4 |
| Observabilité | | | |

**Les versions sont verrouillées.** Une montée de version est une story, pas un
effet de bord.

## 2. Pourquoi ces choix

À COMPLÉTER — un paragraphe par arbitrage **non évident**, avec l'alternative
écartée et la raison. Ce qui est évident n'a pas besoin d'être justifié ; ce qui
l'est se réexplique à chaque session si on ne l'écrit pas.

Si `/dejavu` a servi, renvoyer ici vers la section de
[prior-art.md](prior-art.md) et ses identifiants.

## 3. Règles d'architecture

> ⚠️ Les règles **techniques** vivent ici. Les règles **du domaine** — celles qui
> coûtent le plus cher à violer — vivent dans `CLAUDE.md` et sont reprises dans
> le nœud `domain-expert` de la revue. Les deux listes sont distinctes et
> toutes les deux obligatoires.

À COMPLÉTER. Une règle utile est **vérifiable** : on peut écrire le test qui la
casse. Les familles qui reviennent :

1. **Où vit la logique métier** — et où elle n'a pas le droit de vivre
   (contrôleur, écran d'administration, template).
2. **Comment un état se modélise** — type énuméré + transitions explicites, pas
   de chaîne libre.
3. **Qui a le droit d'écrire quoi** — le point d'entrée unique d'une écriture
   critique, et l'interdiction faite à tout autre code.
4. **Ce qui est immuable** — ce qu'on ne met jamais à jour, ce qu'on compense
   plutôt que de corriger.
5. **Ce que les migrations peuvent faire** — et ce qu'elles ne peuvent plus faire
   dès qu'une donnée réelle existe.
6. **Le cloisonnement** — multi-tenant, périmètres, portées par défaut fermées.
7. **Les secrets** — ce qui n'existe jamais en clair, et où.
8. **Les textes utilisateur** — langues obligatoires, sens d'écriture.

## 4. Gates CI

À COMPLÉTER — quelle vérification tourne à quel moment, et laquelle bloque le
merge. Doit rester cohérent avec [testing-strategy.md](testing-strategy.md) §4.

## 5. Commandes

| Intention | Commande |
|---|---|
| Démarrer l'environnement | À COMPLÉTER |
| Lancer la suite de tests | |
| Formatage | |
| Analyse statique | |
| Migrations | |

> Ces commandes sont celles que `/deliver-story` exécutera et **dont il citera la
> sortie réelle**. Si une commande n'est pas ici, il n'a pas à la deviner.
