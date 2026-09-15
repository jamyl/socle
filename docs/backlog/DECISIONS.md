# {{PROJET}} — décisions prises seul, à valider en fin de cycle

Une question ouverte ne s'attend pas : elle **se tranche sur la recommandation**,
s'applique, et s'écrit ici. Rien ne s'arrête. C'est ce qui permet à
`/cadrer-story` et `/deliver-story` de tourner en boucle, y compris sans
personne devant l'écran.

Ce fichier est donc la contrepartie du silence : tout ce qui n'a pas été demandé
est écrit, daté, et relisible d'un coup d'œil.

## Comment lire ce fichier

Une ligne par décision, la plus récente en bas. Trois colonnes portent
l'information utile :

- **Ce qui a été retenu** — la recommandation appliquée.
- **L'alternative écartée** — ce qu'on aurait fait sinon.
- **Coût du revirement** — ce que ça coûte de changer d'avis **maintenant**, et
  ce que ça coûtera **plus tard**. C'est la seule colonne qui décide de l'ordre
  dans lequel tu les relis.

Une décision sans coût de revirement chiffré n'est pas relisible : « faible — un
écran à rouvrir » et « élevé — migration sur des données réelles » ne se relisent
pas avec la même urgence.

⚠️ Les lignes marquées 🔴 touchent le **domaine critique** déclaré dans
`CLAUDE.md` § « les règles qui coûtent le plus cher à violer ». Une décision 🔴
déjà appliquée à des données réelles ne se révise pas gratuitement : la revoir
demande une migration de correction, pas un changement de code.

## Journal

| Date | Story | La décision | Ce qui a été retenu | Alternative écartée | Coût du revirement |
|---|---|---|---|---|---|

*Aucune décision pour l'instant.*
