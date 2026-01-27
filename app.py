#!/usr/bin/env python3
"""
Hardware & AI Model Monitor
---------------------------
Provides a web interface and JSON API for real-time monitoring of:
- GPU (Nvidia) status and power draw.
- System temperatures (CPU, VRM, SSD).
- Disk usage and Docker-based Ollama model status.

Usage: python app.py
"""

from flask import Flask, render_template
from flask import jsonify
from datetime import datetime
import subprocess
import re
import psutil
import time

app = Flask(__name__)

# Define the storage partition to monitor
storage = "nvme0n1p2"

# Configurable cache timers
FAST_INTERVAL = 1.0   # 1 second
SLOW_INTERVAL = 60.0  # 1 minute

# Global variables to store the cache
cache = {
    "fast_data": {},
    "slow_data": {},
    "last_fast_update": 0,
    "last_slow_update": 0
}



def run_temp_info():
    try:
        temps = psutil.sensors_temperatures()
        fans = psutil.sensors_fans()
        
        data = {
            "cpu_temp": "N/A",
            "ssd_temp": "N/A",
            "vrm_temp": "N/A",
            "pump_speed": "0 RPM",
            "sys_fan_1": "0 RPM"
        }

        # Temperatures
        if 'k10temp' in temps:
            data["cpu_temp"] = f"{temps['k10temp'][0].current}°C"
        
        if 'nvme' in temps:
            data["ssd_temp"] = f"{temps['nvme'][0].current}°C"

        # Motherboard Specifics (nct6687)
        if 'nct6687' in temps:
            for entry in temps['nct6687']:
                if entry.label == 'VRM MOS':
                    data["vrm_temp"] = f"{entry.current}°C"

        if 'nct6687' in fans:
            for entry in fans['nct6687']:
                if entry.label == 'Pump Fan':
                    data["pump_speed"] = f"{entry.current} RPM"
                elif entry.label == 'System Fan #1':
                    # data["sys_fan_1"] = f"{entry.current} RPM"
                    # Check if it's 0 to set a status
                    rpm = entry.current
                    data["sys_fan_1"] = f"{rpm} RPM" if rpm > 0 else "0 RPM"
        
        return data
    except Exception as e:
        return {"error": str(e)}

def run_nvidia_smi():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=fan.speed,temperature.gpu,power.draw,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(',')
        return {
            "fan": parts[0].strip() + "%",
            "temp": parts[1].strip() + "°C",
            "power": parts[2].strip() + "W",
            "mem": parts[3].strip() + " MiB",
            "util": parts[4].strip() + "%"
        }
    except Exception as e:
        return {"error": str(e)}

def run_ollama_ps():
    try:
        # Get the output from the ollama ps command inside the Docker container
        result = subprocess.run(['docker', 'exec', 'ollama', 'ollama', 'ps'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        
        if len(lines) <= 1: # Only header or empty
            return []

        models = []
        # Skip the header line (lines[0]) and parse the rest
        for line in lines[1:]:
            # Split by 2 or more spaces to keep columns intact
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 4:
                models.append({
                    "name": parts[0],
                    "id": parts[1],
                    "size": parts[2],
                    "processor": parts[3],
                    "until": parts[5] if len(parts) > 4 else "N/A"
                })
        return models
    except Exception as e:
        print(f"Ollama Error: {e}")
        return []

def run_system_info():
    # Get memory and load average
    try:
        mem_res = subprocess.run(['free', '-h'], capture_output=True, text=True, check=True)
        mem_match = re.search(r'Mem:\s+(\S+)\s+(\S+)', mem_res.stdout)
        
        load_res = subprocess.run(['uptime'], capture_output=True, text=True, check=True)
        load_match = re.search(r'load average:\s*([\d.]+)', load_res.stdout)
        
        return {
            "mem_total": mem_match.group(1) if mem_match else "N/A",
            "mem_used": mem_match.group(2) if mem_match else "N/A",
            "load": load_match.group(1) if load_match else "N/A"
        }
    except Exception as e:
        return {"error": str(e)}

# Helper function to get disk usage
def run_disk_usage():
    try:
        # Running df -h without a specific path is actually very fast 
        # and less prone to "command failed" errors
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            # Check if our storage name (e.g., "nvme0n1p2") is in this line
            if storage in line:
                parts = line.split()
                # df output columns: Filesystem, Size, Used, Avail, Use%, Mounted on
                return {
                    "storage": storage,
                    "size": parts[1], 
                    "used": parts[2], 
                    "avail": parts[3], 
                    "percent": parts[4], 
                    "mount": parts[5]
                }
        
        # If loop finishes without finding the string
        return {"storage": storage+" not found", "size": "N/A", "used": "N/A", "avail": "N/A", "percent": "0%", "mount": "N/A"}

    except Exception as e:
        # Print the actual error to your terminal so you can see why it failed
        print(f"Disk Usage Error: {e}")
        return {"storage": storage, "size": "Error", "used": "N/A", "avail": "N/A", "percent": "0%", "mount": "N/A"}

# Helper function to get current server time
# Returns formated time string: Sun, Jan 25, 2026 10:56:42 AM
def get_server_time():
    return datetime.now().strftime("%a, %b %d, %Y %I:%M:%S %p")

# Combine fast and slow stats with caching
def get_combined_stats():
    current_time = time.time()
    
    # 1. Update FAST data (Temps, GPU, CPU Load)
    if current_time - cache["last_fast_update"] > FAST_INTERVAL:
        cache["fast_data"] = {
            "nvidia": run_nvidia_smi(),
            "sys": run_system_info(),
            "temps": run_temp_info(),
            "server_time": get_server_time()
        }
        cache["last_fast_update"] = current_time

    # 2. Update SLOW data (Disk, Ollama)
    if current_time - cache["last_slow_update"] > SLOW_INTERVAL:
        cache["slow_data"] = {
            "disk": run_disk_usage(),
            "ollama": run_ollama_ps()
        }
        cache["last_slow_update"] = current_time

    # 3. Merge and return
    return {**cache["fast_data"], **cache["slow_data"]}

@app.route('/')
def monitor():
    return render_template('monitor.html', **get_combined_stats())

@app.route('/api/stats')
def stats_api():
    return jsonify(get_combined_stats())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)