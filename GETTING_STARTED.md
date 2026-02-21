# Getting Started with IHEP Platform

Choose your preferred development environment:

## 🚀 Quick Start Options

### 1. GitHub Codespaces (Fastest - Recommended)
**Time to start: 2-3 minutes**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=ihep-platform/ihep.app)

1. Click the badge above or go to the repository → "Code" → "Codespaces" → "Create codespace on main"
2. Wait for automatic setup (installs dependencies, generates secrets)
3. Update `DATABASE_URL` in `.env.local`
4. Run `docker-compose -f docker-compose.dev.yml up -d` (starts PostgreSQL & Redis)
5. Run `npm run dev`
6. Open http://localhost:5000

**Full guide:** [CODESPACES_SETUP.md](./CODESPACES_SETUP.md)

---

### 2. Local Development
**Time to start: 5-10 minutes**

**Prerequisites:**
- Node.js 18+ (22 recommended)
- Docker (optional, for database)
- Git

**Steps:**
```bash
# 1. Clone repository
git clone https://github.com/ihep-platform/ihep.app.git
cd ihep.app

# 2. Run automated setup
bash scripts/dev-setup.sh

# 3. Start database (if using Docker)
docker-compose -f docker-compose.dev.yml up -d

# 4. Update .env.local with database URL
# DATABASE_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"

# 5. Initialize database
npm run db:push

# 6. Start development server
npm run dev
```

Open http://localhost:5000

---

### 3. Docker Development (Full Stack)
**Time to start: 10-15 minutes**

```bash
# Clone repository
git clone https://github.com/ihep-platform/ihep.app.git
cd ihep.app

# Set environment variables (see .env.example)
cp .env.example .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

The main application will be at http://localhost:3000

---

## 📚 Key Documentation

### For Developers
- **[CODESPACES_SETUP.md](./CODESPACES_SETUP.md)** - GitHub Codespaces quick start
- **[README.md](./README.md)** - Project overview and commands
- **[QUICK_START.md](./QUICK_START.md)** - Detailed local setup
- **[TODO.md](./TODO.md)** - Current tasks and status

### For Deployment
- **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)** - Pre-launch checklist (120+ items)
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - GCP Cloud Run deployment
- **[SECURITY.md](./SECURITY.md)** - Security guidelines

### For Understanding the Codebase
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Comprehensive project overview
- **[SESSION_HANDOFF.md](./SESSION_HANDOFF.md)** - Recent changes and known issues
- **docs/** - Technical specifications and design documents

---

## 🛠️ Common Commands

```bash
# Development
npm run dev              # Start dev server (webpack mode)
npm run dev:turbo        # Start dev server (Turbopack mode)

# Building & Testing
npm run build            # Production build
npm run start            # Start production server
npm run check            # TypeScript type checking
npm run lint             # Run ESLint
npm test                 # Run all tests
npm run test:watch       # Run tests in watch mode

# Database
npm run db:push          # Push schema to database
npm run db:studio        # Open Drizzle Studio UI
npm run db:generate      # Generate migrations
npm run db:migrate       # Run migrations

# Docker (Development Database)
docker-compose -f docker-compose.dev.yml up -d     # Start database
docker-compose -f docker-compose.dev.yml down      # Stop database
docker-compose -f docker-compose.dev.yml logs      # View logs
```

---

## 🔐 Environment Variables

**Required:**
- `NEXTAUTH_URL` - Your app URL (e.g., http://localhost:5000)
- `NEXTAUTH_SECRET` - Session encryption secret (auto-generated)
- `DATABASE_URL` - PostgreSQL connection string

**Generate secrets:**
```bash
bash scripts/generate-secrets.sh
```

**Using Docker:**
```bash
DATABASE_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"
```

**See `.env.example` for all available variables**

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Change port in .env.local
PORT=3000
```

### Dependencies Issues
```bash
rm -rf node_modules .next
npm install
```

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart
docker-compose -f docker-compose.dev.yml restart
```

### Three.js Bundling Errors
The project uses webpack by default (not Turbopack) to avoid Three.js bundling issues. If you encounter errors:
```bash
npm run dev  # Uses webpack by default
```

---

## 🎯 What to Do Next

### For Development
1. ✅ Complete setup (above)
2. Read [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) to understand the architecture
3. Check [TODO.md](./TODO.md) for current tasks
4. Browse the codebase in `src/`

### For Production Launch
1. ✅ Complete setup (above)
2. Review [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - **Start here!**
3. Configure all required environment variables
4. Set up production database
5. Complete security audit
6. Run deployment to staging
7. Complete pre-launch testing
8. Deploy to production

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/ihep-platform/ihep.app/issues)
- **Email:** jason@ihep.app
- **Documentation:** See files in repository root

---

**Version:** 2.0.0  
**Last Updated:** February 17, 2026
