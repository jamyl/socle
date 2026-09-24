# Sous-agents — réserves à connaître

**Trois agents ici**, plus ceux de la stack : les quatre du module
`stack-laravel`, ou `developer` et `dba` générés à l'amorçage depuis
`.claude/templates/agent-stack-*.md` quand aucun module de stack n'est activé.
Ce fichier dit ce qu'ils ne savent pas — le lire avant de croire l'un d'eux.

| Agent | Rôle | Outils |
|---|---|---|
| `reviewer` | Conventions, correction, architecture | **lecture seule**, aucun accès sortant |
| `security-scanner` | Vulnérabilités | **lecture seule**, aucun accès sortant |
| `domain-expert` | Invariants métier — **à spécialiser au bootstrap** | **lecture seule** + recherche web |

Ce sont exactement les trois nœuds de la revue en fan-out
(`.claude/workflows/review-story.js`). Il n'y a pas d'agent de plus au cœur : un
agent qu'aucun workflow n'invoque est un prompt que personne ne relit.

## Aucun des trois ne peut écrire

Les outils des **trois agents du socle** sont limités à la lecture — pas
d'`Edit`, pas de `Write`, pas de `Bash`, aucun outil MCP GitHub d'écriture. C'est
**structurel**, pas une consigne de prompt : un agent qui promet de ne rien
modifier mais garde `Write` tient sa promesse tant qu'il la lit.

Sur l'accès sortant, ils ne sont pas logés à la même enseigne, et c'est délibéré.
`reviewer` et `security-scanner` n'en ont **aucun** : leur entrée est un diff
potentiellement écrit par un tiers, et une instruction glissée dans un
commentaire suffirait à faire sortir du contenu privé sous forme de requête. Une
consigne de prompt ne résiste pas à ça ; l'absence d'outil, si. `domain-expert`
déclare `WebSearch` et `WebFetch`, parce qu'il doit pouvoir vérifier un texte
réglementaire — c'est le seul nœud de la revue qui peut sortir, à savoir avant de
lui confier un diff qu'on n'a pas écrit.

Tous déclarent `model: sonnet`. La politique complète et ce qu'un cycle coûte
sont dans `docs/engineering/models.md`.

⚠️ **Cela ne vaut pas pour les agents de stack.** Qu'ils viennent d'un module ou
d'un gabarit spécialisé à l'amorçage, ils **écrivent** : `developer`,
`queue-specialist` et `laravel-refactoring-expert` déclarent `Edit`, `Write` et
`Bash` ; seul `dba` reste bridé en lecture seule.

C'est justifié par ce qu'ils lisent. Les trois du socle consomment un **diff
tiers** dans la revue — surface d'injection. Un agent de stack reçoit une story
du pilote, pas un diff d'inconnu. Avant de croire qu'un agent de ce dossier ne
peut rien casser, **ouvre son `tools:`**.

Ce projet fait ses PR par le **CLI `gh` en local, après les tests**. Un outil
comme `push_files` permettrait de pousser du code sans passer par la suite de
tests locale — exactement ce que la PR est censée empêcher. Il n'est déclaré
nulle part, et `--read-only` sur le MCP `github` du module ne doit pas être
retiré.

## Ce qu'ils ignorent tous

- **Le backlog, le journal et les règles du domaine.** Aucun n'a lu la section
  « règles qui coûtent le plus cher à violer » de `CLAUDE.md` — sauf
  `domain-expert` une fois spécialisé, et c'est tout son intérêt. Un agent qui
  propose une solution correcte en général peut violer un invariant du projet
  sans le savoir.
- **La méthode.** Ils ne connaissent ni le cycle `deliver-story`, ni la
  discipline de contre-épreuve, ni le passage obligatoire par une PR.
- **La stack**, tant qu'ils n'ont pas lu `docs/engineering/stack.md`. Ils ne
  doivent appliquer aucune liste de contrôle propre à un framework qu'ils n'ont
  pas vérifié être celui du dépôt.

**Leurs findings passent par les mêmes tests et la même revue que le tien.**

## Ce qu'ils ne remplacent pas

- **`security-scanner` et `reviewer` ne remplacent pas `/security-review`.** Sur
  le projet d'origine, c'est `/security-review` qui a trouvé une faille
  exploitable à *chaque* story du domaine critique, après passage des agents.
- **La revue en fan-out ne remplace ni les tests, ni `/security-review`.** C'est
  un gate à deux tours sur ce que la suite de tests ne voit pas : correction,
  puis relecture du correctif, avant la PR.
- **Un rapport vide n'est pas un quitus.** Et un nœud qui ne rend pas de rapport
  n'est pas un nœud sans finding : `review-story` les distingue et le signale.

## Les agents à spécialiser

`/bootstrap-project` **doit** réécrire `domain-expert` — il porte les invariants
du domaine et alimente le troisième nœud de la revue. Sans module de stack, il
doit aussi spécialiser `developer` et `dba`, arrivés des gabarits avec leurs
placeholders et leurs blocs « À REMPLIR ». Même contrôle pour les trois :
`grep -n '{{\|À REMPLIR' .claude/agents/*.md` ne doit rien rendre.

**S'il ne trouve jamais rien, il n'a pas été spécialisé.** Vérifier alors qu'il
ne contient plus ni `{{…}}` ni les blocs « À REMPLIR », et que ses invariants
sont les mêmes que ceux de `.claude/workflows/review-story.js` et de `CLAUDE.md`.

## Historique

Le socle portait douze agents repris d'un jeu importé
(`AratKruglik/claude-laravel`) sans réécriture. Ils décrivaient une stack qui
n'est pas celle du template (Inertia/Vue, Socialite, Spatie, des versions
divergentes), réclamaient une vingtaine de skills absents du dépôt et hors de la
liste blanche de `CLAUDE.md`, et déclaraient des outils GitHub d'écriture.

Un sous-agent suit son prompt, pas `CLAUDE.md` : un prompt qui décrit un autre
projet est pire qu'un agent manquant, parce qu'il répond quand même.

Neuf ont été supprimés, `reviewer` et `security-scanner` réécrits autour de leur
seul rôle réel, `domain-expert` conservé — c'est le seul qui n'était pas importé.

Les quatre agents de `modules/stack-laravel/.claude/agents/` souffraient des mêmes
défauts et ont été réécrits à leur tour : en français, sur la stack que le module
livre réellement (Laravel 13, Filament, Horizon, PostgreSQL 16), sans les onze
skills et les deux fichiers de règles qui n'existaient pas, sans les MCP `figma`
et `ide` configurés nulle part, et avec toutes leurs commandes passant par le
conteneur.
