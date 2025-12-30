# 🔇 GameVoiceGuard

### Network-Level Parental Controls for Game Voice Chat

> **Protect your children from online harassment, cyberbullying, and inappropriate voice communications in games like Fortnite, Roblox, and other multiplayer titles.**

![unnamed-4](https://github.com/user-attachments/assets/c8986313-8a8f-40de-a8af-c8e9242fa955)


---

## 🎯 Why GameVoiceGuard?

Modern games like **Roblox**, **Fortnite**, **Minecraft**, and others include voice chat features that connect your child with strangers worldwide. While these features can enhance gameplay, they also expose children to:

- **Cyberbullying and harassment** from other players
- **Inappropriate language and adult content**
- **Predatory behavior** from bad actors
- **Toxic gaming culture** that affects mental health
- **Unsupervised conversations** that bypass parental awareness

### The Problem with Built-in Parental Controls

| Limitation | Issue |
|------------|-------|
| **Easy to bypass** | Tech-savvy kids can disable in-game settings |
| **Inconsistent** | Each game has different controls |
| **All or nothing** | Often can't block voice while keeping gameplay |
| **Account-based** | Kids create alt accounts to bypass restrictions |

### The GameVoiceGuard Solution

GameVoiceGuard operates at the **network level**, making it:

- ✅ **Impossible to bypass** from the gaming device
- ✅ **Universal** across all games using Vivox voice (industry standard)
- ✅ **Surgical** - blocks only voice chat, gameplay works perfectly
- ✅ **Invisible** to the child - voice simply "doesn't work"
- ✅ **Centrally controlled** from a parent's computer

---

## 🛡️ How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR HOME NETWORK                                │
│                                                                          │
│  ┌──────────────┐       ┌──────────────────┐       ┌──────────────┐     │
│  │    Child's   │       │  GameVoiceGuard  │       │    Router    │     │
│  │ Gaming Device│──────▶│   (Your Mac/PC)  │──────▶│              │────▶│ Internet
│  │              │◀──────│                  │◀──────│              │◀────│
│  └──────────────┘       └──────────────────┘       └──────────────┘     │
│                                  │                                       │
│                                  ▼                                       │
│                    ┌───────────────────────────┐                        │
│                    │     Traffic Analysis      │                        │
│                    │                           │                        │
│                    │  🎮 Game Traffic → PASS   │                        │
│                    │  🎤 Voice Traffic → BLOCK │                        │
│                    └───────────────────────────┘                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technical Overview

1. **ARP Spoofing** - GameVoiceGuard positions itself between the gaming device and your router
2. **Traffic Analysis** - Identifies voice chat packets by analyzing:
   - Destination IPs (Vivox voice servers: 128.116.0.0/16)
   - UDP ports (STUN: 3478, SIP: 5060-5062, Media: 12000-32000)
   - Packet patterns characteristic of voice streams
3. **Selective Blocking** - Drops voice packets while forwarding game traffic
4. **Continuous Monitoring** - Detects new voice server IPs and updates rules

---

## 🎮 Supported Games

GameVoiceGuard blocks voice chat in games using **Vivox** technology (the industry standard):

| Game | Voice Blocked | Gameplay Affected |
|------|---------------|-------------------|
| Roblox | ✅ Yes | ❌ No |
| Fortnite | ✅ Yes | ❌ No |
| PUBG | ✅ Yes | ❌ No |
| League of Legends | ✅ Yes | ❌ No |
| Valorant | ✅ Yes | ❌ No |
| VRChat | ✅ Yes | ❌ No |
| Rec Room | ✅ Yes | ❌ No |
| Rainbow Six Siege | ✅ Yes | ❌ No |
| Many others... | ✅ Yes | ❌ No |

> **Note:** Text chat and gameplay remain fully functional. Only voice communication is blocked.

---

## 📋 Requirements

### Hardware
- **Control Machine**: Mac (macOS 10.15+) or Linux computer on the same network
- **Target Device**: Any gaming device (PC, Xbox, PlayStation, Nintendo Switch, Mobile)

### Software
- Python 3.8+
- Scapy (`pip install scapy`)
- Bettercap (`brew install bettercap` on macOS)
- Root/Administrator privileges

### Network
- All devices must be on the same local network (same WiFi/router)
- Control machine should be wired (Ethernet) for best performance

---

## 🚀 Installation

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 bettercap

# Install Python packages
pip3 install scapy

# Download GameVoiceGuard
git clone https://github.com/yourusername/GameVoiceGuard.git
cd GameVoiceGuard

# Make executable
chmod +x voice_blocker_complete.py
```

### Linux (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip bettercap

# Install Python packages
pip3 install scapy

# Download GameVoiceGuard
git clone https://github.com/yourusername/GameVoiceGuard.git
cd GameVoiceGuard

# Make executable
chmod +x voice_blocker_complete.py
```

---

## 📖 Usage

### Quick Start (One Command)

```bash
sudo python3 voice_blocker_complete.py --target 192.168.1.100
```

Replace `192.168.1.100` with your child's gaming device IP address.

### Find Your Child's Device IP

**Option 1: Check your router**
1. Log into your router (usually 192.168.1.1 or 10.0.0.1)
2. Find "Connected Devices" or "DHCP Clients"
3. Look for the gaming device by name

**Option 2: Use the network scan**
```bash
sudo arp -a
```

### Command Options

| Command | Description |
|---------|-------------|
| `--target IP` | Target device IP to block voice for |
| `--monitor` | Show live count of blocked voice packets |
| `--duration N` | Recon duration in seconds (default: 30) |
| `--no-recon` | Skip voice server discovery, use known servers |
| `--status` | Show current blocking status |
| `--disable` | Turn off all blocking |

### Examples

```bash
# Basic blocking
sudo python3 voice_blocker_complete.py --target 192.168.1.100

# Block with live monitoring (see blocked packets in real-time)
sudo python3 voice_blocker_complete.py --target 192.168.1.100 --monitor

# Quick block without recon (uses known voice servers)
sudo python3 voice_blocker_complete.py --target 192.168.1.100 --no-recon

# Extended recon for detecting new voice servers
sudo python3 voice_blocker_complete.py --target 192.168.1.100 --duration 60

# Check if blocking is active
sudo python3 voice_blocker_complete.py --status

# Disable blocking (restore normal voice chat)
sudo python3 voice_blocker_complete.py --disable
```

---

## 🔍 How the Blocking Works

### Phase 1: Network Interception (ARP Spoofing)

GameVoiceGuard uses ARP spoofing to intercept traffic:

```
Before: Gaming Device ←→ Router ←→ Internet
After:  Gaming Device ←→ GameVoiceGuard ←→ Router ←→ Internet
```

This is the same technique used by enterprise network monitoring tools.

### Phase 2: Voice Server Discovery (Recon)

The tool analyzes traffic to identify voice servers:

```
[*] Running voice server recon (30s)...
    >>> Make sure voice chat is ACTIVE on target! <<<

    Found 3 voice server(s):
      NEW: 128.116.53.33 (Voice pattern, High rate)
      NEW: 128.116.102.90 (STUN)
      128.116.102.126 (STUN) - already covered
```

### Phase 3: Firewall Rules

Blocking rules are applied using the system firewall (pf on macOS):

```
# Voice Server IP Ranges
block drop quick proto udp from 192.168.1.100 to 128.116.0.0/16
block drop quick proto udp from 128.116.0.0/16 to 192.168.1.100

# Voice Signaling Ports
block drop quick proto udp from 192.168.1.100 to any port 3478:3479
block drop quick proto udp from 192.168.1.100 to any port 5060
block drop quick proto udp from 192.168.1.100 to any port 5062

# Voice Media Ports
block drop quick proto udp from 192.168.1.100 to any port 12000:32000
```

### What Gets Blocked vs Allowed

| Traffic Type | Action | Reason |
|--------------|--------|--------|
| Vivox servers (128.116.x.x) | 🚫 BLOCKED | Voice infrastructure |
| STUN ports (3478-3479) | 🚫 BLOCKED | Voice connection setup |
| SIP ports (5060, 5062) | 🚫 BLOCKED | Voice signaling |
| Media ports (12000-32000) | 🚫 BLOCKED | Voice audio streams |
| Game servers | ✅ ALLOWED | Gameplay traffic |
| Matchmaking | ✅ ALLOWED | Finding games |
| Friends/Party | ✅ ALLOWED | Social features |
| Updates | ✅ ALLOWED | Game updates |
| High ports (49152-65535) | ✅ ALLOWED | Game data |

---

## 📊 Monitoring

### Live Blocked Packet Counter

```bash
sudo python3 voice_blocker_complete.py --target 192.168.1.100 --monitor
```

Output:
```
[*] Monitoring blocked packets (Ctrl+C to stop)

  12:30:45  Blocked: 15,234 total (+127 new)  Rate: 324.7/s
  12:30:46  Blocked: 15,361 total (+127 new)  Rate: 318.2/s
  12:30:47  Blocked: 15,488 total (+127 new)  Rate: 321.5/s
```

When voice chat is active, you'll see hundreds of packets blocked per second. When the game is closed or voice isn't being used, the rate drops to zero.

### Status Check

```bash
sudo python3 voice_blocker_complete.py --status
```

Output:
```
╔══════════════════════════════════════════════════════════════════════╗
║             GAME VOICE BLOCKER - All-in-One Edition                  ║
╚══════════════════════════════════════════════════════════════════════╝

[+] pf firewall: ENABLED
[+] Bettercap: RUNNING

Active rules:
  block drop quick proto udp from 192.168.1.100 to 128.116.0.0/16
  block drop quick proto udp from 128.116.0.0/16 to 192.168.1.100
  ...

Packets blocked: 1,234,567 (rate: 0.0/s)

Last target: 192.168.1.100
Last run: 2025-01-15T14:30:00
```

---

## 🔧 Troubleshooting

### "Could not find target device"

- Ensure the gaming device is powered on and connected to WiFi
- Verify you have the correct IP address
- Try pinging the device: `ping 192.168.1.100`

### "Bettercap failed to start"

- Install bettercap: `brew install bettercap` (macOS)
- Make sure you're running with sudo
- Check if another instance is running: `pgrep bettercap`

### Voice chat still works

1. Verify blocking is active: `--status`
2. The game may cache connections - restart the game
3. Run extended recon: `--duration 60`
4. New voice servers may have been added - rerun with recon

### Game disconnects or lag

- This shouldn't happen if configured correctly
- Check that you're not blocking game ports
- Ensure your Mac/PC can handle the traffic throughput
- Use wired (Ethernet) connection for the control machine

### Blocking affects other devices

- Make sure you specified the correct `--target` IP
- Rules are device-specific and shouldn't affect others

---

## ⚠️ Important Considerations

### Legal & Ethical Use

- ✅ **DO** use on your own network with your own devices
- ✅ **DO** use for parental controls on minor children's devices
- ✅ **DO** inform children (age-appropriately) about online safety
- ❌ **DON'T** use on networks you don't own/administer
- ❌ **DON'T** use to harass or interfere with others

### Limitations

1. **Same network required** - Control machine and gaming device must be on the same LAN
2. **Continuous operation** - Bettercap must remain running for blocking to work
3. **New servers** - Voice providers occasionally add new servers; rerun recon periodically
4. **Not 100% foolproof** - Determined teens might find workarounds (VPN, mobile hotspot)

### Privacy

- This tool only analyzes packet metadata (IPs, ports), not content
- Voice conversations are encrypted; this tool cannot listen to them
- No data is collected or transmitted externally

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas for improvement:

- [ ] Windows support
- [ ] Router-level implementation (no ARP spoofing needed)
- [ ] Web-based control panel
- [ ] Scheduled blocking (e.g., school hours only)
- [ ] Support for additional voice platforms
- [ ] Mobile app for control

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built for parents who want granular control over their children's online gaming experience
- Inspired by the need for better parental controls that go beyond simple "allow/block" options
- Thanks to the open-source community for tools like Scapy and Bettercap

---

## 📞 Support

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and community support

---

<p align="center">
  <b>Protecting kids online, one voice packet at a time.</b>
  <br><br>
  ⭐ Star this repo if it helped you!
</p>
