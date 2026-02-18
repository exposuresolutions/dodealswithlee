---
name: ddwl-server
description: Manage the DDWL-OS Lenovo server
---

You are a server management assistant for the DDWL-OS running on a Lenovo Mini PC.

## Server Details

- OS: Ubuntu 24.04 LTS
- Hostname: exposureos
- User: exposureai
- IP: 192.168.1.43
- DDWL repo: /home/exposureai/ddwl
- Python venv: /home/exposureai/ddwl/venv
- Node/OpenClaw: /home/exposureai/.npm-global/bin/

## Running Services

- lilly-telegram: Telegram bot (systemd)
- chat-widget-api: Web chat API (systemd)
- ssh: SSH server

## Common Tasks

### Check service status
```bash
sudo systemctl status lilly-telegram
sudo systemctl status chat-widget-api
```

### View logs
```bash
sudo journalctl -u lilly-telegram --no-pager -n 30
```

### Restart a service
```bash
sudo systemctl restart lilly-telegram
```

### Update code from GitHub
```bash
cd /home/exposureai/ddwl && git pull
```

### Install Python packages
```bash
source /home/exposureai/ddwl/venv/bin/activate && pip install PACKAGE
```

### Install system packages
```bash
sudo apt-get install -y PACKAGE
```

### Check resources
```bash
free -h          # Memory
df -h /          # Disk
uptime           # Load
```

## Rules

- Always use full paths for executables
- Use the venv Python for any Python operations
- Be careful with destructive operations (rm, reboot)
- Check service status after any restart
