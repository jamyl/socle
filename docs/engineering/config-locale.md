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
| `guard-bash.mjs` | avant chaque commande `Bash` | un push vers `main` (toutes les formes que la liste `deny` rate : `HEAD:main`, `-u origin main`, `git push` seul depuis `main`), un push forcé, `--no-verify`, et `gh pr merge` sur une branche `us-XXX-*` dont le dernier essai de `eval-run.mjs` n'est pas vert |
| `stop-gate.mjs` | quand l'agent veut s'arrêter — **seulement si `SOCLE_STOP_GATE=1`** | l'arrêt sur une branche de story avec un dernier essai rouge ou un diff non commité. Une relance par arrêt, pas plus |

Un refus sort en code 2 : Claude Code annule la commande et montre la raison à
l'agent. Le banc de tests : `node --test .claude/hooks/hooks.test.mjs`.

🔑 **Un hook n'est pas non plus un contrôle de sécurité.** Il lit la commande
telle qu'elle est écrite : un script intermédiaire, une refspec entre guillemets
ou un `gh pr merge <n>` lancé depuis une autre branche passent. Il rattrape
l'agent qui **oublie** une règle au 40e tour — le cas courant — pas celui qui la
contourne. La protection de branche GitHub reste la seule barrière.

## Sur un projet qui adopte la méthode

`scripts/adopt.sh` **ne touche jamais** `.claude/settings.json` : une liste de
permissions se relit à la main. Compare la tienne avec celle du template et
reprends ce qui manque — en particulier le bloc `deny` et le bloc `hooks`. Les
scripts des hooks, eux, sont copiés avec le reste de `.claude/`.

Si ton `settings.json` déclare un plugin ou un MCP, vérifie qu'il est bien
installé **et** qu'il figure dans le tableau d'outillage de `CLAUDE.md`. Ce
tableau est une liste blanche : un outil activé dans la configuration mais absent
du tableau est exactement le cas que la barre de confiance interdit.
