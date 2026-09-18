# Politique de modèles

Ce fichier dit **quel modèle tourne où, et pourquoi**. Il existe parce qu'un
modèle non déclaré hérite de celui de la session — le plus cher — et que
personne ne s'en aperçoit avant la facture.

## La règle

| Où | Modèle | Pourquoi |
|---|---|---|
| Les trois agents de la revue (`reviewer`, `security-scanner`, `domain-expert`) | `sonnet` | Ils vérifient une **liste de règles explicites** sur un diff borné. La tâche est du contrôle, pas de la conception |
| Les agents de stack (`developer`, `dba`, ceux d'un module) | `sonnet` | Ils travaillent sous les règles de `stack.md` et le cycle TDD de `/deliver-story`, qui rattrapent ce qu'ils laissent passer |
| Lectures isolées de `/dejavu` | `haiku` | 12 à 20 appels par run, chacun extrait quatre champs d'un seul résumé. C'est le plus gros poste d'un run et la tâche la plus simple |
| `/security-review` | le modèle de la session | Le seul endroit où le jugement lourd est justifié. C'est aussi le seul gate que `deliver-story` impose sur le domaine critique |
| La session elle-même | ton choix | `/model` en cours de session, `opusplan` pour réserver le modèle fort au mode plan |

**Un agent sans `model:` hérite du modèle de session.** C'est presque toujours une
erreur : il tourne au prix fort sur chaque story, indéfiniment. Tout agent de ce
dépôt déclare le sien.

## Ce qu'un cycle dépense

| Action | Appels d'agent |
|---|---|
| Une revue en fan-out | 3, un par nœud, sur chaque story |
| Une recherche `/dejavu` | environ 18 à 26 : 1 catégorisation, 12 à 20 lectures isolées en `haiku`, 1 notation, 1 regroupement, jusqu'à 3 textes intégraux, 1 convergence |
| `codesearch.py` seul | **zéro** — c'est un script Python, aucun modèle dans la boucle |
| `eval-run.mjs` (essai, pré-vol, rétro) | **zéro** — du Node sans dépendance ; il exécute tes commandes de test, il n'en juge rien |
| `/loop` | ce qui précède, autant de fois qu'il reste des stories, sans surveillance |

C'est pour ça que la découverte d'architecture utilise `codesearch.py` sur le
choix d'écosystème et réserve le run complet au mécanisme dur : la question
« quel framework » ne vaut pas vingt lectures d'articles, et aucun article n'y
répond.

## Le poste de dépense qu'on ne voit pas

Le plus gros gaspillage n'est pas un modèle trop cher sur un agent : c'est une
boucle qui n'avance pas. Un rouge qui résiste, un agent qui repatche le même
bloc, et chaque tentative relit le contexte, réécrit le fichier, relance la
suite de tests. Quinze essais sur une fausse piste coûtent plus que la story.

`.claude/rules/exploration-policy.md` plafonne à **deux** essais par hypothèse.
Le compte est tenu par `eval-run.mjs`, qui refuse le troisième — et le refus ne
coûte rien du tout, puisqu'il tombe avant l'exécution des tests. C'est la seule
économie de ce dépôt qui ne dégrade aucune capacité.

## Quand monter un agent en `opus`

Un seul cas défendable : **`domain-expert` sur un domaine critique lourd** —
conformité réglementaire, flux financiers, santé — où une règle ratée coûte plus
qu'un run. Change alors la ligne `model:` de `.claude/agents/domain-expert.md`,
et **écris ici pourquoi**. Un surcoût non justifié dans un fichier finit par être
copié dans les autres.

Ne monte jamais `reviewer` ni `security-scanner` : ce qu'ils rateraient est
précisément ce que `/security-review` est là pour attraper, et lui tourne déjà
au modèle de session.
