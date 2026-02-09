# Repository Guidelines

## Project Structure & Module Organization
The primary Next.js application lives under `src/`, with routes and API handlers in `src/app/`. Shared UI and features are in `src/components/`, utilities and client logic in `src/lib/`, and reusable hooks in `src/hooks/`. Static assets belong in `public/` and `src/assets/`. Infrastructure and service experiments live in folders like `terraform/`, `gcp/`, `k8s/`, and `services/` and are not part of the Next.js build.

## Build, Test, and Development Commands
- `npm run dev`: start the Next.js dev server.
- `npm run build`: production build.
- `npm run start`: run the production server locally.
- `npm run lint`: run ESLint (configured in `eslint.config.mjs`).

## Coding Style & Naming Conventions
- Use TypeScript in strict mode and the `@/*` path alias for `src/*`.
- Follow existing formatting in `src/` (2-space indentation, single quotes, semicolons).
- Components use PascalCase filenames (e.g., `PatientCard.tsx`); utilities and hooks use kebab-case (e.g., `use-auth.ts`).
- Prefer existing shadcn/ui components in `src/components/ui/` before adding new base UI.

## Testing Guidelines
- No repo-wide test runner is configured in `package.json`.
- If you add tests, use `*.test.ts(x)` and co-locate under `__tests__/` or next to the module.
- Existing `lib/simulation/__tests__` uses `node:test` but is excluded from the Next.js build; run it only if you set up a suitable runner.

## Commit & Pull Request Guidelines
- Commit messages generally follow Conventional Commits (e.g., `feat(digital-twin): …`, `fix(build): …`, `docs: …`, `security: …`).
- If AI assistance is used, include the co-author lines listed in `CLAUDE.md`.
- PRs should include a clear summary, testing notes, and UI screenshots when changing visuals.

## Security & Configuration Tips
- Start from `.env.example` and store secrets in `.env.local` only.
- Treat PHI as sensitive: avoid logging, localStorage, or URL exposure; see `SECURITY.md`.
- For project context and current priorities, review `PROJECT_SUMMARY.md`, `SESSION_HANDOFF.md`, and `TODO.md`.
