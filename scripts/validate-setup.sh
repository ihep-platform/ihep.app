#!/bin/bash
set -e

echo "🔍 IHEP Platform - Setup Validation"
echo "===================================="
echo ""

ERRORS=0
WARNINGS=0

# Check Node.js
echo -n "Checking Node.js version... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        echo "✅ $(node -v)"
    else
        echo "❌ Node.js $NODE_VERSION is too old (need 18+)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ Node.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    echo "✅ $(npm -v)"
else
    echo "❌ npm not found"
    ERRORS=$((ERRORS + 1))
fi

# Check for node_modules
echo -n "Checking dependencies... "
if [ -d "node_modules" ]; then
    echo "✅ node_modules exists"
else
    echo "⚠️  node_modules not found (run 'npm install')"
    WARNINGS=$((WARNINGS + 1))
fi

# Check .env.local
echo -n "Checking environment file... "
if [ -f ".env.local" ]; then
    echo "✅ .env.local exists"
    
    # Check for required variables
    if grep -q "NEXTAUTH_SECRET=\"[^\"]*\"" .env.local && ! grep -q "NEXTAUTH_SECRET=\"N+aRfo7PfWjhy/BkovWOHCBjVqYlCL/I/r4JtIrKUFA=\"" .env.local; then
        echo "  ✅ NEXTAUTH_SECRET is set"
    else
        echo "  ⚠️  NEXTAUTH_SECRET not updated (run 'bash scripts/generate-secrets.sh')"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if grep -q "DATABASE_URL=postgresql://" .env.local && ! grep -q "DATABASE_URL=postgresql://user:password@host:port/database" .env.local; then
        echo "  ✅ DATABASE_URL is configured"
    else
        echo "  ⚠️  DATABASE_URL needs to be updated"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "❌ .env.local not found (run 'bash scripts/generate-secrets.sh')"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    echo "✅ $(docker --version | cut -d',' -f1)"
    
    # Check if PostgreSQL container is running
    if docker ps | grep -q "ihep-postgres-dev\|postgres"; then
        echo "  ✅ PostgreSQL container is running"
    else
        echo "  ℹ️  PostgreSQL container not running (run 'docker-compose -f docker-compose.dev.yml up -d')"
    fi
else
    echo "ℹ️  Docker not found (optional for local development)"
fi

# Check Git
echo -n "Checking Git... "
if command -v git &> /dev/null; then
    echo "✅ $(git --version | cut -d' ' -f1-3)"
else
    echo "⚠️  Git not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Check TypeScript
echo -n "Checking TypeScript... "
if [ -d "node_modules" ] && [ -f "node_modules/.bin/tsc" ]; then
    echo "✅ TypeScript installed"
else
    echo "⚠️  TypeScript not found (run 'npm install')"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for build directory
echo -n "Checking build artifacts... "
if [ -d ".next" ]; then
    echo "✅ .next directory exists"
else
    echo "ℹ️  No build found (run 'npm run build' to create production build)"
fi

# Summary
echo ""
echo "===================================="
echo "Summary:"
echo "  ✅ Passed: $((7 - ERRORS - WARNINGS))"
echo "  ⚠️  Warnings: $WARNINGS"
echo "  ❌ Errors: $ERRORS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ Setup validation failed. Please fix the errors above."
    echo ""
    echo "Quick fixes:"
    echo "  - Install Node.js 18+: https://nodejs.org/"
    echo "  - Run 'npm install' to install dependencies"
    echo "  - Run 'bash scripts/generate-secrets.sh' to create .env.local"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  Setup has warnings but should work."
    echo ""
    echo "Recommended actions:"
    [ ! -d "node_modules" ] && echo "  - Run 'npm install'"
    [ ! -f ".env.local" ] && echo "  - Run 'bash scripts/generate-secrets.sh'"
    grep -q "DATABASE_URL=postgresql://user:password@host:port/database" .env.local 2>/dev/null && echo "  - Update DATABASE_URL in .env.local"
    echo ""
    echo "To start development:"
    echo "  1. docker-compose -f docker-compose.dev.yml up -d"
    echo "  2. npm run db:push"
    echo "  3. npm run dev"
    exit 0
else
    echo "✅ All checks passed! Your setup looks good."
    echo ""
    echo "To start development:"
    echo "  1. docker-compose -f docker-compose.dev.yml up -d  (if not already running)"
    echo "  2. npm run db:push  (first time only)"
    echo "  3. npm run dev"
    echo ""
    echo "Your app will be available at http://localhost:5000"
    exit 0
fi
