#!/bin/bash
set -e

echo "🚀 Setting up IHEP Platform development environment..."

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
  echo "📝 Creating .env.local from .env.example..."
  cp .env.example .env.local
  
  # Generate NEXTAUTH_SECRET if needed
  if command -v openssl &> /dev/null; then
    echo "🔐 Generating NEXTAUTH_SECRET..."
    NEXTAUTH_SECRET=$(openssl rand -base64 32)
    sed -i "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=\"$NEXTAUTH_SECRET\"|g" .env.local
  fi
  
  echo "⚠️  Please update DATABASE_URL in .env.local with your database connection string"
fi

# Check TypeScript compilation
echo "🔍 Checking TypeScript..."
npm run check || echo "⚠️  TypeScript check failed - review errors above"

# Run tests
echo "🧪 Running tests..."
npm test || echo "⚠️  Some tests failed - review errors above"

echo "✅ Setup complete! Run 'npm run dev' to start the development server"
echo ""
echo "📚 Next steps:"
echo "  1. Update DATABASE_URL in .env.local"
echo "  2. Run 'npm run db:push' to sync database schema"
echo "  3. Run 'npm run dev' to start the development server"
echo "  4. Open http://localhost:5000 in your browser"
