# socle

Template de projet pour **Claude Code** : la méthode de livraison est déjà en
place, le domaine se remplit à l'amorçage par une interview.

```bash
gh repo create mon-projet --template jamyl/socle --private --clone
cd mon-projet && claude
```

puis, dans la session : **`/bootstrap-project`**.

👉 **Suite détaillée : [GETTING-STARTED.md](GETTING-STARTED.md)** — prérequis,
étapes, vérifications, dépannage.

## Ce qu'il y a dedans

**Le cycle de livraison.** `/deliver-story` livre **une** story de bout en bout :
branche → plan → TDD → tests verts → revue en fan-out à trois nœuds → PR → CI
verte → merge squash. Conçu pour tourner en boucle (`/loop`).

**Le cadrage, séparé de la livraison.** `/cadrer-story` transforme un requis brut
en 2 à 5 stories au gabarit *Étant donné / Quand / Alors*, filtrées par INVEST,
avec les questions ouvertes tranchées et consignées. Séparé exprès : une story
mal cadrée découverte en livraison coûte une branche déjà ouverte.

**La discipline de contre-épreuve.** Un test n'est une preuve que si on l'a vu
échouer. Le skill porte les **huit motifs** de fausse vérification rencontrés en
vrai — tautologie, mise en scène absente, garde doublé ailleurs… — et la question
qui les résume : *« que devrait voir ce test pour devenir rouge ? »*

**La revue en fan-out.** Trois nœuds en lecture seule sur le même diff, sans se
lire entre eux : `reviewer` (conventions), `security-scanner` (vulns),
`domain-expert` (invariants métier). Un nœud muet est signalé — couverture
incomplète n'est pas « rien à signaler ».

**L'antériorité avant l'architecture.** `/dejavu` cherche si le problème dur est
déjà résolu et publié, avant qu'on le rebâtisse. Conclusions consignées avec
leurs identifiants dans `docs/engineering/prior-art.md`.

**Trois modules optionnels**, activés à l'interview :

| Module | Contenu |
|---|---|
| `stack-laravel` | Docker Compose (PHP 8.4 · PostgreSQL 16 · Redis · Mailpit · Horizon, images pinnées par digest), CI GitHub Actions (Pint, Larastan 8, Pest **sur PostgreSQL**, `composer audit`), scanner de secrets, MCP, 4 sous-agents Laravel, `E01` pré-écrit |
| `mobile-flutter` | `mobile/`, stories de toolchain (déjà `bloqué` — Xcode ne s'automatise pas), niveaux de test golden/intégration |
| `dejavu` | Le skill `/dejavu` embarqué et **versionné avec le projet** : scripts Python en bibliothèque standard seule, 4 sources académiques, aucune clé d'API. À ne pas activer si le poste l'a déjà en global |

Sans module : le cœur seul, agnostique.

## Ce qu'il n'y a pas dedans, exprès

- **Aucun scaffold applicatif.** Il naît de la première itération, avec les
  versions du jour. Un scaffold figé dans un template pourrit en silence.
- **Aucun domaine.** Le socle vient d'un projet financier ; toute trace de
  comptabilité en a été retirée. Il **demande** tes invariants au lieu de les
  supposer.
- **Aucun backlog complet.** L'amorçage écrit `E01` seulement. Les epics
  lointains rédigés trop tôt sont des epics à réécrire.

## Origine

Extrait d'un projet réel, après 49 PR et 50 stories livrées en
~44 h. Ce qui a survécu à l'extraction, c'est ce qui avait déjà attrapé un défaut :
la contre-épreuve, la revue à trois voix, la section « comment tu peux le vérifier
toi-même », et la barre de confiance sur l'outillage.

## Licence

[MIT](LICENSE).
