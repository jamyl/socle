# Configuration locale — ce qui se partage et ce qui ne se commite pas

Claude Code lit plusieurs fichiers de configuration. Certains appartiennent au
dépôt et doivent être identiques pour toute l'équipe ; d'autres sont propres à
ton poste et n'ont rien à faire dans l'historique. Les mélanger produit deux
symptômes désagréables : une permission qui marche chez toi et nulle part
ailleurs, ou un chemin de machine commité dans une PR.

## Ce qui se commite

| Fichier | Ce qu'il porte | Pourquoi partagé |
|---|---|---|
| `.claude/settings.json` | Les permissions `allow` et `deny` du projet | Toute l'équipe doit avoir les mêmes garde-fous. Une règle qui n'existe que chez une personne ne protège personne |
| `.claude/skills/`, `agents/`, `rules/`, `workflows/`, `templates/` | La méthode | C'est le contenu du dépôt, au même titre que le code |
| `CLAUDE.md` | Le contexte projet et la liste blanche d'outillage | Il est lu à chaque session, par tout le monde |
| `.mcp.json`, quand un module en fournit un | La déclaration des serveurs MCP | Un MCP déclaré chez une seule personne casse la revue pour les autres |

## Ce qui ne se commite jamais

Ces entrées sont déjà dans le `.gitignore` du template :

| Chemin | Ce que c'est | Pourquoi local |
|---|---|---|
| `.claude/settings.local.json` | Tes surcharges personnelles de permissions | Tu peux vouloir autoriser chez toi ce que le projet laisse en confirmation. Ça ne regarde que ta machine |
| `.claude/scheduled_tasks.json` et `.lock` | L'état des boucles `/loop` en cours | Une boucle appartient à la session qui l'a lancée. Commiter son état ferait croire à un autre poste qu'une boucle tourne |
| `.socle/runs/` | Le cache d'essais de `/deliver-story` : un fichier par tentative | C'est le **chemin** d'une story, pas son résultat. Le résultat vit dans la PR et dans `JOURNAL.md`. Le cache porte des sorties de commandes brutes, donc des chemins de ta machine et des extraits de journaux |
| `.socle/interdits.txt` | Les noms qui ne doivent jamais être publiés : un projet source, un client, une personne. Un terme par ligne, `#` commente. `guard-bash.mjs` refuse un commit, une PR ou un commentaire de PR qui en contient un, en mot entier et sans tenir compte de la casse | Commitée, la liste publierait elle-même ce qu'elle protège. Sans elle, le contrôle ne fait rien |
| `__pycache__/`, `*.pyc` | Bytecode Python | Propre à la version de l'interpréteur ; périmé pour quiconque clone |
| `*.bak` | Sauvegardes d'un amorçage interrompu | Elles contiennent la version **avant** substitution, donc les placeholders |

## Ce qui ne vit pas dans le dépôt du tout

| Où | Quoi |
|---|---|
| `~/.claude/settings.json` | Tes préférences globales, tous projets confondus |
| `~/.claude/skills/` | Les skills que tu as installés pour toi seul, comme `/dejavu` en global |
| `~/.cache/dejavu` | Le cache des recherches d'antériorité. Partagé entre **tous** tes projets : un run ici réchauffe le cache d'ailleurs. `DEJAVU_CACHE_DIR` le déplace |
| Variables d'environnement | `DEJAVU_CONTACT`, et toute clé d'API |

⚠️ **Une variable d'environnement doit être dans ton fichier de profil**
(`~/.zshrc`, `~/.bashrc`), pas seulement exportée dans un terminal. Le processus
de Claude Code a démarré avant ton `export` : il ne le voit pas. Après édition du
profil, **rouvre le terminal**.

## Les permissions, et ce qu'elles ne font pas

`.claude/settings.json` est volontairement **minimal** dans ce template : les
commandes de lecture et de commit sont en `allow`, et trois formes de push
destructif en `deny`.

Ce qui manque à la liste `allow`, exprès : `git push`, `gh pr create`,
`gh pr checks`, `gh pr merge`. `/deliver-story` en a besoin pour clôturer un
cycle, donc le premier passage demandera confirmation à chaque étape.

