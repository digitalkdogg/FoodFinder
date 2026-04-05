#!/bin/bash

# FoodFinder Web App Startup Script
# Starts the Next.js web application on port 3003

cd "$(dirname "$0")" || exit 1

echo "🍽️  Starting FoodFinder Web Application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if node_modules exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Generate Prisma Client if needed
if [ ! -d "node_modules/.prisma/client" ]; then
    echo "🔧 Generating Prisma Client..."
    npm run prisma:generate
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please ensure .env file exists with DATABASE_URL"
    exit 1
fi

# Start the server
echo "🚀 Starting server on port 3003..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Access the app at: http://localhost:3003"
echo ""
echo "Pages:"
echo "  🏠 Home:       http://localhost:3003/"
echo "  🔍 Search:     http://localhost:3003/search"
echo "  📂 Categories: http://localhost:3003/categories"
echo "  🏷️  Tags:      http://localhost:3003/tags"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PORT=3003 npm start
