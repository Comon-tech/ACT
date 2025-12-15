# ACT Bot Deployment Guide - Raspberry Pi 4

This guide covers deploying the ACT Discord bot to a Raspberry Pi 4 home server.

## 📋 Prerequisites

- Raspberry Pi 4 (ideally 4GB+ RAM)
- Raspbian/Raspberry Pi OS installed
- Internet connection
- SSH access configured
- GitHub repository access

## 🔐 SSH & Tailscale Setup for GitHub Actions

> [!NOTE] > **You already have Tailscale working!** Since you can `ssh comon@pi4` from different networks, we just need to set up GitHub Actions to use it too.

### Quick Setup Steps

Follow the detailed guide: [SSH_SETUP.md](./SSH_SETUP.md)

**TL;DR:**

1. Generate SSH key: `ssh-keygen -t ed25519 -f ~/.ssh/act-deploy`
2. Copy to Pi: `ssh-copy-id -i ~/.ssh/act-deploy.pub comon@pi4`
3. Get Pi's Tailscale IP: `ssh comon@pi4 "tailscale ip -4"`
4. Set up GitHub secrets (see below)

### Required GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret Name          | How to Get                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `PI_HOST`            | Run on Pi: `tailscale ip -4` (will be like `100.x.x.x`)                                             |
| `PI_USER`            | `comon`                                                                                             |
| `PI_SSH_KEY`         | Content of `~/.ssh/act-deploy` (private key)                                                        |
| `TS_OAUTH_CLIENT_ID` | [Tailscale OAuth](https://login.tailscale.com/admin/settings/oauth) → Create OAuth client → Copy ID |
| `TS_OAUTH_SECRET`    | Same OAuth client → Copy Secret                                                                     |

> [!TIP] > **Creating Tailscale OAuth Client:**
>
> 1. Go to https://login.tailscale.com/admin/settings/oauth
> 2. Click **Generate OAuth Client**
> 3. Add tag: `tag:ci`
> 4. Copy the Client ID and Secret to GitHub secrets

## 🚀 Initial Setup

### 1. Run Setup Script

SSH into your Pi and run:

```bash
cd ~
git clone https://github.com/Comon-tech/ACT.git
cd ACT
chmod +x deployment/setup-pi.sh
./deployment/setup-pi.sh
```

### 2. Configure Environment Variables

Edit the `.env` file with your actual values:

```bash
nano /home/comon/ACT/.env
```

Required variables:

```env
DISCORD_BOT_TOKEN=your_actual_bot_token
GEMINI_AI_API_KEY=your_actual_gemini_key
MONGO_DB_URI=mongodb atlas uri
APP_SERVER_URL=http://localhost:8001
```

> [!NOTE] > **Port 8001** is used instead of 8000 to avoid conflict with your other app.

### 3. Start MongoDB

```bash
# Start MongoDB service
sudo systemctl start mongodb

# Enable MongoDB to start on boot
sudo systemctl enable mongodb
```

### 4. Start the Bot

```bash
# Start the service
sudo systemctl start act-bot.service

# Check status
sudo systemctl status act-bot.service

# View logs
sudo journalctl -u act-bot.service -f
```

## 🔄 Manual Deployment

To manually deploy updates:

```bash
cd /home/comon/ACT
git pull origin main
sudo systemctl restart act-bot.service
```

## 📊 Service Management

```bash
# Start the bot
sudo systemctl start act-bot.service

# Stop the bot
sudo systemctl stop act-bot.service

# Restart the bot
sudo systemctl restart act-bot.service

# Check status
sudo systemctl status act-bot.service

# View logs (live)
sudo journalctl -u act-bot.service -f

# View last 100 lines of logs
sudo journalctl -u act-bot.service -n 100
```

## 🔧 Troubleshooting

### Bot won't start

1. Check logs:

   ```bash
   sudo journalctl -u act-bot.service -n 50
   ```

2. Verify environment variables:

   ```bash
   cat /home/comon/ACT/.env
   ```

3. Test manually:
   ```bash
   cd /home/comon/ACT
   uv run python main.py --bot --db
   ```

### MongoDB connection issues

```bash
# Check MongoDB status
sudo systemctl status mongodb

# Check if MongoDB is listening
sudo netstat -tlnp | grep 1717

# Start MongoDB if not running
sudo systemctl start mongodb
```

### Port conflict

If port 8001 is also taken, edit `.env` and change `APP_SERVER_URL`:

```env
APP_SERVER_URL=http://localhost:8002
```

Then restart the service.

### GitHub Actions can't connect

1. Verify Tailscale is running on Pi:

   ```bash
   ssh comon@pi4 "tailscale status"
   ```

2. Verify you're using the correct Tailscale IP in `PI_HOST` secret:

   ```bash
   ssh comon@pi4 "tailscale ip -4"
   ```

3. Check GitHub Actions logs for specific errors

4. Test SSH connection with the deployment key:

   ```bash
   ssh -i ~/.ssh/act-deploy comon@TAILSCALE_IP
   ```

5. Verify Tailscale OAuth credentials are correct in GitHub secrets

## 🔒 Security Recommendations

1. **Use Tailscale** ✅ (you're already doing this!)
2. **Use SSH keys only** (disable password authentication)
3. **Keep system updated**: `sudo apt update && sudo apt upgrade`
4. **Monitor logs regularly**: `sudo journalctl -u act-bot.service -f`
5. **Rotate SSH keys periodically** (regenerate deployment keys every few months)

## 📝 Notes

- The bot will automatically restart on system boot
- Logs are managed by systemd journal
- MongoDB data is stored in the default location
- The API component is optional (only needed for web integrations)
