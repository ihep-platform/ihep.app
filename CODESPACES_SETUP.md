# GitHub Codespaces Quick Start

This guide will help you get the IHEP Platform running in GitHub Codespaces in under 5 minutes.

## 🚀 Launch Codespace

1. Click the "Code" button on the GitHub repository
2. Select the "Codespaces" tab
3. Click "Create codespace on main" (or your preferred branch)

The Codespace will automatically:
- ✅ Install Node.js 22
- ✅ Install all npm dependencies
- ✅ Create `.env.local` from `.env.example`
- ✅ Generate a secure `NEXTAUTH_SECRET`
- ✅ Run TypeScript checks
- ✅ Run the test suite

## ⚙️ Configure Environment Variables

After the Codespace starts, you need to configure your database connection:

### Option 1: Use Docker Compose (Recommended for Development)

Start PostgreSQL and Redis locally:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This will start:
- PostgreSQL on port 5432 (username: `ihep`, password: `ihep_dev_password`, database: `ihep_db`)
- Redis on port 6379

Update `.env.local`:
```bash
DATABASE_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"
DIRECT_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"
```

To stop the services:
```bash
docker-compose -f docker-compose.dev.yml down
```

### Option 2: Use External Database

Update `.env.local` with your external database connection:
```bash
DATABASE_URL="postgresql://user:password@host:port/database"
DIRECT_URL="postgresql://user:password@host:port/database"
```

## 🗄️ Initialize Database

Once your database is configured:

```bash
# Push schema to database
npm run db:push

# (Optional) Open Drizzle Studio to view/edit data
npm run db:studio
```

## 🏃 Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5000` (automatically forwarded by Codespaces).

## 🔐 Environment Variables Reference

### Required Variables
- `NEXTAUTH_URL` - Your application URL (auto-generated for Codespaces)
- `NEXTAUTH_SECRET` - Secret for NextAuth.js session encryption (auto-generated)
- `DATABASE_URL` - PostgreSQL connection string
- `DIRECT_URL` - Direct PostgreSQL connection (for migrations)

### Optional Variables
- `NODE_ENV` - Environment (development/production)
- `PORT` - Application port (default: 5000)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth providers
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - OAuth providers
- `SENTRY_DSN` - Error monitoring
- `DB_POOL_SIZE` - Database connection pool size (default: 10)

## 🧪 Run Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## 🔍 Verify Setup

```bash
# Check TypeScript compilation
npm run check

# Lint code
npm run lint

# Build for production
npm run build
```

## 📝 Codespace Secrets

For sensitive data (API keys, OAuth secrets), use Codespace secrets instead of `.env.local`:

1. Go to your GitHub account settings
2. Navigate to "Codespaces" → "Secrets"
3. Add repository or organization secrets
4. Secrets are automatically available as environment variables

## 🐛 Troubleshooting

### Port 5000 Already in Use
```bash
# Change port in .env.local
PORT=3000

# Or kill the process
lsof -ti:5000 | xargs kill -9
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart services
docker-compose -f docker-compose.dev.yml restart postgres
```

### Module Not Found Errors
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### Three.js Bundling Issues
If you encounter Three.js bundling errors, use webpack instead of Turbopack:
```bash
npm run dev  # Already uses webpack by default
```

## 📚 Additional Resources

- [Project README](./README.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Production Checklist](./PRODUCTION_CHECKLIST.md)
- [Security Guidelines](./SECURITY.md)
- [TODO List](./TODO.md)

## 🆘 Need Help?

- Check existing issues on GitHub
- Review [SESSION_HANDOFF.md](./SESSION_HANDOFF.md) for known issues
- Create a new issue with the "question" label
