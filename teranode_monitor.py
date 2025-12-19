#!/usr/bin/env python3
"""
Teranode Monitor Web Dashboard - Enhanced Edition
=================================================
A Flask-based web interface to monitor your Teranode BSV node.
Features: Blue Matrix rain, floating blockchain blocks, BSV themed animations

Usage:
    pip install flask requests --break-system-packages
    python teranode_monitor.py

Then open: http://localhost:4000
"""

from flask import Flask, render_template_string, jsonify
import requests
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================
TERANODE_HOST = "IP_ADDRESS_OF_TERANODE_SERVER_HERE"
TERANODE_RPC_PORT = 9292
TERANODE_RPC_USER = "bitcoin"
TERANODE_RPC_PASS = "bitcoin"
FLASK_HOST = "0.0.0.0"  # Listen on all interfaces
FLASK_PORT = 4000

# Target block height (update periodically)
TARGET_HEIGHT = 928100

# ============================================
# RPC HELPER
# ============================================
def rpc_call(method, params=[]):
    """Make an RPC call to Teranode"""
    url = f"http://{TERANODE_HOST}:{TERANODE_RPC_PORT}/"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "1.0",
        "id": "monitor",
        "method": method,
        "params": params
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            auth=(TERANODE_RPC_USER, TERANODE_RPC_PASS),
            timeout=10
        )
        result = response.json()
        return result.get("result"), None
    except requests.exceptions.ConnectionError:
        return None, "Connection refused - is Teranode running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except Exception as e:
        return None, str(e)

