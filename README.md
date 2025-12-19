Here is a comprehensive, professional, and easy-to-follow `README.md` file for your project.

I have structured it to guide the user from zero to a fully running dashboard, including optional steps for running it 24/7 as a background service.

---

# ⛓️ Teranode Monitor - Enhanced Edition

A visually stunning, Flask-based web dashboard to monitor your Bitcoin SV (BSV) Teranode. featuring a "Matrix" style aesthetic, floating blockchain animations, and real-time network statistics.

## ✨ Features

* **Real-Time Monitoring:** Live updates every 10 seconds via RPC.
* **Visual Aesthetics:** Blue Matrix rain animation, floating blocks, and hex-grid overlays.
* **Sync Progress:** Visual progress bar tracking your node against the network target height.
* **Detailed Stats:** View mempool size, peer connections, difficulty, and block info.
* **Responsive Design:** Fully optimized for Desktop, Tablet, and Mobile (with touch feedback).
* **API Endpoints:** Built-in JSON endpoints for external health checks.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.6+** installed.
2. **Access to a Teranode** (IP address, RPC Username, and RPC Password).
3. **Network Access:** Ensure the machine running this dashboard can reach the Teranode's RPC port (default `9292`).

---

## 🚀 Installation & Setup Guide

Follow these steps to get your monitor running in minutes.

### Step 1: Download the Monitor

Save the script file as `teranode_monitor.py` in a dedicated folder.

```bash
mkdir teranode-monitor
cd teranode-monitor
# Move your python file into this folder

```

### Step 2: Install Dependencies

You need `Flask` for the web server and `Requests` to talk to the node.

Run the following command:

```bash
pip install flask requests

```

*> **Note:** If you are on a managed Linux environment (like newer Ubuntu versions) and get an "externally-managed-environment" error, you can use:*

```bash
pip install flask requests --break-system-packages

```

### Step 3: Configure Your Node Details

You need to edit the Python script to point to your specific Teranode.

1. Open `teranode_monitor.py` in a text editor (nano, vim, VS Code, etc.).
2. Locate the **CONFIGURATION** section near the top (lines 23-30).
3. Update the variables with your node's details:

```python
# ============================================
# CONFIGURATION
# ============================================
TERANODE_HOST = "127.0.0.1"      # <-- IP address of your Teranode
TERANODE_RPC_PORT = 9292         # <-- Usually 9292 or 8332
TERANODE_RPC_USER = "your_user"  # <-- Your RPC Username
TERANODE_RPC_PASS = "your_pass"  # <-- Your RPC Password

# Update this periodically to match the global network height
TARGET_HEIGHT = 928100 

```

4. Save and close the file.

### Step 4: Run the Dashboard

Start the monitor with the following command:

```bash
python3 teranode_monitor.py

```

You should see an output similar to this:

```text
╔═══════════════════════════════════════════════════════════════╗
║          TERANODE MONITOR WEB DASHBOARD - ENHANCED            ║
...
║  🌐 Dashboard URL:  http://0.0.0.0:4000                       ║
...

```

### Step 5: Access the Dashboard

Open your web browser and navigate to:

* **Local machine:** `http://localhost:4000`
* **From another device:** `http://<YOUR_SERVER_IP>:4000`

---

## 📡 API Documentation

The monitor exposes simple JSON endpoints if you want to pull data into other tools (like Grafana or Uptime Kuma).

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | The visual HTML Dashboard |
| `/api/status` | GET | Full JSON dump of all node statistics |
| `/api/health` | GET | Simple status check (Returns `healthy: true/false`) |

**Example `/api/health` response:**

```json
{
  "block_height": 927500,
  "connections": 42,
  "healthy": true
}

```

---

## ⚙️ Optional: Run as a Service (Linux)

To keep the dashboard running 24/7 even if you close your terminal, set it up as a systemd service.

1. **Create the service file:**
```bash
sudo nano /etc/systemd/system/teranode-monitor.service

```


2. **Paste the following** (adjust paths to match your setup):
```ini
[Unit]
Description=Teranode Web Monitor
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/your/folder
ExecStart=/usr/bin/python3 /path/to/your/folder/teranode_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

```


3. **Enable and Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable teranode-monitor
sudo systemctl start teranode-monitor

```



---

## ❓ Troubleshooting

**"Connection refused - is Teranode running?"**

* Check if your Teranode is actually running.
* Verify the `TERANODE_HOST` IP address is correct.
* Check firewall settings (ensure port 9292 is open locally).

**"401 Unauthorized"**

* Double-check your `TERANODE_RPC_USER` and `TERANODE_RPC_PASS` in the configuration section.

**I don't see the animations.**

* The dashboard uses modern CSS. Ensure your browser is up to date.
* If you have "Reduce Motion" enabled in your OS settings, the animations are automatically disabled for accessibility.

---

**License:** MIT

**Created for the BSV Ecosystem**
