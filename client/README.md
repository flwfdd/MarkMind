# mark-mind-client

This is the Vue 3 + Vite client for the MarkMind app.

## Requirements

- Node.js v20.19.0 or v22.12.0+
- pnpm or npm/yarn (this project includes a `pnpm-lock.yaml` — pnpm is recommended)
- Optional: `nvm`, `volta` or `asdf` to manage Node versions

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd) 
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
pnpm install
```

### Compile and Hot-Reload for Development

```sh
pnpm dev
```

### Type-Check, Compile and Minify for Production

```sh
pnpm build
```

### Lint with [ESLint](https://eslint.org/)

```sh
pnpm lint
### Other useful commands

- `pnpm run type-check` — Runs `vue-tsc` for TypeScript checks
- `pnpm run format` — Formats the `src/` directory with Prettier
- `pnpm preview` — Preview a production build

### Notes & Tips

- Global CSS lives in `src/assets/main.css` which imports `src/assets/base.css`.
- Components may use scoped styles — check `.vue` files for component-specific CSS.
- This project uses Tailwind; if you change `tailwind.config.js` or PostCSS, restart the dev server.
- If you change Node versions, delete `node_modules` and re-run `pnpm install` (or `npm ci`).

```
