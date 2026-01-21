# 🖥️ AI Station Monitor

A lightweight, real-time web dashboard built with **Flask** and **Docker** to monitor NVIDIA GPU performance, system resources, and running **Ollama** models.



## 🚀 Features
* **GPU Monitoring:** Real-time tracking of Fan Speed, Temperature, Power Draw, and VRAM usage via `nvidia-smi`.
* **Ollama Integration:** Structured view of currently loaded AI models, including size and processor (CPU/GPU) type.
* **System Vitals:** Live updates of CPU Load Average, RAM usage, and Disk health (`nvme0n1p2`).
* **Auto-Refresh:** Uses JavaScript `fetch` to update stats every 5 seconds without page flickering.
* **Containerized:** Fully Dockerized with GPU passthrough and Docker-socket access.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure your Ubuntu host has the following installed:
* [Docker & Docker Compose](https://docs.docker.com/engine/install/ubuntu/)
* [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) (Required for GPU passthrough)

### 2. Clone the Repository
```bash
git clone git@github.com:dougpark/monitor_app.git
cd monitor_app