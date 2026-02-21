#!/bin/bash
set -e

echo "🔐 IHEP Platform - Secret Generation"
echo "===================================="
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "❌ Error: openssl is not installed"
    echo "Please install openssl and try again"
    exit 1
fi

# Generate NEXTAUTH_SECRET
echo "Generating NEXTAUTH_SECRET..."
NEXTAUTH_SECRET=$(openssl rand -base64 32)

# Check if .env.local exists
if [ -f .env.local ]; then
    echo ""
    echo "⚠️  .env.local already exists"
    read -p "Do you want to update NEXTAUTH_SECRET? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update existing file
        if grep -q "NEXTAUTH_SECRET=" .env.local; then
            sed -i.bak "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=\"$NEXTAUTH_SECRET\"|g" .env.local
            rm .env.local.bak 2>/dev/null || true
            echo "✅ Updated NEXTAUTH_SECRET in .env.local"
        else
            echo "NEXTAUTH_SECRET=\"$NEXTAUTH_SECRET\"" >> .env.local
            echo "✅ Added NEXTAUTH_SECRET to .env.local"
        fi
    else
        echo "Skipped updating .env.local"
    fi
else
    # Create new file from template
    if [ -f .env.example ]; then
        cp .env.example .env.local
        sed -i.bak "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=\"$NEXTAUTH_SECRET\"|g" .env.local
        rm .env.local.bak 2>/dev/null || true
        echo "✅ Created .env.local with generated NEXTAUTH_SECRET"
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

echo ""
echo "📋 Generated Secrets:"
echo "===================="
echo "NEXTAUTH_SECRET=\"$NEXTAUTH_SECRET\""
echo ""
echo "🔒 Keep these secrets secure!"
echo ""
echo "📝 Next Steps:"
echo "1. Update DATABASE_URL in .env.local with your database connection"
echo "2. Add any OAuth provider secrets (GOOGLE_CLIENT_ID, etc.)"
echo "3. Never commit .env.local to version control"
echo ""
echo "For GCP Cloud Run deployment, add secrets using:"
echo "gcloud secrets create nextauth-secret --data-file=- <<< \"$NEXTAUTH_SECRET\""
