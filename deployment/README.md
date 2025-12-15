# 📦 Deployment Files Overview

Your ACT bot now has complete Raspberry Pi deployment support.

## 🎯 Choose Your Deployment Method

### Option 1: Manual Deployment (Recommended to Start) ⭐

No OAuth required, simple and straightforward!

**Follow:** [MANUAL_DEPLOY.md](file:///home/comon/dev/comon/ACT/deployment/MANUAL_DEPLOY.md)

**Quick commands:**

```bash
ssh comon@pi4
git clone https://github.com/Comon-tech/ACT.git
cd ACT
nano .env  # Add your credentials
./deployment/setup-pi.sh
sudo systemctl start act-bot.service
```

### Option 2: Automated Deployment with GitHub Actions

Requires Tailscale OAuth setup, but enables automatic deployment on push.

**Follow:** [QUICK_START.md](file:///home/comon/dev/comon/ACT/deployment/QUICK_START.md)

## 📁 Documentation Files

```
deployment/
├── MANUAL_DEPLOY.md     # 👈 START HERE for manual deployment
├── ANSWERS.md           # Answers to your Tailscale/OAuth questions
├── QUICK_START.md       # Automated deployment (requires OAuth)
├── SSH_SETUP.md         # SSH key setup (for automated deployment)
├── DEPLOYMENT.md        # Complete reference guide
├── setup-pi.sh          # Automated setup script
└── act-bot.service      # Systemd service file
```

## ❓ Your Questions Answered

See [ANSWERS.md](file:///home/comon/dev/comon/ACT/deployment/ANSWERS.md) for detailed answers to:

- Will Tailscale affect other apps?
- Do I need OAuth?
- MongoDB Atlas setup

### 2. Set Up SSH Keys

Follow: **[deployment/SSH_SETUP.md](file:///home/comon/dev/comon/ACT/deployment/SSH_SETUP.md)**

**Quick version:**

```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/act-deploy

# Copy to Pi
ssh-copy-id -i ~/.ssh/act-deploy.pub comon@pi4

# Test it
ssh -i ~/.ssh/act-deploy comon@pi4
```

### 3. Get Information for GitHub Secrets

```bash
# Get Pi's Tailscale IP
ssh comon@pi4 "tailscale ip -4"
# Example output: 100.123.45.67

# Get private key content
cat ~/.ssh/act-deploy
# Copy the entire output
```

### 4. Create Tailscale OAuth Client

1. Go to: https://login.tailscale.com/admin/settings/oauth
2. Click "Generate OAuth Client"
3. Add tag: `tag:ci`
4. Save the Client ID and Secret

### 5. Add GitHub Secrets

Go to: https://github.com/Comon-tech/ACT/settings/secrets/actions

Add these 5 secrets:

| Name                 | Value                                        |
| -------------------- | -------------------------------------------- |
| `PI_HOST`            | Your Tailscale IP (100.x.x.x)                |
| `PI_USER`            | `comon`                                      |
| `PI_SSH_KEY`         | Content of `~/.ssh/act-deploy` (private key) |
| `TS_OAUTH_CLIENT_ID` | From Tailscale OAuth                         |
| `TS_OAUTH_SECRET`    | From Tailscale OAuth                         |

### 6. Run Setup on Your Pi

```bash
ssh comon@pi4
cd ~
git clone https://github.com/Comon-tech/ACT.git
cd ACT
chmod +x deployment/setup-pi.sh
./deployment/setup-pi.sh
```

### 7. Configure Environment Variables

```bash
nano /home/comon/ACT/.env
```

Add your actual values:

- `DISCORD_BOT_TOKEN`
- `GEMINI_AI_API_KEY`

### 8. Start the Bot

```bash
sudo systemctl start act-bot.service
sudo systemctl status act-bot.service
```

### 9. Test Automated Deployment

Push to the `main` branch and watch GitHub Actions deploy automatically!

## 📚 Documentation Summary

- **[QUICK_START.md](file:///home/comon/dev/comon/ACT/deployment/QUICK_START.md)** - Start here! Condensed guide
- **[SSH_SETUP.md](file:///home/comon/dev/comon/ACT/deployment/SSH_SETUP.md)** - Detailed SSH key setup
- **[DEPLOYMENT.md](file:///home/comon/dev/comon/ACT/deployment/DEPLOYMENT.md)** - Complete reference guide

## 🔑 Key Points

✅ **Port 8001** - Changed from 8000 to avoid conflicts  
✅ **Tailscale VPN** - Secure, no port forwarding needed  
✅ **SSH Keys** - Different from GitHub access tokens  
✅ **Auto-Deploy** - Push to main = automatic deployment  
✅ **Systemd Service** - Bot runs as background service

## ❓ Questions Answered

**Q: What's the difference between GitHub token and SSH key?**  
A: GitHub token is for API/git operations. SSH key is for server access. See [SSH_SETUP.md](file:///home/comon/dev/comon/ACT/deployment/SSH_SETUP.md)

**Q: How do I add the public key to Pi?**  
A: `ssh-copy-id -i ~/.ssh/act-deploy.pub comon@pi4`

**Q: How do I add the private key as a GitHub secret?**  
A: Copy content of `~/.ssh/act-deploy` and paste into GitHub repo secrets

**Q: Can VPN work for deployment?**  
A: Yes! Your Tailscale setup is perfect. No port forwarding needed.

## 🆘 Getting Help

If stuck, check:

1. [QUICK_START.md](file:///home/comon/dev/comon/ACT/deployment/QUICK_START.md) troubleshooting section
2. [DEPLOYMENT.md](file:///home/comon/dev/comon/ACT/deployment/DEPLOYMENT.md) detailed troubleshooting
3. GitHub Actions logs (Actions tab in repo)
4. Bot logs: `sudo journalctl -u act-bot.service -f`