def get_node_status():
    """Get comprehensive node status"""
    status = {
        "online": False,
        "error": None,
        "block_height": 0,
        "best_block_hash": "",
        "chain": "",
        "difficulty": 0,
        "connections": 0,
        "version": 0,
        "protocol_version": 0,
        "verification_progress": 0,
        "sync_percentage": 0,
        "target_height": TARGET_HEIGHT,
        "blocks_remaining": TARGET_HEIGHT,
        "mempool_size": 0,
        "mempool_bytes": 0,
        "peers": [],
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Get blockchain info
    info, error = rpc_call("getblockchaininfo")
    if error:
        status["error"] = error
        return status
    
    if info:
        status["online"] = True
        status["block_height"] = info.get("blocks", 0)
        status["best_block_hash"] = info.get("bestblockhash", "")[:16] + "..."
        status["chain"] = info.get("chain", "unknown")
        status["difficulty"] = info.get("difficulty", 0)
        status["verification_progress"] = info.get("verificationprogress", 0)
        status["blocks_remaining"] = TARGET_HEIGHT - status["block_height"]
        status["sync_percentage"] = round((status["block_height"] / TARGET_HEIGHT) * 100, 2) if TARGET_HEIGHT > 0 else 0
    
    # Get node info
    node_info, _ = rpc_call("getinfo")
    if node_info:
        status["connections"] = node_info.get("connections", 0)
        status["version"] = node_info.get("version", 0)
        status["protocol_version"] = node_info.get("protocolversion", 0)
    
    # Get mempool info
    mempool, _ = rpc_call("getmempoolinfo")
    if mempool:
        status["mempool_size"] = mempool.get("size", 0)
        status["mempool_bytes"] = mempool.get("bytes", 0)
    
    # Get peer info
    peers, _ = rpc_call("getpeerinfo")
    if peers and isinstance(peers, list):
        status["peers"] = [{
            "addr": p.get("addr", "unknown"),
            "subver": p.get("subver", ""),
            "synced_blocks": p.get("synced_blocks", 0)
        } for p in peers[:10]]  # Limit to 10 peers
        status["connections"] = len(peers)
    
    return status

# ============================================
# HTML TEMPLATE WITH ENHANCED ANIMATIONS
# ============================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0a0e17">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Teranode Monitor | BSV Blockchain</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: rgba(26, 34, 52, 0.85);
            --bg-card-solid: #1a2234;
            --bg-card-hover: #1f2937;
            --border-color: rgba(59, 130, 246, 0.2);
            --border-glow: rgba(59, 130, 246, 0.4);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --accent-cyan: #06b6d4;
            --bsv-orange: #eab308;
            --glow-blue: rgba(59, 130, 246, 0.3);
            --glow-cyan: rgba(6, 182, 212, 0.3);
            --matrix-blue: #3b82f6;
            --matrix-cyan: #06b6d4;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            font-size: 16px;
            -webkit-text-size-adjust: 100%;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        
        /* ============================================
           MATRIX RAIN ANIMATION - BLUE THEME
           ============================================ */
        #matrix-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.15;
            pointer-events: none;
        }
        
        /* ============================================
           FLOATING BLOCKCHAIN BLOCKS
           ============================================ */
        .blockchain-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            overflow: hidden;
        }
        
        .floating-block {
            position: absolute;
            border: 1px solid var(--border-color);
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05));
            border-radius: 8px;
            opacity: 0;
            animation: floatBlock 20s infinite ease-in-out;
        }
        
        .floating-block::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 60%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
        }
        
        .floating-block::after {
            content: '⛓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.6em;
            opacity: 0.5;
        }
        
        .floating-block:nth-child(1) { width: 60px; height: 60px; left: 5%; animation-delay: 0s; }
        .floating-block:nth-child(2) { width: 80px; height: 80px; left: 15%; animation-delay: 2s; }
        .floating-block:nth-child(3) { width: 50px; height: 50px; left: 25%; animation-delay: 4s; }
        .floating-block:nth-child(4) { width: 70px; height: 70px; left: 35%; animation-delay: 6s; }
        .floating-block:nth-child(5) { width: 55px; height: 55px; left: 45%; animation-delay: 8s; }
        .floating-block:nth-child(6) { width: 65px; height: 65px; left: 55%; animation-delay: 10s; }
        .floating-block:nth-child(7) { width: 75px; height: 75px; left: 65%; animation-delay: 12s; }
        .floating-block:nth-child(8) { width: 45px; height: 45px; left: 75%; animation-delay: 14s; }
        .floating-block:nth-child(9) { width: 85px; height: 85px; left: 85%; animation-delay: 16s; }
        .floating-block:nth-child(10) { width: 55px; height: 55px; left: 92%; animation-delay: 18s; }
        
        @keyframes floatBlock {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 0.3;
            }
            90% {
                opacity: 0.3;
            }
            100% {
                transform: translateY(-100px) rotate(360deg);
                opacity: 0;
            }
        }
        
        /* ============================================
           CHAIN LINK CONNECTIONS
           ============================================ */
        .chain-connections {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            overflow: hidden;
        }
        
        .chain-link {
            position: absolute;
            width: 200px;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-blue), var(--accent-cyan), transparent);
            opacity: 0;
            animation: chainPulse 8s infinite ease-in-out;
        }
        
        .chain-link:nth-child(1) { top: 10%; left: -200px; animation-delay: 0s; transform: rotate(15deg); }
        .chain-link:nth-child(2) { top: 25%; left: -200px; animation-delay: 1.5s; transform: rotate(-10deg); }
        .chain-link:nth-child(3) { top: 40%; left: -200px; animation-delay: 3s; transform: rotate(5deg); }
        .chain-link:nth-child(4) { top: 55%; left: -200px; animation-delay: 4.5s; transform: rotate(-15deg); }
        .chain-link:nth-child(5) { top: 70%; left: -200px; animation-delay: 6s; transform: rotate(10deg); }
        .chain-link:nth-child(6) { top: 85%; left: -200px; animation-delay: 7.5s; transform: rotate(-5deg); }
        
        @keyframes chainPulse {
            0% {
                left: -200px;
                opacity: 0;
            }
            10% {
                opacity: 0.6;
            }
            90% {
                opacity: 0.6;
            }
            100% {
                left: calc(100% + 200px);
                opacity: 0;
            }
        }
        
        /* ============================================
           HEXAGON GRID PATTERN
           ============================================ */
        .hex-grid {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='49' viewBox='0 0 28 49'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%233b82f6' fill-opacity='0.03'%3E%3Cpath d='M13.99 9.25l13 7.5v15l-13 7.5L1 31.75v-15l12.99-7.5zM3 17.9v12.7l10.99 6.34 11-6.35V17.9l-11-6.34L3 17.9zM0 15l12.98-7.5V0h-2v6.35L0 12.69v2.3zm0 18.5L12.98 41v8h-2v-6.85L0 35.81v-2.3zM15 0v7.5L27.99 15H28v-2.31h-.01L17 6.35V0h-2zm0 49v-8l12.99-7.5H28v2.31h-.01L17 42.15V49h-2z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.5;
        }
        
        /* ============================================
           GLOWING ORB ACCENTS
           ============================================ */
        .glow-orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
        }
        
        .glow-orb-1 {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.15), transparent);
            top: -100px;
            right: -100px;
            animation: orbFloat 15s infinite ease-in-out;
        }
        
        .glow-orb-2 {
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.1), transparent);
            bottom: -50px;
            left: -50px;
            animation: orbFloat 20s infinite ease-in-out reverse;
        }
        
        .glow-orb-3 {
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.1), transparent);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: orbPulse 10s infinite ease-in-out;
        }
        
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(30px, 30px); }
        }
        
        @keyframes orbPulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
            50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }
        }
        
        /* ============================================
           DATA STREAM PARTICLES
           ============================================ */
        .data-particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
            overflow: hidden;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--accent-cyan);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-cyan), 0 0 20px var(--accent-blue);
            opacity: 0;
            animation: particleStream 6s infinite linear;
        }
        
        .particle:nth-child(1) { left: 10%; animation-delay: 0s; }
        .particle:nth-child(2) { left: 20%; animation-delay: 0.5s; }
        .particle:nth-child(3) { left: 30%; animation-delay: 1s; }
        .particle:nth-child(4) { left: 40%; animation-delay: 1.5s; }
        .particle:nth-child(5) { left: 50%; animation-delay: 2s; }
        .particle:nth-child(6) { left: 60%; animation-delay: 2.5s; }
        .particle:nth-child(7) { left: 70%; animation-delay: 3s; }
        .particle:nth-child(8) { left: 80%; animation-delay: 3.5s; }
        .particle:nth-child(9) { left: 90%; animation-delay: 4s; }
        .particle:nth-child(10) { left: 95%; animation-delay: 4.5s; }
        
        @keyframes particleStream {
            0% {
                transform: translateY(-10px);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(100vh);
                opacity: 0;
            }
        }
        
        /* ============================================
           MAIN CONTAINER
           ============================================ */
        .container {
            position: relative;
            z-index: 10;
            max-width: 1400px;
            margin: 0 auto;
            padding: 15px;
        }
        
        /* ============================================
           HEADER
           ============================================ */
        .header {
            text-align: center;
            margin-bottom: 25px;
            padding: 25px 15px;
            position: relative;
        }
        
        .header h1 {
            font-size: clamp(1.5rem, 5vw, 2.5rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan), var(--accent-purple));
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            animation: gradientShift 5s ease infinite;
            text-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            font-size: clamp(0.8rem, 2.5vw, 1rem);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .bsv-logo {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: linear-gradient(135deg, var(--bsv-orange), #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 600;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-top: 15px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .status-badge.online {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.4);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
        }
        
        .status-badge.offline {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
        }
        
        .pulse {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .pulse.green {
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green), 0 0 20px var(--accent-green);
        }
        
        .pulse.red {
            background: var(--accent-red);
            box-shadow: 0 0 10px var(--accent-red);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        
        /* ============================================
           GRID LAYOUT
           ============================================ */
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        @media (min-width: 640px) {
            .grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }
        }
        
        @media (min-width: 1024px) {
            .grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
        
        .grid-wide {
            grid-template-columns: 1fr !important;
        }
        
        /* ============================================
           CARDS
           ============================================ */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s ease;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .card:hover {
            border-color: var(--border-glow);
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.15), inset 0 0 20px rgba(59, 130, 246, 0.03);
            transform: translateY(-2px);
        }
        
        .card:hover::before {
            opacity: 1;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .card-icon {
            width: 40px;
            height: 40px;
            min-width: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            position: relative;
        }
        
        .card-icon::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            animation: iconPulse 3s infinite ease-in-out;
        }
        
        @keyframes iconPulse {
            0%, 100% { box-shadow: 0 0 0 0 transparent; }
            50% { box-shadow: 0 0 15px rgba(59, 130, 246, 0.3); }
        }
        
        .card-icon.blue { background: rgba(59, 130, 246, 0.15); }
        .card-icon.green { background: rgba(16, 185, 129, 0.15); }
        .card-icon.purple { background: rgba(139, 92, 246, 0.15); }
        .card-icon.yellow { background: rgba(245, 158, 11, 0.15); }
        .card-icon.cyan { background: rgba(6, 182, 212, 0.15); }
        
        .card-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* ============================================
           STATS
           ============================================ */
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        
        .stat-row:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        
        .stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            text-align: right;
            word-break: break-all;
        }
        
        .stat-value.highlight {
            color: var(--accent-blue);
            font-size: 1.3rem;
        }
        
        .stat-value.success { color: var(--accent-green); text-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }
        .stat-value.warning { color: var(--accent-yellow); text-shadow: 0 0 10px rgba(245, 158, 11, 0.3); }
        .stat-value.danger { color: var(--accent-red); }
        
        /* ============================================
           PROGRESS BAR
           ============================================ */
        .progress-container {
            margin-top: 15px;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .progress-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .progress-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--accent-cyan);
            font-weight: 600;
            text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }
        
        .progress-bar {
            height: 14px;
            background: rgba(17, 24, 39, 0.8);
            border-radius: 7px;
            overflow: hidden;
            position: relative;
            border: 1px solid var(--border-color);
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan), var(--accent-purple));
            background-size: 200% 100%;
            border-radius: 7px;
            transition: width 0.5s ease;
            position: relative;
            animation: progressGradient 3s linear infinite;
        }
        
        @keyframes progressGradient {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        /* ============================================
           BIG NUMBER DISPLAY
           ============================================ */
        .big-number-container {
            text-align: center;
            margin-bottom: 20px;
            padding: 20px 0;
        }
        
        .big-number {
            font-family: 'JetBrains Mono', monospace;
            font-size: clamp(2rem, 8vw, 3.5rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
            text-shadow: 0 0 40px rgba(59, 130, 246, 0.4);
            position: relative;
            display: inline-block;
        }
        
        .big-number::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%);
            width: 50%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
        }
        
        .big-number-label {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* ============================================
           PEERS TABLE
           ============================================ */
        .peers-table-container {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin: 0 -10px;
            padding: 0 10px;
        }
        
        .peers-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 400px;
        }
        
        .peers-table th,
        .peers-table td {
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .peers-table th {
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(0,0,0,0.2);
            position: sticky;
            top: 0;
        }
        
        .peers-table td {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
        }
        
        .peers-table tr:hover td {
            background: rgba(59, 130, 246, 0.05);
        }
        
        /* ============================================
           FOOTER
           ============================================ */
        .footer {
            text-align: center;
            padding: 25px 15px;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid rgba(255,255,255,0.03);
            margin-top: 20px;
        }
        
        .footer .last-update {
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-cyan);
        }
        
        .footer-brand {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        
        .footer-brand span {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 600;
        }
        
        /* ============================================
           ERROR STATE
           ============================================ */
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 12px;
            padding: 15px 20px;
            text-align: center;
            color: var(--accent-red);
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            font-size: 0.9rem;
        }
        
        /* ============================================
           REFRESH INDICATOR
           ============================================ */
        .refresh-indicator {
            position: fixed;
            bottom: 15px;
            right: 15px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            padding: 8px 14px;
            font-size: 0.7rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 100;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .refresh-indicator .spinner {
            width: 12px;
            height: 12px;
            border: 2px solid var(--border-color);
            border-top-color: var(--accent-cyan);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* ============================================
           BSV BADGE
           ============================================ */
        .bsv-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 10px;
            background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(245, 158, 11, 0.1));
            border: 1px solid rgba(234, 179, 8, 0.3);
            border-radius: 20px;
            font-size: 0.7rem;
            color: var(--bsv-orange);
            font-weight: 600;
        }
        
        /* ============================================
           MOBILE SPECIFIC
           ============================================ */
        @media (max-width: 640px) {
            .container {
                padding: 10px;
            }
            
            .card {
                padding: 15px;
                border-radius: 12px;
            }
            
            .header {
                padding: 20px 10px;
                margin-bottom: 15px;
            }
            
            .stat-row {
                padding: 8px 0;
            }
            
            .stat-label, .stat-value {
                font-size: 0.8rem;
            }
            
            .peers-table th,
            .peers-table td {
                padding: 10px 8px;
                font-size: 0.7rem;
            }
            
            .floating-block {
                display: none;
            }
            
            .chain-link {
                width: 100px;
            }
            
            .glow-orb {
                opacity: 0.5;
            }
        }
        
        /* ============================================
           TABLET
           ============================================ */
        @media (min-width: 641px) and (max-width: 1023px) {
            .grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        /* ============================================
           ANIMATIONS REDUCED MOTION
           ============================================ */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
            }
        }
    </style>