**Approuve-les au fil du premier cycle plutôt que d'élargir la liste à l'avance.**
Un `"Bash(git push:*)"` global paraît pratique et ouvre le premier interdit du
dépôt : `git push origin HEAD:main` pousse sur `main` sans PR, sans CI et sans
revue.

🔑 **Une liste `deny` n'est pas un contrôle de sécurité.** Elle compare des
préfixes littéraux, et les formes équivalentes d'un même push sont innombrables :
`HEAD:main`, `-u origin main`, un remote nommé autrement, `git push` seul depuis
`main`. Les trois règles `deny` du template attrapent les fautes d'inattention,
rien de plus.

Ce qui en est un : la **protection de branche côté GitHub**. Sur un dépôt privé
en offre gratuite elle est indisponible (`403 : Upgrade to GitHub Pro`) — dans ce
cas l'interdit ne tient que par la méthode, et c'est une raison de plus pour ne
pas pré-approuver `git push` en bloc.

## Les hooks, et ce qu'ils tiennent

`settings.json` déclare deux hooks, dans `.claude/hooks/` :

| Hook | Quand | Ce qu'il refuse |
|---|---|---|
| `guard-bash.mjs` | avant chaque commande `Bash` | un push vers `main` (toutes les formes que la liste `deny` rate : `HEAD:main`, `-u origin main`, `git push` seul depuis `main`), un push forcé, `--no-verify`, et `gh pr merge` sur une branche `us-XXX-*` dont le dernier essai de `eval-run.mjs` n'est pas vert, et `gh pr create` sur une story dont le corps ne porte pas la rétrospective ni le verdict de revue. Partout : un mot-clé de fermeture (`Fixes #12`) dans un commit ou une PR, un `rm` ou un `mv` sur `.socle/`, `.git`, `.env` ou `.claude/settings.local.json`, et `git clean -x`. Un nom de `.socle/interdits.txt` dans un commit (message, lignes ajoutées) ou une PR. Une commande qui ne rend jamais la main (`gh run watch` sans numéro, `docker compose up` sans `-d`, `logs -f`, `tail -f`), sauf bornée par `timeout`, un `&` ou un lancement en arrière-plan |
| `stop-gate.mjs` | quand l'agent veut s'arrêter — **seulement si `SOCLE_STOP_GATE=1`** | l'arrêt sur une branche de story avec un dernier essai rouge ou un diff non commité. Une relance par arrêt, pas plus |

Un refus sort en code 2 : Claude Code annule la commande et montre la raison à
l'agent. Le banc de tests : `node --test .claude/hooks/hooks.test.mjs`.

🔑 **Un hook n'est pas non plus un contrôle de sécurité.** Il lit la commande
telle qu'elle est écrite : un script intermédiaire, une refspec entre guillemets
ou un `gh pr merge <n>` lancé depuis une autre branche passent. Il rattrape
l'agent qui **oublie** une règle au 40e tour — le cas courant — pas celui qui la
contourne. La protection de branche GitHub reste la seule barrière.

## Un compte GitHub pour l'agent

Celui qui écrit le code ne doit pas agir avec le compte de celui qui valide.
L'agent pousse avec un **compte séparé**, dont le jeton n'a pas la portée
`workflow` : GitHub refuse alors tout push qui modifie `.github/workflows/`. La
garde des tests (`integrite.yml`) et l'alarme de merge ne changent donc qu'avec
le propriétaire. C'est le seul verrou que l'agent ne peut pas lever depuis sa
session (`docs/engineering/fiabilite-des-agents.md`).

1. **Crée un compte GitHub pour l'agent**, et invite-le en écriture sur le
   dépôt (Settings → Collaborators).
2. **Connecte-le dans un dossier à part**, depuis ton terminal. Ne colle jamais un
   jeton dans la conversation avec Claude :

   ```bash
   GH_CONFIG_DIR=~/.config/gh-<projet>-agent gh auth login
   ```

   Choisis HTTPS. Réponds **NON** à « Authenticate Git with your GitHub
   credentials? » : ça écrirait l'identifiant de l'agent dans ta configuration
   git globale, et ton propre terminal pousserait sous son nom.
   **N'accorde pas la portée `workflow`.** Sans elle, le jeton ne peut pas
   modifier les règles de la CI.
