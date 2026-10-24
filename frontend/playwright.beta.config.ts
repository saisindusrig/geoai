import {defineConfig,devices} from '@playwright/test';

export default defineConfig({
  testDir:'./e2e',
  testMatch:['offline-platform-website.spec.ts','production-beta.spec.ts'],
  fullyParallel:false, workers:1, retries:0, timeout:180_000,
  outputDir:'../docs/production-beta/browser-results',
  reporter:[['list'],['json',{outputFile:'../docs/production-beta/browser-tests.json'}]],
  use:{baseURL:'http://localhost:3011',viewport:{width:1600,height:900},
    screenshot:'only-on-failure',trace:'retain-on-failure',video:'on',
    launchOptions:{args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']}},
  projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}],
});
