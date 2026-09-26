// Budgets sur les seuils « good » de web.dev. INP ne se mesure qu'avec de vrais
// utilisateurs : en laboratoire, Lighthouse le remplace par le Total Blocking
// Time, son meilleur indicateur avancé. Le vrai INP se lit en production.
const { readFileSync } = require('node:fs')
const conf = JSON.parse(readFileSync(`${__dirname}/routes.json`, 'utf8'))
const serveur = process.env.WEB_SERVER_CMD ?? conf.serveur
const baseURL = process.env.BASE_URL ?? conf.baseURL

module.exports = {
  ci: {
    collect: {
      url: conf.routes.map((r) => new URL(r, baseURL).href),
      numberOfRuns: 3,
      ...(serveur ? { startServerCommand: `cd .. && ${serveur}` } : {}),
    },
    assert: {
      assertions: {
        'largest-contentful-paint': ['error', { maxNumericValue: 2500, aggregationMethod: 'median-run' }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1, aggregationMethod: 'median-run' }],
        'total-blocking-time': ['error', { maxNumericValue: 200, aggregationMethod: 'median-run' }],
      },
    },
    upload: { target: 'filesystem', outputDir: '.lighthouseci' },
  },
}
