# SSH Key Setup Guide for ACT Deployment

This guide will walk you through setting up SSH keys for automated deployment from GitHub Actions to your Raspberry Pi via Tailscale.

## 🔐 Understanding SSH Keys vs GitHub Tokens

**GitHub Access Token** (what you have):

- Used for authenticating to GitHub API
- Used for git operations (clone, push, pull)
- Works over HTTPS

**SSH Key Pair** (what we need):

- Used for secure shell access to servers
- A pair of files: private key (secret) + public key (can share)
- GitHub Actions will use this to SSH into your Pi

## 📋 Step-by-Step Guide

### Step 1: Generate SSH Key Pair

On your **local machine** (not the Pi), open a terminal and run:

```bash
# Generate a new SSH key specifically for deployments
ssh-keygen -t ed25519 -f ~/.ssh/act-deploy -C "act-github-deployment"
```

When prompted:

- **"Enter passphrase"**: Just press Enter (leave empty for automated deployment)
- **"Enter same passphrase again"**: Press Enter again

This creates two files:

- `~/.ssh/act-deploy` - **Private key** (keep secret!)
- `~/.ssh/act-deploy.pub` - **Public key** (safe to share)

### Step 2: Add Public Key to Your Raspberry Pi

Copy the public key to your Pi's authorized keys:

```bash
# Method 1: Automatic (recommended)
ssh-copy-id -i ~/.ssh/act-deploy.pub comon@pi4

# Method 2: Manual if ssh-copy-id doesn't work
cat ~/.ssh/act-deploy.pub | ssh comon@pi4 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### Step 3: Test SSH Connection

Verify the key works:

```bash
ssh -i ~/.ssh/act-deploy comon@pi4
```

If you can log in without a password, it's working! Type `exit` to disconnect.

### Step 4: Get Tailscale IP Address

On your **Raspberry Pi**, find its Tailscale IP:

```bash
# SSH into your Pi
ssh comon@pi4

# Get Tailscale IP (usually starts with 100.x.x.x)
tailscale ip -4
```

Save this IP address - you'll need it for GitHub secrets.

### Step 5: Add Private Key to GitHub Secrets

1. **Copy the private key content**:

   ```bash
   # On your local machine
   cat ~/.ssh/act-deploy
   ```

   Copy the **entire output** (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

2. **Go to GitHub**:

   - Navigate to https://github.com/Comon-tech/ACT
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**

3. **Add these secrets**:

   | Name                 | Value               | Description                        |
   | -------------------- | ------------------- | ---------------------------------- |
   | `PI_HOST`            | `100.x.x.x`         | Your Pi's Tailscale IP from Step 4 |
   | `PI_USER`            | `comon`             | Your username on the Pi            |
   | `PI_SSH_KEY`         | [paste private key] | The private key content from above |
   | `TAILSCALE_AUTH_KEY` | [see below]         | Tailscale authentication key       |

4. **Get Tailscale Auth Key**:
   - Go to https://login.tailscale.com/admin/settings/keys
   - Click **Generate auth key**
   - Check: ✅ **Reusable** and ✅ **Ephemeral**
   - Copy the key and add it as `TAILSCALE_AUTH_KEY` secret

## ✅ Verification

After setting up all secrets, the next push to the `main` branch will trigger automatic deployment!

## 🔒 Security Notes

- ✅ Private key never leaves your machine or GitHub's secure vault
- ✅ Tailscale provides encrypted tunnel - no exposed SSH port
- ✅ Keys are separate from your personal SSH keys
- ✅ You can revoke keys anytime from GitHub or regenerate them

## 🆘 Troubleshooting

**"Permission denied (publickey)"**

```bash
# Make sure permissions are correct on Pi
ssh comon@pi4
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

**"Host key verification failed"**

```bash
# Add Pi's Tailscale IP to known hosts
ssh-keyscan -H 100.x.x.x >> ~/.ssh/known_hosts
```

**Test from GitHub Actions side**

- Check GitHub Actions logs under "Actions" tab
- Look for SSH connection errors
- Verify Tailscale is connected during deployment
