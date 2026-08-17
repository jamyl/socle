# {{NOM_AFFICHE}} — image PHP de développement (backend Laravel).
#
# Image pinnée par digest : un tag seul ne garantit pas un rebuild identique.
# « Docker ne garantit pas la reproductibilité » (arXiv 2601.12811) — la couche
# apt seule suffit à faire diverger deux builds du même Dockerfile à deux
# semaines d'écart.
FROM php:8.4-cli@sha256:f78661b492226388a7057679cc731c3e43bc92ba66cd49a8cfe12374a56bee9f

# Extensions requises par la stack :
#   pdo_pgsql/pgsql -> PostgreSQL (source de vérité)
#   intl            -> i18n
#   bcmath          -> arithmétique entière sûre (montants, quantités)
#   zip, opcache    -> Composer / performances
#   redis (pecl)    -> queues Horizon, cache, rate limiting
#   pcntl, posix    -> requis par Laravel Horizon (gestion des workers)
#
# ⚠️ `pcntl` sert aussi aux tests de concurrence RÉELS (niveau N4) : sans lui on
# ne peut pas forker de vrais processus, et un test de concurrence dégénère en
# boucle séquentielle — qui passe, en mentant.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git unzip libpq-dev libicu-dev libzip-dev \
    && docker-php-ext-install -j"$(nproc)" pdo_pgsql pgsql intl bcmath zip opcache pcntl posix \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2.9@sha256:b09bccd91a78fe8a9ab4b33d707b862e8fe54fec17782e32683ad2a69c46867d \
     /usr/bin/composer /usr/bin/composer

WORKDIR /app
