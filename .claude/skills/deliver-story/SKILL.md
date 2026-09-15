---
name: deliver-story
description: Livre la prochaine user story actionnable du backlog (docs/backlog/) en TDD, met à jour son statut et le journal de bord. Une story par exécution — conçu pour tourner en boucle via /loop.
---

# Livrer la prochaine story du backlog

Tu livres **exactement une user story** par exécution, de bout en bout. Tout
l'état vit dans les fichiers (statuts du backlog, `JOURNAL.md`, git) — ne
suppose aucun contexte d'une itération précédente hors de ces fichiers.

## 1. Sélection de la story

1. Lis `docs/backlog/JOURNAL.md` (s'il existe) : contexte des itérations passées,
   story annoncée comme suivante, blocages connus.
2. La **source unique d'ordonnancement est le graphe des dépendances** (« Dépend
   de » de chaque story), pas une liste figée. Balaie **tous** les epics dans
   l'ordre indicatif de la roadmap `docs/backlog/README.md` et prends la
   **première story `à faire` dont toutes les dépendances sont `fait`**. La roadmap
   n'est qu'un ordre de préférence : une story dont une dépendance vit dans un epic
   plus loin est simplement sautée puis redevient candidate quand sa dépendance est
   livrée — aucune exception codée en dur n'est nécessaire.
3. **Périmètre optionnel** : si des arguments sont passés (ex. `/deliver-story E01
   E02`), restreins le balayage à ces epics. Les dépendances **hors** périmètre
   comptent quand même : une story dont une dépendance n'est pas `fait` est sautée,
   même si cette dépendance vit ailleurs. Sans argument, le périmètre est le
   backlog entier.
4. Si la story exige une action humaine ou externe — création de compte chez un
   tiers, clé d'API, avis juridique, arbitrage business, installation d'un
   outil non automatisable, secret de production — passe son statut à
   `bloqué (motif précis)`, note ce qui est attendu de l'utilisateur, et prends
   la story actionnable suivante.
5. Une question qui surgit **en cours de livraison** et que tu pourrais trancher
   seul ne s'arrête pas : tranche sur la recommandation, applique, et écris la
   ligne dans `docs/backlog/DECISIONS.md` — même règle que `/cadrer-story`. Ce
   qui bloque, c'est ce que tu ne *peux* pas trancher, pas ce que tu préférerais
   faire valider.

## 2. Garde-fous (non négociables)

