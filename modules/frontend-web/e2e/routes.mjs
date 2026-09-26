// Source unique des pages contrôlées : les trois gates (axe, capture,
// Lighthouse) lisent ce fichier. Une page ajoutée ici est contrôlée partout.
import { readFileSync } from 'node:fs'

const conf = JSON.parse(readFileSync(new URL('./routes.json', import.meta.url), 'utf8'))

export const serveur = process.env.WEB_SERVER_CMD ?? conf.serveur
export const baseURL = process.env.BASE_URL ?? conf.baseURL
export const routes = conf.routes
