import { defineConfig, devices } from '@playwright/test'
import { serveur, baseURL } from './routes.mjs'

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  forbidOnly: true,
  retries: 0,
  reporter: [['list']],
  // Les captures de référence dépendent du rendu des polices, donc de l'OS :
  // elles se génèrent et se comparent dans l'image Playwright officielle, la
  // même en local et en CI (docs/engineering/frontend.md).
  snapshotPathTemplate: '{testDir}/__captures__/{arg}{ext}',
  // Tolérance par défaut de Playwright (zéro pixel) : à 1 %, un bouton vidé de
  // son texte passait (constaté). Une capture générée dans la même image ne
  // bouge pas d'un pixel sans raison.
  expect: { toHaveScreenshot: { animations: 'disabled' } },
  use: { baseURL },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: serveur ? { command: serveur, url: baseURL, reuseExistingServer: !process.env.CI, cwd: '..' } : undefined,
})
