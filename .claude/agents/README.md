# Sous-agents — réserves à connaître

**Trois agents ici**, plus quatre si le module `stack-laravel` est activé. Ce
fichier dit ce qu'ils ne savent pas — le lire avant de croire l'un d'eux.

| Agent | Rôle | Outils |
|---|---|---|
| `reviewer` | Conventions, correction, architecture | **lecture seule** |
| `security-scanner` | Vulnérabilités | **lecture seule** + recherche web |
| `domain-expert` | Invariants métier — **à spécialiser au bootstrap** | **lecture seule** |

Ce sont exactement les trois nœuds de la revue en fan-out
(`.claude/workflows/review-story.js`). Il n'y a pas d'agent de plus au cœur : un
agent qu'aucun workflow n'invoque est un prompt que personne ne relit.

## Aucun d'eux ne peut écrire

Leurs outils sont limités à la lecture — pas d'`Edit`, pas de `Write`, pas de
`Bash`, aucun outil MCP GitHub d'écriture. C'est **structurel**, pas une
consigne de prompt : un agent qui promet de ne rien modifier mais garde `Write`
tient sa promesse tant qu'il la lit.

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
- **La revue en fan-out ne remplace ni les tests, ni `/security-review`.** Ce
  n'est pas un gate : elle attrape avant la PR ce que la suite de tests ne voit
  pas.
- **Un rapport vide n'est pas un quitus.** Et un nœud qui ne rend pas de rapport
  n'est pas un nœud sans finding : `review-story` les distingue et le signale.

## `domain-expert` : le seul à spécialiser

C'est le seul agent de ce dossier que `/bootstrap-project` **doit** réécrire, et
c'est celui qui compte. Il porte les invariants du domaine et alimente le
troisième nœud de la revue.

**S'il ne trouve jamais rien, il n'a pas été spécialisé.** Vérifier alors qu'il
ne contient plus ni `{{…}}` ni les blocs « À REMPLIR », et que ses invariants
sont les mêmes que ceux de `.claude/workflows/review-story.js` et de `CLAUDE.md`.

## Historique

Un jeu de seize agents importés (`AratKruglik/claude-laravel`) a été retiré :
ils décrivaient une stack qui n'est pas celle du template (Inertia/Vue, Socialite,
Spatie, des versions divergentes), réclamaient une vingtaine de skills absents du
dépôt et hors de la liste blanche de `CLAUDE.md`, et déclaraient des outils
GitHub d'écriture. Un sous-agent suit son prompt, pas `CLAUDE.md` : un prompt qui
décrit un autre projet est pire qu'un agent manquant, parce qu'il répond quand
même. Les agents propres à la stack Laravel vivent désormais dans
`modules/stack-laravel/.claude/agents/`.
