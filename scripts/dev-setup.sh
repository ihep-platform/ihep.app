#!/bin/bash
set -e

echo "🚀 IHEP Platform - Development Setup"
echo "====================================="
echo ""

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js version 18 or higher is required"
    echo "Current version: $(node -v)"
    exit 1
fi
echo "✅ Node.js $(node -v) detected"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Generate secrets if .env.local doesn't exist
if [ ! -f .env.local ]; then
    echo ""
    echo "🔐 Setting up environment variables..."
    bash scripts/generate-secrets.sh
else
    echo ""
    echo "✅ .env.local already exists"
fi

# Run TypeScript check
echo ""
echo "🔍 Checking TypeScript..."
npm run check || echo "⚠️  TypeScript check failed (non-blocking)"

# Run tests
echo ""
echo "🧪 Running tests..."
npm test || echo "⚠️  Some tests failed (non-blocking)"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo ""
    echo "🐳 Docker detected"
    read -p "Do you want to start PostgreSQL and Redis with Docker Compose? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        docker-compose -f docker-compose.dev.yml up -d
        echo "✅ PostgreSQL and Redis started"
        echo ""
        echo "📝 Update your .env.local with:"
        echo 'DATABASE_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"'
        echo 'DIRECT_URL="postgresql://ihep:ihep_dev_password@localhost:5432/ihep_db"'
    fi
else
    echo ""
    echo "ℹ️  Docker not detected - you'll need to provide your own database"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Update DATABASE_URL in .env.local"
echo "  2. Run 'npm run db:push' to sync database schema"
echo "  3. Run 'npm run dev' to start the development server"
echo "  4. Open http://localhost:5000 in your browser"
echo ""
echo "📖 For more information, see:"
echo "  - CODESPACES_SETUP.md"
echo "  - README.md"
echo "  - QUICK_START.md"
