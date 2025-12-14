# SSH Timeout Prevention - Configuration Guide

## ✅ What Was Configured

I've added anti-timeout settings to your `~/.ssh/config` file. This will prevent SSH connections from timing out.

### Settings Explained:

- **`ServerAliveInterval 60`**: Sends a keepalive message every 60 seconds
- **`ServerAliveCountMax 3`**: Allows 3 failed keepalive attempts before disconnecting
- **`TCPKeepAlive yes`**: Enables TCP-level keepalive packets
- **`Compression yes`**: Enables compression (faster transfers)
- **`ControlMaster auto`**: Enables connection multiplexing (reuses connections)
- **`ControlPersist 10m`**: Keeps master connection alive for 10 minutes after last use

## 🚀 How to Use

### Option 1: Use the Host Alias (Recommended)
```bash
ssh namo-server
```

### Option 2: Use IP Address (Still Works)
```bash
ssh -p 2111 frede@212.27.13.34
```

Both will now use the anti-timeout settings automatically!

## 🔧 Alternative: Command-Line Options

If you prefer not to use the config file, you can add these flags directly:

```bash
ssh -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o TCPKeepAlive=yes \
    -p 2111 frede@212.27.13.34
```

## 📝 Quick Commands

### Connect to server:
```bash
ssh namo-server
```

### Run commands remotely:
```bash
ssh namo-server "cd /home/frede/NAMO_nov25 && ls -la"
```

### Start tmux session remotely:
```bash
ssh namo-server "tmux new-session -d -s nlp_processing 'cd /home/frede/NAMO_nov25 && python3 scripts/02_nlp_processing_from_db.py --total-articles 200 --chunk-size 50 --model mistralai/Mistral-7B-Instruct-v0.3'"
```

### Check tmux session:
```bash
ssh namo-server "tmux capture-pane -t nlp_processing -p | tail -30"
```

## 🛠️ Server-Side Configuration (Optional)

If you have server admin access, you can also configure the SSH server to prevent timeouts:

Edit `/etc/ssh/sshd_config` on the server:
```
ClientAliveInterval 60
ClientAliveCountMax 3
TCPKeepAlive yes
```

Then restart SSH: `sudo systemctl restart sshd`

## ✅ Test the Connection

Try connecting now:
```bash
ssh namo-server
```

The connection should stay alive much longer now!


