# E01 (module mobile) — Toolchain & scaffold Flutter

> 🔧 Stories apportées par le module `mobile-flutter`. À **fusionner** dans
> `E01-fondations.md` au bootstrap, ou à garder à part si l'epic devient long.
>
> Les numéros sont en `US-15x` pour ne pas collisionner avec les stories backend.

---

## US-151 — Toolchain mobile native
**En tant que** développeur, **je veux** Flutter, Xcode et Android opérationnels
**afin de** builder l'app sur les trois cibles.
**Priorité** P0 · **Estimation** S ·
**Statut** bloqué (installation manuelle : Xcode via l'App Store, CocoaPods, Android Studio + JDK, acceptation des licences SDK — non automatisable)

> 🔑 **Cette story part `bloqué`, pas `à faire`.** La toolchain mobile est la
> seule partie non conteneurisable — contrainte Apple, pas choix d'architecture.
> Si elle partait `à faire`, la première itération de `/deliver-story` la
> prendrait, découvrirait le mur et perdrait un tour. Elle repasse actionnable
> d'elle-même dès que `flutter doctor` est propre.

Critères d'acceptation :
- [ ] Flutter SDK installé **nativement** (`flutter --version` répond).
- [ ] Xcode et Android Studio installés nativement.
- [ ] `xcode-select -p` pointe sur `Xcode.app`, **pas** sur `CommandLineTools` — c'est l'erreur la plus fréquente, et elle ne se manifeste qu'au premier build iOS.
- [ ] Licences Android SDK acceptées.
- [ ] `flutter doctor` sans erreur bloquante (un simulateur iOS + un émulateur Android disponibles).
- [ ] Étapes ajoutées à `docs/setup.md`.

> Au premier lancement d'un binaire Flutter, macOS peut bloquer l'exécution
> jusqu'à validation manuelle dans les Réglages. Ce n'est pas une panne.

## US-152 — Mobile scaffold + CI
**En tant que** développeur, **je veux** un squelette Flutter buildable **afin de**
valider la chaîne iOS/Android/web tôt.
**Priorité** P0 · **Estimation** S · **Statut** à faire
**Dépend de** : US-151, US-102

Critères d'acceptation :
- [ ] `flutter create mobile` (organisation propre), lints stricts (`flutter_lints`).
- [ ] Build debug OK sur simulateur iOS **et** émulateur Android **et** `flutter build web`.
- [ ] CI : `dart format --set-exit-if-changed`, `flutter analyze`, `flutter test` à chaque push.

> **Le scaffold n'est pas dans le template** : `flutter create` s'exécute ici,
> avec la version du jour. Un `mobile/` figé dans un template pourrit en
> quelques mois.

## US-153 — Socle UI (design system)
**En tant que** utilisateur, **je veux** une interface cohérente **afin de** faire
confiance au produit.
**Priorité** P0 · **Estimation** M · **Statut** à faire
**Dépend de** : US-152

Critères d'acceptation :
- [ ] Tokens (couleurs par **rôle**, typographie, espacements), aucune valeur en dur.
- [ ] Composants de base avec leurs états **vide / chargement / erreur** — ce sont les trois qu'on oublie, et ceux que l'utilisateur voit le jour où ça compte.
- [ ] i18n branchée dès le socle (fichiers ARB), pas rétrofitée.
- [ ] 🔑 **Golden tests dans chaque sens d'écriture** si le produit est bilingue LTR/RTL : le miroir se vérifie **pixel par pixel**, pas à l'œil. Un composant « qui devrait marcher en RTL » ne marche pas en RTL.
- [ ] Contraste AA **mesuré**, pas estimé.

> Le prompt de départ est dans `.claude/templates/prompt-design-system.md`.

## Niveaux de test ajoutés par ce module

À reporter dans `docs/engineering/testing-strategy.md` :

**N7 — Widget & golden tests (à chaque push).** Composants du socle en golden
tests, **un par sens d'écriture** si le produit est bidirectionnel. Widget tests
sur les écrans porteurs de logique (formulaires, confirmations).

**N8 — Tests d'intégration (pré-release).** `integration_test/` sur simulateur
iOS + émulateur Android, parcours critique de bout en bout, API mockée
localement. Puis le même parcours en smoke sur **staging** avant chaque release.

## Outillage

Le plugin `dart-flutter` (~22 skills) couvre Dart, Flutter et la gestion d'état.
**Inutile tant que `mobile/` est vide** — l'ajouter au tableau d'outillage de
`CLAUDE.md` au moment d'US-152, pas avant.
