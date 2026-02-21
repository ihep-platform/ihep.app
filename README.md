# IHEP Platform

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=ihep-platform/ihep.app)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-Custom-green)

The Integrated Health Engagement Platform (IHEP) is a Next.js-based healthcare aftercare platform with digital twin technology, wellness tracking, and financial empowerment tools.

## 🚀 Quick Start

**New to the project?** See [GETTING_STARTED.md](./GETTING_STARTED.md) for all setup options.

### Option 1: GitHub Codespaces (Recommended)

The fastest way to get started is with GitHub Codespaces:

1. Click the "Open in GitHub Codespaces" badge above
2. Wait for the environment to set up (2-3 minutes)
3. Update `DATABASE_URL` in `.env.local`
4. Run `npm run dev`

See [CODESPACES_SETUP.md](./CODESPACES_SETUP.md) for detailed instructions.

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/ihep-platform/ihep.app.git
cd ihep.app

# Run the setup script
bash scripts/dev-setup.sh

# Validate your setup
bash scripts/validate-setup.sh

# Start the development server
npm run dev
```

Open [http://localhost:5000](http://localhost:5000) with your browser.

## 📚 Documentation

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Start here! All setup options and quick reference
- **[CODESPACES_SETUP.md](./CODESPACES_SETUP.md)** - GitHub Codespaces detailed guide
- **[QUICK_START.md](./QUICK_START.md)** - Local development setup details
- **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)** - Pre-launch checklist (120+ items)
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - GCP Cloud Run deployment guide
- **[SECURITY.md](./SECURITY.md)** - Security guidelines and PHI handling
- **[TODO.md](./TODO.md)** - Current tasks and project status
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Comprehensive project overview

## 🛠️ Tech Stack

- **Framework:** Next.js 16.1.5 with App Router
- **Language:** TypeScript 5 (strict mode)
- **UI:** React 19, Tailwind CSS 4, shadcn/ui
- **Database:** PostgreSQL with Drizzle ORM
- **Authentication:** NextAuth.js v4
- **Testing:** Vitest + React Testing Library (113+ tests)
- **Security:** Post-Quantum Cryptography (Kyber, ML-DSA)
- **3D Graphics:** Three.js for Digital Twin visualization
- **Deployment:** GCP Cloud Run with Docker

## 🏗️ Project Structure

```
ihep.app/
├── src/                    # Main application code
│   ├── app/               # Next.js App Router pages
│   ├── components/        # React components
│   ├── lib/              # Utilities and client logic
│   ├── hooks/            # Custom React hooks
│   └── shared/           # Shared schemas and types
├── .devcontainer/        # GitHub Codespaces configuration
├── scripts/              # Helper scripts
├── public/               # Static assets
└── docs/                 # Additional documentation
```

## 🧪 Development Commands

```bash
# Validation
bash scripts/validate-setup.sh  # Verify your setup is correct

# Development
npm run dev              # Start dev server (uses webpack for Three.js compatibility)
npm run dev:turbo        # Start dev server with Turbopack

# Building & Testing
npm run build            # Production build
npm run start            # Start production server
npm run check            # TypeScript type checking
npm run lint             # ESLint
npm test                 # Run tests
npm run test:watch       # Run tests in watch mode

# Database
npm run db:push          # Push schema changes to database
npm run db:studio        # Open Drizzle Studio
npm run db:generate      # Generate migrations
npm run db:migrate       # Run migrations
```

## 🔐 Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
# Required
NEXTAUTH_URL=http://localhost:5000
NEXTAUTH_SECRET=<generated-secret>
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
GOOGLE_CLIENT_ID=<your-google-client-id>
GITHUB_CLIENT_ID=<your-github-client-id>
SENTRY_DSN=<your-sentry-dsn>
```

Generate secrets with: `bash scripts/generate-secrets.sh`

## 🚢 Deployment

The platform is configured for deployment to GCP Cloud Run. See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

**Before deploying to production, review [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md).**

## 🧑‍💻 Contributing

This project uses:
- Conventional Commits for commit messages
- ESLint for code quality
- TypeScript strict mode
- Vitest for testing

See [CLAUDE.md](./CLAUDE.md) for AI assistance attribution.

## 📄 License

See [LICENSE](./LICENSE) file for details.

## 🆘 Support

- **Documentation:** See files in the repository root
- **Issues:** [GitHub Issues](https://github.com/ihep-platform/ihep.app/issues)
- **Contact:** jason@ihep.app

## 📈 Project Status

**Version:** 2.0.0  
**Status:** Production-ready foundation, database connection required

See [TODO.md](./TODO.md) for current tasks and [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) for detailed project information.
