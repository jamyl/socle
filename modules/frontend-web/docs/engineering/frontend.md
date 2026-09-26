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

## 6. Partir d'une référence

Une interface sans référence finit générique. Trois points de départ, du plus
sûr au moins sûr :

1. **Une maquette du projet** (image, export Figma) : Claude lit l'image, en tire
   `DESIGN.md` et `design/tokens.json`, puis le code. La story porte la maquette
   en `Référence visuelle` : la boucle visuelle de `/deliver-story` §4 compare
   l'écran livré à elle.
2. **Une capture d'un produit que tu admires** : même chemin, mais tu en
   retiens des **principes** (densité, hiérarchie, rythme), pas une copie.
3. **Un `DESIGN.md` public** — [awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
   en rassemble, extraits de sites réels (Vercel, Linear, Stripe…). **Inspiration
   seulement** : ces fichiers décrivent l'identité visuelle d'une marque tierce,
   et la reproduire n'est pas un choix de design, c'est un risque juridique.
   Rien de ce dépôt n'est copié ici.

## 7. Les skills de direction — des conseils, pas des gates

Trois skills vendorisés dans `.claude/skills/`, chacun figé à un commit avec sa
licence. Aucun n'a de mesure publiée de son effet : ils orientent la génération,
ils ne prouvent rien. Les gates §1 restent le seul verdict.

| Skill | Source | Déclenchement | Quand |
|---|---|---|---|
| `frontend-design` | Anthropic, Apache-2.0 | automatique, sur toute construction d'interface | par défaut : choisir une direction avant de coder, deux passes, critique sur capture |
| `/design-taste-frontend` | taste-skill v2, MIT | **manuel** | une direction affirmée (landing, portfolio) ; trois réglages : variance, mouvement, densité. ~22 000 tokens par appel |
| `/redesign-existing-projects` | taste-skill, MIT | **manuel** | refondre un écran existant : audit d'abord, puis corrections |

Les trois portent en tête le même garde : `DESIGN.md`, les tokens et `stack.md`
passent avant eux ; aucun paquet installé ni ressource externe sans story.

⚠️ Si le poste a déjà un `frontend-design` en global (plugin officiel), deux
skills portent le même nom. Garde l'un des deux.
