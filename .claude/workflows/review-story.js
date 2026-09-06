export const meta = {
  name: 'review-story',
  description: 'Revue pré-commit en fan-out lecture seule sur le diff d\'une story (qualité, vulns, invariants métier)',
  whenToUse: 'Étape revue de /deliver-story, après tests verts et avant /security-review. args = {diffPath, branch}',
  phases: [
    { title: 'Revue', detail: 'reviewer + security-scanner + domain-expert en parallèle sur le même diff' },
  ],
}

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string', description: 'chemin relatif au repo' },
          line: { type: 'integer', description: '0 si non localisable' },
          invariant: { type: 'string', description: 'la règle violée, en une clause' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          detail: { type: 'string', description: 'ce qui casse, concrètement' },
        },
        required: ['file', 'line', 'invariant', 'severity', 'detail'],
      },
    },
  },
  required: ['findings'],
}

const diffPath = args?.diffPath
const branch = args?.branch ?? '(branche non précisée)'
if (!diffPath) throw new Error('args.diffPath est requis — écrire le diff avec: git diff main...HEAD > <path>')

const contrat = `Lis UNIQUEMENT le fichier de diff ${diffPath} (branche ${branch}). N'ouvre aucun autre fichier du repo sauf pour lever une ambiguïté sur une ligne du diff. Ne modifie rien. Rapporte seulement ce que le diff démontre : pas d'hypothèse sur du code non montré. Si le diff ne viole rien de ta liste, renvoie une liste vide — un rapport vide est une réponse valide.`

const NOEUDS = [
  {
    label: 'reviewer',
    agentType: 'reviewer',
    regles: [
      'logique métier hors des contrôleurs (validation -> action/service -> présentation)',
      'états modélisés par des types énumérés + transitions explicites, pas de chaînes libres',
      'pas de logique métier dans la couche de présentation ni dans un écran d\'administration',
      'style et conventions du code existant',
    ],
  },
  {
    label: 'security-scanner',
    agentType: 'security-scanner',
    regles: [
      'aucun secret ni donnée sensible en clair (base, logs, réponse d\'API non authentifiée)',
      'autorisation présente sur chaque ressource exposée (BOLA/BFLA, IDOR)',
      'validation des entrées, injection SQL, XSS',
      'enveloppe d\'erreur homogène, sans fuite d\'information interne',
    ],
  },
  {
    label: 'domain-expert',
    agentType: 'domain-expert',
    // ⚠️ Rempli au bootstrap depuis les « règles qui coûtent le plus cher à
    // violer » de CLAUDE.md. Une clause par ligne, VÉRIFIABLE sur un diff :
    // « aucun code hors de X n'écrit dans Y » se vérifie, « le code doit être
    // propre » ne se vérifie pas. C'est ce nœud qui attrape ce que ni les
    // conventions ni les vulns ne voient.
    regles: [
      '{{INVARIANTS}}',
    ],
  },
]

phase('Revue')

const rapports = await parallel(NOEUDS.map((n) => () =>
  agent(
    `${contrat}\n\nTu vérifies exactement ces règles, et rien d'autre :\n${n.regles.map((r) => `- ${r}`).join('\n')}`,
    { label: n.label, agentType: n.agentType, phase: 'Revue', schema: FINDINGS },
  // ⚠️ `agent()` RÉSOUT à `null` quand le nœud meurt — il ne lève pas. Un
  // `r?.findings ?? []` transformait ce `null` en rapport vide : le nœud mort
  // était compté comme « a répondu, rien à signaler », exactement le contresens
  // que la détection de nœuds muets plus bas est censée empêcher. Le rapport
  // reste `null` jusqu'au filtre, et `muets` le voit.
  ).then((r) => (r ? { noeud: n.label, findings: r.findings ?? [] } : null))
))

const rang = { high: 0, medium: 1, low: 2 }
const vus = new Set()
const findings = []
for (const r of rapports.filter(Boolean)) {
  for (const f of r.findings) {
    const cle = `${f.file}:${f.line}:${f.invariant}`
    if (vus.has(cle)) continue
    vus.add(cle)
    findings.push({ ...f, noeud: r.noeud })
  }
}
findings.sort((a, b) => rang[a.severity] - rang[b.severity])

const muets = NOEUDS.map((n) => n.label).filter((l) => !rapports.some((r) => r?.noeud === l))
if (muets.length) log(`⚠️ nœud(s) sans rapport, couverture incomplète : ${muets.join(', ')}`)

log(`${findings.length} finding(s) après dédup — ${rapports.filter(Boolean).length}/${NOEUDS.length} nœuds ont répondu`)

return { branch, diffPath, noeudsMuets: muets, findings }
