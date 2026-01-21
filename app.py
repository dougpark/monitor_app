from flask import Flask, render_template
from flask import jsonify
from datetime import datetime
import subprocess
import re

app = Flask(__name__)

# Define the storage partition to monitor
storage = "nvme0n1p2"

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

def run_disk_usage():
    # Get disk usage for the specified storage partition
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if storage in line:
                parts = line.split()
                return {"size": parts[1], "used": parts[2], "avail": parts[3], "percent": parts[4], "mount": parts[5]}
        return None
    except Exception:
        return None

@app.route('/')
# Main monitoring page
def monitor():
    server_time = datetime.now().strftime("%a, %b %d, %Y %I:%M:%S %p")
    return render_template('monitor.html', 
                           nvidia=run_nvidia_smi(), 
                           ollama=run_ollama_ps(), 
                           sys=run_system_info(), 
                           disk=run_disk_usage(),
                           server_time=server_time)

@app.route('/api/stats')
# API endpoint to get stats in JSON format
def stats_api():
    
    # This returns the raw data for JavaScript to use
    return jsonify({
        "nvidia": run_nvidia_smi(),
        "ollama": run_ollama_ps(),
        "sys": run_system_info(),
        "disk": run_disk_usage(),
        "server_time": datetime.now().strftime("%a, %b %d, %Y %I:%M:%S %p")
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)