</head>
<body>
    <!-- Matrix Canvas -->
    <canvas id="matrix-canvas"></canvas>
    
    <!-- Hex Grid Pattern -->
    <div class="hex-grid"></div>
    
    <!-- Glowing Orbs -->
    <div class="glow-orb glow-orb-1"></div>
    <div class="glow-orb glow-orb-2"></div>
    <div class="glow-orb glow-orb-3"></div>
    
    <!-- Floating Blockchain Blocks -->
    <div class="blockchain-bg">
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
        <div class="floating-block"></div>
    </div>
    
    <!-- Chain Connections -->
    <div class="chain-connections">
        <div class="chain-link"></div>
        <div class="chain-link"></div>
        <div class="chain-link"></div>
        <div class="chain-link"></div>
        <div class="chain-link"></div>
        <div class="chain-link"></div>
    </div>
    
    <!-- Data Particles -->
    <div class="data-particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    
    <div class="container">
        <header class="header">
            <h1>⛓️ Teranode Monitor</h1>
            <p class="subtitle">
                <span class="bsv-badge">◆ BSV</span>
                Mainnet Node Dashboard
            </p>
            <div id="status-badge" class="status-badge {{ 'online' if status.online else 'offline' }}">
                <span class="pulse {{ 'green' if status.online else 'red' }}"></span>
                {{ 'Online - Syncing' if status.online else 'Offline' }}
            </div>
        </header>
        
        {% if status.error %}
        <div class="error-message">
            ⚠️ {{ status.error }}
        </div>
        {% endif %}
        
        <!-- Sync Progress -->
        <div class="grid grid-wide">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon blue">📊</div>
                    <span class="card-title">Sync Progress</span>
                </div>
                <div class="big-number-container">
                    <div class="big-number" id="block-height">{{ "{:,}".format(status.block_height) }}</div>
                    <div class="big-number-label">Current Block Height</div>
                </div>
                <div class="progress-container">
                    <div class="progress-header">
                        <span class="progress-label">Progress to Target ({{ "{:,}".format(status.target_height) }})</span>
                        <span class="progress-value" id="sync-percent">{{ status.sync_percentage }}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: {{ status.sync_percentage }}%"></div>
                    </div>
                </div>
                <div class="stat-row" style="margin-top: 15px;">
                    <span class="stat-label">Blocks Remaining</span>
                    <span class="stat-value warning" id="blocks-remaining">{{ "{:,}".format(status.blocks_remaining) }}</span>
                </div>
            </div>
        </div>
        
        <!-- Stats Grid -->
        <div class="grid">
            <!-- Blockchain Info -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon purple">🔗</div>
                    <span class="card-title">Blockchain</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Network</span>
                    <span class="stat-value">{{ status.chain | upper }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Best Block</span>
                    <span class="stat-value" style="font-size: 0.75rem;">{{ status.best_block_hash }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Difficulty</span>
                    <span class="stat-value">{{ "{:,.2f}".format(status.difficulty) }}</span>
                </div>
            </div>
            
            <!-- Network Info -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon green">🌐</div>
                    <span class="card-title">Network</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Connections</span>
                    <span class="stat-value {{ 'success' if status.connections > 0 else 'danger' }}" id="connections">{{ status.connections }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Protocol</span>
                    <span class="stat-value">{{ status.protocol_version }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Version</span>
                    <span class="stat-value">{{ status.version }}</span>
                </div>
            </div>
            
            <!-- Mempool Info -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon yellow">📦</div>
                    <span class="card-title">Mempool</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Transactions</span>
                    <span class="stat-value" id="mempool-size">{{ "{:,}".format(status.mempool_size) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Size</span>
                    <span class="stat-value" id="mempool-bytes">{{ "{:,.0f}".format(status.mempool_bytes / 1024) }} KB</span>
                </div>
            </div>
            
            <!-- Node Info -->
            <div class="card">
                <div class="card-header">
                    <div class="card-icon cyan">🖥️</div>
                    <span class="card-title">Node</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Host</span>
                    <span class="stat-value">{{ teranode_host }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Port</span>
                    <span class="stat-value">{{ teranode_port }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Status</span>
                    <span class="stat-value {{ 'success' if status.online else 'danger' }}">
                        {{ 'SYNCING' if status.online else 'OFFLINE' }}
                    </span>
                </div>
            </div>
        </div>
        
        <!-- Peers -->
        {% if status.peers %}
        <div class="grid grid-wide">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon green">👥</div>
                    <span class="card-title">Connected Peers</span>
                </div>
                <div class="peers-table-container">
                    <table class="peers-table">
                        <thead>
                            <tr>
                                <th>Address</th>
                                <th>Client</th>
                                <th>Synced</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for peer in status.peers %}
                            <tr>
                                <td>{{ peer.addr }}</td>
                                <td>{{ peer.subver }}</td>
                                <td>{{ "{:,}".format(peer.synced_blocks) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}
        
        <footer class="footer">
            <p>Last Updated: <span class="last-update" id="last-update">{{ status.last_update }}</span></p>
            <div class="footer-brand">
                <span>Teranode Monitor</span> • BSV Blockchain
            </div>
        </footer>
    </div>
    
    <div class="refresh-indicator">
        <div class="spinner"></div>
        Auto-refresh: 10s
    </div>
    
    <script>
        // ============================================
        // MATRIX RAIN ANIMATION - BLUE THEME
        // ============================================
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Matrix characters
        const chars = 'ᛒᛋᚡ01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン₿◆⛓∞<>/\\{}[]|#@$%^&*+=~`';
        const charArray = chars.split('');
        
        // Column settings
        const fontSize = 14;
        let columns = Math.floor(canvas.width / fontSize);
        let drops = Array(columns).fill(1);
        
        // Colors - Blue theme
        const colors = [
            'rgba(59, 130, 246, 0.8)',   // Blue
            'rgba(6, 182, 212, 0.8)',    // Cyan
            'rgba(139, 92, 246, 0.6)',   // Purple
            'rgba(59, 130, 246, 0.4)',   // Light blue
        ];
        
        function drawMatrix() {
            // Semi-transparent black to create fade effect
            ctx.fillStyle = 'rgba(10, 14, 23, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.font = fontSize + 'px JetBrains Mono, monospace';
            
            for (let i = 0; i < drops.length; i++) {
                // Random character
                const char = charArray[Math.floor(Math.random() * charArray.length)];
                
                // Random color from palette
                ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
                
                // Draw character
                ctx.fillText(char, i * fontSize, drops[i] * fontSize);
                
                // Reset drop when it reaches bottom or randomly
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    drops[i] = 0;
                }
                
                drops[i]++;
            }
        }
        
        // Run matrix animation
        setInterval(drawMatrix, 50);
        
        // Handle resize
        window.addEventListener('resize', () => {
            columns = Math.floor(canvas.width / fontSize);
            drops = Array(columns).fill(1);
        });
        
        // ============================================
        // AUTO-REFRESH DATA
        // ============================================
        function refreshData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update values with animation
                    animateValue('block-height', data.block_height);
                    document.getElementById('sync-percent').textContent = data.sync_percentage + '%';
                    document.getElementById('progress-fill').style.width = data.sync_percentage + '%';
                    document.getElementById('blocks-remaining').textContent = data.blocks_remaining.toLocaleString();
                    document.getElementById('connections').textContent = data.connections;
                    document.getElementById('mempool-size').textContent = data.mempool_size.toLocaleString();
                    document.getElementById('mempool-bytes').textContent = (data.mempool_bytes / 1024).toFixed(0) + ' KB';
                    document.getElementById('last-update').textContent = data.last_update;
                    
                    // Update status badge
                    const badge = document.getElementById('status-badge');
                    if (data.online) {
                        badge.className = 'status-badge online';
                        badge.innerHTML = '<span class="pulse green"></span> Online - Syncing';
                    } else {
                        badge.className = 'status-badge offline';
                        badge.innerHTML = '<span class="pulse red"></span> Offline';
                    }
                })
                .catch(error => console.error('Error fetching status:', error));
        }
        
        // Animate number changes
        function animateValue(id, newValue) {
            const element = document.getElementById(id);
            element.textContent = newValue.toLocaleString();
        }
        
        // Refresh every 10 seconds
        setInterval(refreshData, 10000);
        
        // ============================================
        // TOUCH FEEDBACK FOR MOBILE
        // ============================================
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            });
            card.addEventListener('touchend', function() {
                this.style.transform = '';
            });
        });
    </script>
