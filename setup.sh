#!/bin/bash

# Soccer Analytics Backend - Setup Script
# This script helps initialize the project for first-time setup

set -e

echo "🚀 Soccer Analytics Backend - Setup Script"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please review and update .env with your configuration"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Ask if user wants to start services
read -p "🤔 Do you want to build and start the services now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔨 Building Docker containers..."
    docker-compose build

    echo ""
    echo "🚀 Starting services..."
    docker-compose up -d

    echo ""
    echo "⏳ Waiting for database to be ready..."
    sleep 10

    echo ""
    echo "🔄 Running database migrations..."
    docker-compose exec -T api alembic upgrade head

    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "Services are running:"
    echo "  📡 API:          http://localhost:8000"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo "  📖 ReDoc:        http://localhost:8000/redoc"
    echo "  🌺 Flower:       http://localhost:5555"
    echo "  🗄️  PostgreSQL:   localhost:5432"
    echo "  🔴 Redis:        localhost:6379"
    echo ""
    echo "Useful commands:"
    echo "  View logs:       docker-compose logs -f"
    echo "  Stop services:   docker-compose down"
    echo "  Restart:         docker-compose restart"
    echo ""
    echo "Or use the Makefile:"
    echo "  make help        Show all available commands"
    echo "  make logs        View logs"
    echo "  make down        Stop services"
    echo ""
else
    echo ""
    echo "✅ Setup complete! Environment is ready."
    echo ""
    echo "To start the services manually, run:"
    echo "  docker-compose up -d"
    echo ""
    echo "Or use the Makefile:"
    echo "  make up"
    echo ""
fi

echo "📚 For more information, see README.md"
echo ""
echo "Happy coding! 🎉"