- Applique `docs/engineering/stack.md` (règles d'architecture) et
  `docs/engineering/testing-strategy.md` (niveau de test requis) à la lettre.
- Suite de tests rouge AVANT de commencer → ne livre rien : répare si c'est
  évident, sinon journalise le problème et termine l'itération là-dessus.
- Jamais de déploiement production, jamais de dépense, jamais de secret réel :
  sandbox, fakes et interfaces mockées uniquement.
- Story estimée XL ou manifestement trop grosse pour une itération : découpe-la
  en sous-stories (US-XXXa, US-XXXb…) dans le fichier d'epic, livre la première.
- **Story mal cadrée → `/cadrer-story` d'abord.** Un critère d'acceptation sans
  *Quand* ni *Alors*, ou qui nomme une bibliothèque plutôt qu'un comportement
  observable, n'est pas livrable tel quel : repasse la story par
  `/cadrer-story`, puis livre. Ne s'applique **pas** aux critères déjà `fait` —
  ils ne se réécrivent pas.

## 3. Implémentation

- **Ouvre une branche AVANT d'écrire quoi que ce soit** :
  `git checkout -b us-XXX-<slug-court>` depuis un `main` à jour. Jamais de
  travail directement sur `main`.
- Plan bref (3-5 lignes) en début d'itération, puis TDD : pour chaque critère
  d'acceptation, test qui échoue → code → vert.
- **Un scénario = un test portant son titre.** Quand le critère porte un titre en
  gras suivi d'un *Étant donné / Quand / Alors* (gabarit de `/cadrer-story`), le
  test reprend ce titre mot pour mot : le lien entre le critère et sa preuve se
  lit alors sans interprétation.
- Coche `[x]` chaque critère couvert dans le fichier d'epic, au fur et à mesure.

## 4. Vérification

- Exécute réellement les commandes de test, de formatage et d'analyse statique
  déclarées dans `docs/engineering/stack.md`, et rapporte leur **sortie réelle**.
  Jamais « devrait passer ».
- Story touchant un **domaine critique déclaré dans `CLAUDE.md`** (celui qui
  porte les règles les plus chères à violer) ou une migration de données : lance
  aussi `/security-review` et corrige les findings avant de clôturer.
- Tests verts = condition absolue du passage à `fait`.

### Revue en fan-out (avant `/security-review`)

Une fois les tests verts, exporte le diff et lance la revue parallèle :

```bash
git diff main...HEAD > /tmp/us-XXX.diff
```

puis le workflow `review-story` avec `{diffPath: "/tmp/us-XXX.diff", branch: "<branche>"}`.
Trois nœuds **en lecture seule** lisent le même diff sans se lire entre eux —
`reviewer` (conventions), `security-scanner` (vulns), `domain-expert`
(invariants métier) — et leurs findings sont dédupliqués en code.

Ce n'est **pas** un gate : il ne remplace ni les tests, ni `/security-review`,
qui restent souverains. Il sert à attraper avant la PR ce que la suite de tests
ne voit pas. Si un nœud ne rend pas de rapport, le workflow le signale : la
couverture est incomplète, ne le lis pas comme « rien à signaler ».

Quand un run déraille, attribue l'échec à **un** nœud (son prompt, ses outils,
son contrat d'entrée) et ne corrige que celui-là.

**Fais échouer tes propres tests avant de les présenter comme une preuve.**
Retire le garde, le verrou ou le correctif qu'ils prétendent couvrir, relance,
**constate le rouge**, restaure. Une vérification qui reste verte ne prouve rien
— et vaut moins que rien, car on cessera de la regarder.

Les huit motifs ci-dessous ont tous été rencontrés en vrai, sur un projet
financier, en deux jours. Ils ne dépendent pas du langage :

1. **Tautologie** — comparer la sortie d'un générateur à son entrée.
2. **`throws` à deux appels** — le premier lève, le second n'est jamais
   atteint. Isole **un seul** appel par assertion d'exception.
3. **Échec trop tôt** — l'exception survient avant la ligne censée être testée.
4. **Mise en scène absente** — le test ne crée jamais la condition qu'il décrit
   (aucune ligne dans l'état attendu, processus qui ne courent pas vraiment en
   parallèle).
5. **Mauvais environnement** — vérifier sur une base fraîche un défaut qui
   n'existe que sur une base **qui vit**. Ce contrôle-là appartient à une
   commande d'intégrité, pas à la suite de tests.
6. **Course calée sur des temporisations** — un test de concurrence dont
   l'ordre dépend de `sleep` passe là où on l'a écrit et ment sur une machine
   plus lente (un runner CI à deux cœurs sérialise ce qui collisionnait en
   local). Ce qui doit être ordonné l'est par un **signal**, pas par une durée.
7. **Preuve de durée pour un verrou** — mesurer qu'une opération a attendu ne
   dit pas *quel* verrou l'a fait attendre. Prouver l'**ordre**, pas la durée.
8. **Le garde retiré est doublé ailleurs** — la contre-épreuve reste verte non
   parce que le test est bon, mais parce qu'une autre couche produit le même
   résultat. Vécu : renommer un trigger de chaînage pour le faire passer AVANT
   l'horodatage ne cassait rien, la colonne portant `DEFAULT now()` et `now()`
   valant l'instant de la transaction. Quand une contre-épreuve reste verte,
   chercher **qui d'autre** fournit la valeur avant de conclure quoi que ce soit
   sur le test.

Et un piège d'**environnement**, pas de test — l'exemple est PostgreSQL, la
classe de défaut est universelle : insérer en masse dans une transaction
ouverte (ce que fait un rollback-par-test), c'est insérer des lignes que le
collecteur de statistiques ne voit pas. Un `ANALYZE` d'autovacuum qui passe
pendant ce temps voit les pages sans voir les lignes et enregistre
`reltuples = 0` sur une table de plusieurs Mo — le planificateur la croit vide
et choisit un plan catastrophique. Diagnostic : `reltuples` nul avec `relpages`
élevé dans `pg_class`. Correctif : `ANALYZE` explicite après le chargement.
**Le réflexe à garder** : quand une mesure de performance est absurde, soupçonner
les statistiques du moteur avant de soupçonner le code.

Avant d'écrire « c'est couvert », réponds à : *« que devrait voir ce test pour
devenir rouge ? »* Si la réponse n'est pas immédiate et concrète, il ne couvre
rien.

## 5. Clôture — par pull request

- Statut de la story → `fait` dans le fichier d'epic ; tout écart entre le livré
  et le prévu est noté sous la story.
- Ajoute une ligne à `docs/backlog/JOURNAL.md` (crée le fichier au besoin) :
  `- [YYYY-MM-DD HH:MM] US-XXX <titre> — fait|bloqué(motif) — tests : <commande> → <résultat> — suivante : US-YYY`
  (date réelle via la commande `date`).
- Commit atomique `US-XXX: <titre court>` sur la branche. Les correctifs issus
  de `/security-review` sont des commits séparés sur la même branche — le fil de
  la revue doit rester lisible dans la PR.

Puis, dans cet ordre :

```bash
git push -u origin us-XXX-<slug>
gh pr create --title "US-XXX — <titre>" --body "<corps, voir ci-dessous>"
gh pr checks --watch --fail-fast    # la CI tourne AVANT que main soit touché
gh pr merge --squash --delete-branch
```

Le corps de la PR porte : les critères d'acceptation cochés, la commande de test
et **sa sortie réelle**, les findings de `/security-review` et ce qu'ils ont
changé, et tout écart avec le prévu. C'est la trace qui manque quand ces
éléments ne vivent qu'en prose dans le journal.

**Ne merge JAMAIS sur une CI rouge.** Sur un repo privé en offre gratuite les
rulesets GitHub sont indisponibles (`403 : Upgrade to GitHub Pro`), donc **rien
ne t'en empêche techniquement**. C'est une règle de méthode, pas une barrière —
elle ne tient que si tu la tiens.

- **Tag** à la clôture d'un epic, pas à chaque story : `git tag -a e0X-complete`.
- Aucune branche ne survit à sa PR (`--delete-branch`). Si une branche traîne,
  c'est qu'une story n'a pas été clôturée : signale-le.

## 6. Rapport de fin d'itération

Termine ton message par : la story livrée, **l'URL de la PR mergée**, la commande
de test et son résultat réel, les stories passées `bloqué` avec ce qui est
attendu de l'utilisateur, et la prochaine story prévue.

### Puis, toujours : « comment tu peux le vérifier toi-même »

Tes rapports prouvent que *tu* as vérifié. Ils ne donnent à l'utilisateur aucun
moyen de le constater. Il doit pouvoir contrôler **sans te croire sur parole** —
et cette exigence monte avec l'enjeu : sur un produit qui manipule de l'argent,
des données personnelles ou une décision réglementée, elle n'est pas négociable.

Termine donc par une courte section, en langage simple et sans jargon :

- **Une commande copiable-collable**, jamais un principe. Si l'environnement est
  conteneurisé, elle est préfixée par le passage dans le conteneur — aucune
  commande ne doit supposer un service installé sur le poste.
- **Ce qu'il doit voir** : le nombre, la ligne, la couleur attendue.
- **Ce qui signalerait un problème.**
- **Le test qui échoue quand il existe** : « change telle valeur, relance, tu
  dois voir rouge » vaut mieux que « relance, tu dois voir vert » — c'est la
  seule façon de distinguer un filet d'un décor.
- **Dès qu'une interface existe** : l'URL exacte, quoi cliquer, ce qui doit
  s'afficher. Les tests verts ne suffisent pas.
- **Si ce n'est pas vérifiable à la main** — trigger de base, verrou concurrent,
  code sans écran — **le dire franchement** et proposer le plus proche
  observable : un compteur de tests, une requête en lecture, une ligne de
  journal. Ne jamais inventer une manipulation qui n'existe pas.

## 7. Condition d'arrêt de la boucle

S'il ne reste **aucune** story actionnable **dans le périmètre demandé** (tout est
`fait` ou `bloqué`), n'implémente rien et termine par exactement cette ligne :
`BACKLOG ÉPUISÉ — ARRÊTER LA BOUCLE` suivie de la liste des blocages en attente.