</body>
</html>
"""

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    status = get_node_status()
    return render_template_string(
        HTML_TEMPLATE,
        status=status,
        teranode_host=TERANODE_HOST,
        teranode_port=TERANODE_RPC_PORT
    )

@app.route('/api/status')
def api_status():
    status = get_node_status()
    return jsonify(status)

@app.route('/api/health')
def api_health():
    status = get_node_status()
    return jsonify({
        "healthy": status["online"],
        "block_height": status["block_height"],
        "connections": status["connections"]
    })

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║         TERANODE MONITOR WEB DASHBOARD - ENHANCED             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  🌐 Dashboard URL:  http://{FLASK_HOST}:{FLASK_PORT}                          ║
║  🔗 Teranode RPC:   http://{TERANODE_HOST}:{TERANODE_RPC_PORT}                      ║
║                                                               ║
║  ✨ Features:                                                 ║
║     • Blue Matrix Rain Animation                              ║
║     • Floating Blockchain Blocks                              ║
║     • Chain Connection Animations                             ║
║     • Data Stream Particles                                   ║
║     • Mobile-Responsive Design                                ║
║     • Touch-Optimized UI                                      ║
║                                                               ║
║  📡 API Endpoints:                                            ║
║     GET /           - Web Dashboard                           ║
║     GET /api/status - JSON Status                             ║
║     GET /api/health - Health Check                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)
