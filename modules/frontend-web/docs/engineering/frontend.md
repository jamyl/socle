# Frontend — les gates et les règles

Ce fichier vient du module `frontend-web`. Il décrit ce qui **prouve** qu'une
interface est correcte, et ce qui ne fait que l'**orienter**.

> Une gate rend vert ou rouge. Un conseil améliore la génération sans rien
> prouver. Les deux servent ; seule la première bloque un merge.

## 1. Ce qui est vérifié, et par quoi

| # | Gate | Outil | Rouge si | Preuve que ça sert |
|---|---|---|---|---|
| 1 | Boucle visuelle | Playwright (capture) + relecture | un écart avec la référence de la story n'est pas corrigé | Doc Claude Code : « verify UI changes visually » ; gate UI de Shopify Helix |
| 2 | Accessibilité | `@axe-core/playwright` | une violation `serious` ou `critical` | Deque : ~57 % des défauts trouvés automatiquement (étude du vendeur) |
| 3 | Tokens | `stylelint` + `design/build-tokens.mjs --check` | une couleur, un espacement ou une police en dur ; un `tokens.css` périmé | Spec DTCG 2025.10 |
| 4 | Performance | Lighthouse CI | LCP > 2,5 s, CLS > 0,1, TBT > 200 ms (médiane de 3 runs) | Vodafone : LCP −31 % → +8 % de ventes (A/B, web.dev) |
| 5 | Régression visuelle (N7) | `toHaveScreenshot` | un pixel change sur une page de `e2e/routes.json` | — |

Les gates 2 à 5 tournent en CI (`.github/workflows/frontend.yml`) et en local :

```bash
cd e2e && npm ci
npm run gates     # tokens, styles, accessibilité, captures
npm run perf      # Lighthouse
```

La gate 1 est une étape de `/deliver-story` §4 : elle demande une référence et
un regard, pas seulement un script.

## 2. Brancher l'app

Tout part de `e2e/routes.json` :

| Clé | Sens |
|---|---|
| `preparation` | ce qui rend l'app lançable en CI (`npm ci && npm run build`…) |
| `serveur` | la commande qui la sert, lancée depuis la racine |
| `baseURL` | où elle répond |
| `routes` | les pages contrôlées par **toutes** les gates |

Tant que `serveur` est vide, la CI saute les gates. Une fois rempli sur `main`,
une PR ne peut plus le vider pour les sauter. `BASE_URL` et `WEB_SERVER_CMD`
surchargent le fichier en local. Si l'app demande plus que Node pour démarrer
(PHP, une base), `preparation` l'installe, ou les gates rejoignent la CI de la
stack.

## 3. Les règles vérifiables

1. **Tout état est dessiné** : vide, chargement, erreur, succès. Une liste sans
   état vide est une story incomplète.
2. **Aucune valeur en dur** : couleur, espacement, police, rayon, ombre passent par
   `var(--…)` de `design/tokens.css`. Stylelint le refuse.
3. **Tout est atteignable au clavier**, avec un focus visible. Axe voit le
   nom accessible ; il ne voit pas l'ordre de tabulation — ça se teste à la main
   ou par un test Playwright au clavier.
4. **Le mouvement respecte `prefers-reduced-motion`.**
5. **Une information ne passe jamais par la seule couleur** : texte ou icône en plus.
6. **Chiffres comparés en `font-variant-numeric: tabular-nums`.**

Ce qu'axe **ne voit pas** : la pertinence d'un texte alternatif, l'ordre logique,
un libellé ambigu, un piège au clavier. Zéro violation n'est pas « accessible ».

## 4. Les captures de référence

Le rendu des polices dépend de l'OS : une capture faite sur macOS ne se compare
pas à une capture faite sous Linux. Les références se génèrent **dans l'image
Playwright de la CI**, à la version exacte de `@playwright/test` :

```bash
docker run --rm -v "$PWD:/w" -w /w/e2e mcr.microsoft.com/playwright:v1.63.0-noble \
  sh -c 'npm ci && npx playwright test --update-snapshots'
```

Une différence voulue se valide en régénérant la capture **dans le commit du
changement**. La tolérance reste à zéro pixel : à 1 %, un bouton vidé de son
texte passait (constaté à la mise en place du module).

## 5. Les tokens

`design/tokens.json` (format DTCG) est la source ; `design/tokens.css` en est
généré et commité. Après toute modification :

```bash
cd e2e && npm run tokens
```

`npm run gates` refuse un `tokens.css` qui ne correspond plus au JSON.
`DESIGN.md` à la racine dit l'intention de chaque token.
