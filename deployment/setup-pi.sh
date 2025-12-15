#!/bin/bash
# Initial setup script for deploying ACT bot on Raspberry Pi 4

set -e

echo "🚀 ACT Bot - Raspberry Pi Setup Script"
echo "========================================"

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

APP_DIR="/home/comon/ACT"
REPO_URL="https://github.com/Comon-tech/ACT.git"

echo ""
echo "📦 Step 1: Installing UV package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ UV installed successfully"
else
    echo "✅ UV already installed"
fi

echo ""
echo "📂 Step 2: Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    git clone "$REPO_URL" .
    echo "✅ Repository cloned"
else
    echo "✅ Directory already exists"
    cd "$APP_DIR"
fi

echo ""
echo "🔧 Step 3: Installing dependencies..."
uv sync
echo "✅ Dependencies installed"

echo ""
echo "📝 Step 4: Setting up environment variables..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'EOF'
# ACT Bot Environment Variables
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_AI_API_KEY=your_gemini_api_key_here

# MongoDB Connection URI
# For MongoDB Atlas (cloud):
MONGO_DB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
# For local MongoDB (if you have it installed):
# MONGO_DB_URI=mongodb://localhost:1717

APP_SERVER_URL=http://localhost:8001
EOF
    echo "✅ Created .env file - PLEASE EDIT IT WITH YOUR ACTUAL VALUES"
    echo "   Location: $APP_DIR/.env"
    echo ""
    echo "⚠️  IMPORTANT: You must configure your MongoDB connection!"
    echo "   - If using MongoDB Atlas, update MONGO_DB_URI with your connection string"
    echo "   - If using local MongoDB, install it first and update the URI"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔌 Step 6: Setting up systemd service..."
sudo cp "$APP_DIR/deployment/act-bot.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable act-bot.service
echo "✅ Service installed and enabled"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit environment variables: nano $APP_DIR/.env"
echo "   2. Make sure your MongoDB Atlas cluster is accessible"
echo "   3. Start the bot: sudo systemctl start act-bot.service"
echo "   4. Check status: sudo systemctl status act-bot.service"
echo "   5. View logs: sudo journalctl -u act-bot.service -f"
echo ""
echo "🔐 For GitHub Actions deployment:"
echo "   Add these secrets to your GitHub repository:"
echo "   - PI_HOST: Your Pi's hostname/IP (e.g., pi4.local or your public IP)"
echo "   - PI_USER: comon"
echo "   - PI_SSH_KEY: Your SSH private key for deployment"
