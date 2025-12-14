# SSH Connection Troubleshooting

## Current Issue: SSH Connection Timeout

If `ssh -p 2111 frede@212.27.13.34` is timing out, this is typically a **network/firewall issue**, not a server problem.

## 🔍 Diagnostic Steps

### 1. Test Basic Connectivity
```bash
# Test if the server is reachable
ping -c 4 212.27.13.34

# Test if port 2111 is open
nc -zv -w 5 212.27.13.34 2111
# OR
telnet 212.27.13.34 2111
```

### 2. Check Your Network
- Are you on a different network than usual?
- Is there a VPN that needs to be connected?
- Is there a firewall blocking outbound connections on port 2111?

### 3. Try Different Connection Methods
```bash
# Try with verbose output to see where it fails
ssh -vvv -p 2111 frede@212.27.13.34

# Try with different timeout settings
ssh -o ConnectTimeout=30 -p 2111 frede@212.27.13.34
```

## 🔄 Server Restart Options

### Option 1: Cloud Provider Console
If this is a cloud server (AWS, DigitalOcean, etc.):
1. Log into your cloud provider's web console
2. Find the server instance
3. Use the "Reboot" or "Restart" option

### Option 2: Physical/Console Access
If you have physical access or console access:
- Use the server's physical console
- Or use a KVM/IPMI interface if available

### Option 3: Contact Server Admin
If you don't have direct access, contact whoever manages the server.

## 🛠️ Alternative: Check if Server is Actually Down

The timeout might mean:
- Server is powered off
- Network routing issue
- Firewall blocking the connection
- Server crashed/hung

## 📝 What to Check After Restart

Once you can connect again:

1. **Check SSH service:**
   ```bash
   sudo systemctl status sshd
   ```

2. **Check server resources:**
   ```bash
   free -h
   df -h
   nvidia-smi  # Check GPU
   ```

3. **Check system logs:**
   ```bash
   sudo journalctl -u sshd -n 50
   ```

## 🚀 Quick Test Script

Save this as `test_connection.sh`:

```bash
#!/bin/bash
echo "Testing connection to 212.27.13.34:2111..."
if timeout 5 nc -zv 212.27.13.34 2111 2>&1 | grep -q "succeeded"; then
    echo "✅ Port 2111 is open"
    echo "Trying SSH connection..."
    ssh -o ConnectTimeout=10 -p 2111 frede@212.27.13.34 "echo 'Connection successful!'"
else
    echo "❌ Port 2111 is not reachable"
    echo "This could mean:"
    echo "  - Server is down"
    echo "  - Firewall is blocking"
    echo "  - Network routing issue"
fi
```

Run it: `chmod +x test_connection.sh && ./test_connection.sh`


