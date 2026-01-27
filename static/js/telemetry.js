// telemetry.js

/**
 * Global Constants
 */
const API_STATS_URL = '/api/stats';
const REFRESH_MS = 1000;

async function updateStats() {
    let isAnyTempDangerous = false;
    const pulseDot = document.querySelector('.pulse'); // Select the dot
    const clockElement = document.getElementById('live-clock');
    const statusText = document.getElementById('status-text'); // Get the text element

    try {
        const response = await fetch(API_STATS_URL);
        if (!response.ok) throw new Error("Server Error");

        const data = await response.json();

        // Server is available
        statusText.innerText = "Telemetry: Active";
        statusText.style.color = "var(--success)"; // Make the text green for visibility
        document.querySelector('.clock-box').style.borderColor = "rgba(56, 189, 248, 0.3)";

        // Server is UP: Add the animation class
        pulseDot.classList.add('active');
        if (data.server_time) {
            clockElement.innerText = data.server_time;
            clockElement.style.color = "var(--accent)"; // Reset color if it was red
        }

        // Update the Server Clock from the API response
        if (data.server_time) {
            document.getElementById('live-clock').innerText = data.server_time;
        }

        // Update GPU Stats
        if (!data.nvidia.error) {
            document.getElementById('gpu-util').innerText = data.nvidia.util;
            document.getElementById('gpu-temp').innerText = data.nvidia.temp;
            document.getElementById('gpu-mem').innerText = data.nvidia.mem;
            document.getElementById('gpu-power').innerText = data.nvidia.power;
            document.getElementById('gpu-fan').innerText = data.nvidia.fan;
        }

        // Update System Stats
        document.getElementById('sys-load').innerText = data.sys.load;
        document.getElementById('sys-mem').innerText = `${data.sys.mem_used} / ${data.sys.mem_total}`;

        // Update Thermal Stats
        if (data.temps) {

            // CPU Temp
            const cpuEl = document.getElementById('cpu-temp');
            const cpuVal = Math.ceil(parseFloat(data.temps.cpu_temp));
            cpuEl.innerText = cpuVal + "°C";
            const cpuTempEl = document.getElementById('cpuTemp-badge');

            // Dynamic Color Warning for CPU
            if (cpuVal > 80) {
                cpuEl.style.color = "var(--danger)";
                isAnyTempDangerous = true;
                cpuTempEl.innerText = "High";
                cpuTempEl.className = "temp-status status-high";
            } else {
                cpuEl.style.color = "var(--text-main)";

            }

            // SSD Temp
            const ssdEl = document.getElementById('ssd-temp');
            const ssdVal = Math.ceil(parseFloat(data.temps.ssd_temp));
            ssdEl.innerText = ssdVal + "°C";

            // Dynamic Color Warning for SSD
            if (ssdVal > 70) {
                ssdEl.style.color = "var(--danger)";
                isAnyTempDangerous = true;
            } else {
                ssdEl.style.color = "var(--text-main)";

            }

            // VRM Temp
            const vrmEl = document.getElementById('vrm-temp');
            const vrmVal = Math.ceil(parseFloat(data.temps.vrm_temp));
            vrmEl.innerText = vrmVal + "°C";

            // Dynamic Color Warning for VRM
            if (vrmVal > 90) {
                vrmEl.style.color = "var(--danger)";
                isAnyTempDangerous = true;
            } else {
                vrmEl.style.color = "var(--text-main)";
            }

            // AIO Pump Speed
            const pumpSpeed = parseInt(data.temps.pump_speed);
            const pumpEl = document.getElementById('pump-speed');

            if (pumpSpeed < 500) {
                pumpEl.style.color = "var(--danger)";
                pumpEl.innerHTML = `⚠️ Low ${data.temps.pump_speed}`;
                isAnyTempDangerous = true;

            } else {
                pumpEl.style.color = "var(--text-main)";

            }

            // Highlight card if any temp is dangerous
            if (isAnyTempDangerous) {
                cpuEl.closest('.card').style.boxShadow = "0 0 20px #f87171";
            } else {
                cpuEl.closest('.card').style.boxShadow = "";
            }

            // System Fan
            const fanValue = data.temps.sys_fan_1;
            const fanEl = document.getElementById('sys-fan-1');
            const badgeEl = document.getElementById('fan-badge');

            fanEl.innerText = fanValue;

            if (parseInt(fanValue) === 0) {
                fanEl.innerText = "";
                badgeEl.innerText = "Idle";
                badgeEl.className = "fan-status status-silent";
                fanEl.style.color = "var(--text-dim)";
            } else {
                badgeEl.innerText = "Active";
                badgeEl.className = "fan-status status-active";
                fanEl.style.color = "var(--success)";
            }


        }

        // Update Disk Stats
        if (data.disk) {
            document.getElementById('disk-used').innerText = data.disk.used;
            document.getElementById('disk-percent').innerText = data.disk.percent;
            document.getElementById('disk-avail').innerText = `${data.disk.avail} of ${data.disk.size}`;
        }

        // Update Ollama Table
        const ollamaBody = document.querySelector('.ollama-table ollama-body') || document.getElementById('ollama-body');
        if (data.ollama.length > 0) {
            let html = '';
            data.ollama.forEach(model => {
                // Determine the color based on processor status
                const isFullGpu = model.processor === "100% GPU";
                const badgeColor = isFullGpu ? 'var(--success)' : 'var(--warning)'; // Success green vs Warning yellow
                const badgeBorder = isFullGpu ? 'var(--success)' : 'var(--warning)';

                html += `<tr>
                            <td><span class="model-name">${model.name}</span></td>
                            <td>${model.size}</td>
                            <td>
                                <span class="badge" style="color: ${badgeColor}; border-color: ${badgeBorder};">
                                    ${model.processor}
                                </span>
                            </td>
                            <td>${model.until}</td>
                        </tr>`;
            });
            ollamaBody.innerHTML = html;
        } else {
            ollamaBody.innerHTML = '<tr> \
                        <td colspan="3" style="style="color: var(--text-dim); font-style: italic; text-align: left;">No models currently loaded</td></tr>';
        }

    } catch (error) {
        console.error('Error fetching stats:', error);
        // ERROR STATE
        pulseDot.classList.remove('active');
        statusText.innerText = "Telemetry: Unavailable";
        statusText.style.color = "var(--danger)"; // Make the text red for visibility

        clockElement.innerText = "OFFLINE";
        clockElement.style.color = "var(--danger)";

        document.querySelector('.clock-box').style.borderColor = "var(--danger)";
    }



}

// Run every REFRESH_MS milliseconds
setInterval(updateStats, REFRESH_MS);



