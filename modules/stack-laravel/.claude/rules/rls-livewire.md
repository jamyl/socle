# RLS PostgreSQL et Livewire — quatre pièges

**Ne s'applique que si le projet cloisonne ses tenants par la RLS de
PostgreSQL** (Row Level Security), avec un contexte de tenant ouvert par
requête. Sans RLS, ignore ce fichier.

Chacun de ces pièges a été vécu sur un projet réel. Aucun ne lève d'erreur par
défaut : les données partent au mauvais endroit, ou ne partent pas, sans rien
dire.

## 1. Le contexte d'un composant Livewire tient pendant l'action

Livewire rejoue les middlewares persistants dans un pipeline qui se **termine
avant** l'action du composant. Un contexte de tenant ouvert par une fermeture
dans ce pipeline est donc refermé à vide au moment où l'action écrit.

→ Ouvre le contexte dans un `ComponentHook`, pour toute la durée du composant.
Referme-le dans `destroy()`, et aussi dans `app()->terminating()` pour le cas où
`destroy()` ne serait pas appelé.

## 2. Un `ComponentHook` s'enregistre dans `register()`, pas dans `boot()`

`ComponentHookRegistry::boot()` ne branche que les hooks qu'il connaît déjà. Un
hook enregistré dans le `boot()` d'un ServiceProvider n'est donc actif qu'à
partir de la **deuxième** application créée par le processus.

→ Enregistre-le dans `register()`.
**Symptôme en test** : seul le premier test du fichier est rouge, quel que soit
l'ordre des tests.

## 3. Une écriture perdue doit lever une erreur

Eloquent ignore le nombre de lignes que touchent `save()` et `delete()`. Sous un
rôle soumis à la RLS, une écriture faite hors contexte touche zéro ligne et
réussit quand même : la donnée est perdue sans erreur.

→ Dans le trait de cloisonnement, surcharge `performUpdate` (et la suppression).
Si une fiche **existante** ne touche aucune ligne, lève une exception.

## 4. Les tests doivent tourner sous le rôle de l'application

La suite tourne souvent sous le **propriétaire** de la base, que la RLS ne
contraint pas : chaque test d'isolation passe, et ne prouve rien.

→ Fournis un helper (`sousLeCompteDeLApplication()`) qui exécute un bloc sous le
rôle applicatif. Tiens un **cliquet** : la liste des dossiers de tests qui
tournent encore sous le propriétaire, une liste qui ne fait que rétrécir. Un
nouveau dossier n'y entre pas.
