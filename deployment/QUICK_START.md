# 🚀 Quick Start: Deploy ACT to Raspberry Pi

This is your condensed guide to deploying the ACT bot to your Raspberry Pi via Tailscale.

## One-Time Setup (Do These Once)

### 1. Generate SSH Key for Deployment

```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/act-deploy -C "act-deployment"
# Press Enter twice (no passphrase)

# Copy to your Pi
ssh-copy-id -i ~/.ssh/act-deploy.pub comon@pi4
```

### 2. Get Your Pi's Tailscale IP

```bash
ssh comon@pi4 "tailscale ip -4"
# Save this IP (e.g., 100.x.x.x)
```

### 3. Create Tailscale OAuth Client

1. Go to: https://login.tailscale.com/admin/settings/oauth
2. Click **Generate OAuth Client**
3. Add tag: `tag:ci`
4. Save the **Client ID** and **Secret**

### 4. Add GitHub Secrets

Go to: https://github.com/Comon-tech/ACT/settings/secrets/actions/new

Add these 5 secrets:

| Name                 | Value                                |
| -------------------- | ------------------------------------ |
| `PI_HOST`            | Your Tailscale IP from step 2        |
| `PI_USER`            | `comon`                              |
| `PI_SSH_KEY`         | Paste content of `~/.ssh/act-deploy` |
| `TS_OAUTH_CLIENT_ID` | From step 3                          |
| `TS_OAUTH_SECRET`    | From step 3                          |

### 5. Run Initial Setup on Pi

```bash
# SSH into your Pi
ssh comon@pi4

# Clone and run setup
cd ~
git clone https://github.com/Comon-tech/ACT.git
cd ACT
chmod +x deployment/setup-pi.sh
./deployment/setup-pi.sh

# Edit environment variables
nano .env
# Add your DISCORD_BOT_TOKEN and GEMINI_AI_API_KEY

# Start the bot
sudo systemctl start act-bot.service
sudo systemctl status act-bot.service
```

## ✅ You're Done!

Now every time you push to `main` branch, GitHub Actions will automatically:

1. Connect to your Pi via Tailscale
2. Pull latest code
3. Restart the bot service

## 📋 Common Commands

```bash
# View bot logs
sudo journalctl -u act-bot.service -f

# Restart bot
sudo systemctl restart act-bot.service

# Check status
sudo systemctl status act-bot.service
```

## 🆘 Troubleshooting

**Bot won't start?**

```bash
# Check what went wrong
sudo journalctl -u act-bot.service -n 50 --no-pager
```

**GitHub Actions failing?**

- Check Actions tab in GitHub repo
- Verify all 5 secrets are set correctly
- Make sure Tailscale is running on Pi: `tailscale status`

---

For detailed documentation, see [DEPLOYMENT.md](./DEPLOYMENT.md) and [SSH_SETUP.md](./SSH_SETUP.md)
