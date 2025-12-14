# Network Connection Troubleshooting

## Current Situation

**Problem:** All SSH ports (22, 2111, 2222) are timing out  
**Server:** 212.27.13.34  
**Status:** "Operation timed out" (not "Connection refused")

This means packets aren't reaching the server or responses aren't coming back.

---

## 🔍 Quick Diagnostics

### 1. Test Basic Network Connectivity
```bash
# Test if the server IP is reachable at all
ping -c 5 212.27.13.34

# Test DNS (if using a hostname)
nslookup 212.27.13.34

# Check your current public IP
curl -s ifconfig.me
```

### 2. Check What Changed
- ✅ You were able to connect earlier and saw Ubuntu welcome message
- ❌ Now all connections time out

**Possible causes:**
- Your network changed (WiFi, VPN disconnected, etc.)
- Server's network/firewall configuration changed
- ISP or intermediate firewall blocking
- Server is down/unreachable

---

## 🌐 Network Change Checklist

### Check Your Network
```bash
# See your current network interface
ifconfig | grep "inet " | grep -v 127.0.0.1

# Check if you're on VPN
ifconfig | grep -i tun
ifconfig | grep -i vpn

# Check routing
netstat -rn | grep default
```

### Questions to Ask:
- [ ] Are you on the same WiFi/network as when it last worked?
- [ ] Did you disconnect from a VPN?
- [ ] Is there a corporate/university firewall?
- [ ] Did you change locations?
- [ ] Is your internet connection stable?

---

## 🛠️ Troubleshooting Steps

### Option 1: Try Different Network
```bash
# Test from mobile hotspot
# Connect to your phone's hotspot, then try:
ssh -p 2111 frede@212.27.13.34

# Test from different WiFi
# Connect to a different network and try again
```

### Option 2: Check Server Status (Alternative Methods)

**If you have server console access:**
- Cloud provider web console (AWS, DigitalOcean, etc.)
- Physical console
- IPMI/KVM interface

**If you have monitoring tools:**
- Check uptime monitoring (UptimeRobot, Pingdom, etc.)
- Check cloud provider status dashboard
- Check if other services on the server are responding

### Option 3: Check Firewall Rules

**On your local machine:**
```bash
# Check if outbound connections are blocked
sudo lsof -i :2111

# Try telnet (might be blocked by firewall)
telnet 212.27.13.34 2111
```

**On the server (if you have console access):**
```bash
# Check SSH is running
sudo systemctl status sshd

# Check firewall rules
sudo ufw status
sudo iptables -L -n | grep 2111

# Check if SSH is listening
sudo netstat -tlnp | grep :2111
```

---

## 🚨 Emergency: Alternative Access Methods

### 1. Cloud Provider Web Console
Most cloud providers offer web-based console access:
- **AWS:** EC2 → Instances → Connect → Session Manager
- **DigitalOcean:** Droplets → Access → Console
- **Google Cloud:** Compute Engine → VM instances → SSH → Open in browser
- **Azure:** Virtual Machines → Connect → Bastion

### 2. VPN/Bastion Host
If server is behind VPN:
```bash
# Connect to VPN first
# Then try SSH
```

If there's a bastion/jump host:
```bash
ssh -J bastion-user@bastion-host frede@212.27.13.34 -p 2111
```

---

## 📊 Network Path Diagnostics

### Traceroute to Server
```bash
# See where packets are getting stuck
traceroute 212.27.13.34

# macOS alternative
traceroute -I 212.27.13.34
```

### MTR (My TraceRoute) - More Detailed
```bash
# Install mtr if not available: brew install mtr
sudo mtr -c 10 212.27.13.34
```

---

## ✅ Once Connection Works Again

### Document What Fixed It
Note which of these worked:
- [ ] Changed network (WiFi, mobile hotspot, etc.)
- [ ] Connected to VPN
- [ ] Server was rebooted
- [ ] Firewall rule was changed
- [ ] Port forwarding was fixed
- [ ] Just waited and it started working

### Prevent Future Issues
1. **Set up VPN** (if not already):
   - Tailscale (easiest)
   - WireGuard
   - OpenVPN

2. **Set up monitoring**:
   - UptimeRobot (free tier)
   - Pingdom
   - Cloud provider monitoring

3. **Document access methods**:
   - Save VPN credentials
   - Note cloud provider console access
   - Keep backup access method

---

## 🔄 Workaround: Process Data Locally

While troubleshooting network access, you can:

1. **Process data locally** (slower, no GPU):
   ```bash
   cd /Users/Codebase/projects/alterpublics/NAMO_nov25
   python3 scripts/02_nlp_processing.py --test --batch-size 1
   ```

2. **Use remote desktop/VNC** (if available):
   - Access the server via VNC/RDP
   - Run commands from there

3. **Contact server administrator**:
   - Ask them to check server status
   - Ask if firewall rules changed
   - Request alternative access method

---

## 📝 Summary

**Current Status:**
- ❌ SSH connection timing out on all ports
- ❌ Ping not working (100% packet loss)
- ⚠️  Network-level issue, not SSH configuration

**Most Likely Causes (in order):**
1. Your network changed or VPN disconnected
2. Server is behind a firewall that's blocking your current IP
3. Server's network interface went down
4. Server is powered off or crashed

**Next Steps:**
1. Check if you're on the same network as before
2. Try connecting from mobile hotspot
3. Check cloud provider console for server status
4. Contact server administrator if you have no direct access