3. **Copie `.claude/settings.local.json.example` en `.claude/settings.local.json`**
   (déjà dans le `.gitignore`), et remplis-le. Le chemin de `GH_CONFIG_DIR` est
   absolu : `~` n'y est pas développé. Les deux lignes `GIT_CONFIG_*` vident
   d'abord la liste des helpers d'identifiants pour `github.com` (le trousseau du
   poste, par exemple), puis délèguent à `gh`, qui lit le dossier de l'agent.
4. **Relance Claude Code.** Les variables de `env` ne s'appliquent qu'au
   démarrage.

Pour vérifier :

| Où | Commande | Réponse attendue |
|---|---|---|
| Une session Claude Code | `gh api user --jq .login` | le compte agent |
| Une session Claude Code | `printf 'protocol=https\nhost=github.com\n\n' \| git credential fill` | `username=` le compte agent |
| Ton terminal | les deux mêmes | ton compte |

Toute modification de `.github/workflows/` se pousse **depuis ton terminal**,
avec ton compte. Quand une story en a besoin, l'agent écrit le fichier, puis te
donne la commande exacte à lancer. Il ne la contourne pas.

### Le verrou de merge gratuit : une organisation

Sur un dépôt **personnel**, un collaborateur a forcément le droit d'écriture,
donc celui de merger : le compte agent pourrait merger sur du rouge. Une
**organisation GitHub gratuite** permet de lui donner la seule lecture. Il
propose alors ses changements depuis sa copie (fork), et c'est le robot
`fusion.yml`, avec le jeton du dépôt, qui merge quand tout est vert.

1. Crée une organisation gratuite, et **transfère-lui le dépôt** (Settings →
   Danger Zone → Transfer).
2. Invite le compte agent comme **collaborateur du dépôt, en rôle Read**, pas comme
   membre de l'organisation.
3. Dans l'organisation (Settings → Member privileges), autorise les **forks de
   dépôts privés**.
4. Coche **« Run workflows from fork pull requests »** dans l'organisation
   (Settings → Actions), **puis** dans le dépôt : la case du dépôt reste grisée
   tant que celle de l'organisation ne l'est pas. Décoche l'approbation des
   workflows de forks. N'envoie aux forks **ni jeton d'écriture, ni secrets**.
5. Connecté avec le compte agent, crée sa copie du dépôt (`gh repo fork`), et
   ajoute-la comme remote `agent` dans le clone de travail.
6. Dans le dépôt (Settings → Secrets and variables → Actions → Variables) :
   `AGENT_LOGIN` = le compte agent. En option, `CHECKS_REQUIS` liste les
   contrôles indispensables, **séparés par des `;`**. Par défaut, le robot exige
   au moins la garde des tests.

Ce montage a été **éprouvé sur un projet réel** avant d'entrer dans socle : les
cinq essais ci-dessous y ont passé. Sur ce projet, une PR de la copie du compte
agent a été mergée par `github-actions`, et non par une personne. Rejoue-les
quand même sur un **dépôt jetable** de ton organisation avant d'y brancher le
vrai dépôt : les réglages d'organisation ne se copient pas avec le gabarit.

| Essai | Attendu |
|---|---|
| Le compte agent lance `gh pr merge` | refusé par GitHub |
| PR verte, avec `VERDICT: MERGE <sha>` du compte agent | mergée par `github-actions` |
| PR rouge, ou sans verdict | laissée ouverte |
| Le compte agent pousse un fichier de `.github/workflows/` | refusé (pas de portée `workflow`) |
| La CI d'une PR de fork | tourne sans clic |

## Sur un projet qui adopte la méthode

`scripts/adopt.sh` **ne touche jamais** `.claude/settings.json` : une liste de
permissions se relit à la main. Compare la tienne avec celle du template et
reprends ce qui manque — en particulier le bloc `deny` et le bloc `hooks`. Les
scripts des hooks, eux, sont copiés avec le reste de `.claude/`.

Si ton `settings.json` déclare un plugin ou un MCP, vérifie qu'il est bien
installé **et** qu'il figure dans le tableau d'outillage de `CLAUDE.md`. Ce
tableau est une liste blanche : un outil activé dans la configuration mais absent
du tableau est exactement le cas que la barre de confiance interdit.
