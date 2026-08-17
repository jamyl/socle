# Règles git

Référencé par plusieurs sous-agents. Fait autorité sur ce dépôt.

## Le cycle

Une story = une branche = une PR = un commit sur `main` (squash).

```bash
git checkout -b us-XXX-<slug-court>      # depuis un main à jour
# … TDD, tests verts, revue en fan-out …
git commit -m "US-XXX: <sujet à l'impératif>"
git push -u origin us-XXX-<slug>
gh pr create --title "US-XXX — <titre>" --body "<corps>"
gh run watch --exit-status                # la CI tourne AVANT que main soit touché
gh pr merge --squash --delete-branch
```

## Interdits

- **Jamais de push direct sur `main`.**
- **Jamais de merge sur une CI rouge.** Sur un repo privé en offre gratuite, les
  rulesets GitHub sont indisponibles (`403 : Upgrade to GitHub Pro`) : rien ne
  t'en empêche techniquement. C'est une règle de méthode — elle ne tient que si
  tu la tiens.
- **Jamais de `--force` sur une branche partagée**, ni de réécriture d'historique
  sur `main`.
- **Aucune branche ne survit à sa PR** (`--delete-branch`). Une branche qui
  traîne signale une story non clôturée : le dire.
- Les MCP d'écriture GitHub (`push_files`, `create_pull_request`) ne sont pas
  utilisés ici : ils permettraient de pousser sans passer par la suite de tests
  locale, ce que la PR est précisément censée empêcher. Le CLI `gh`, après les
  tests.

## Messages de commit

`US-XXX: sujet` pour une story ; `fix:` / `chore:` / `docs:` sinon. Le **corps**
porte le raisonnement : ce qui a été trouvé, ce qui a été écarté et pourquoi.

Les correctifs issus d'une revue sont des **commits séparés** sur la même
branche — le fil de la revue doit rester lisible dans la PR.

## Après un merge

```bash
git fetch --prune    # sinon la branche distante supprimée reste en cache local
```
