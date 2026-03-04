"""
web_dashboard.py — Web dashboard for the Server Health Check Bot.

Provides a real-time HTTP-based dashboard for monitoring server metrics.
"""

from flask import Flask, jsonify, render_template
import psutil

from dashboard import _collect_metrics as collect_metrics
from logger import get_logger

logger = get_logger("web_dashboard")
app = Flask(__name__)


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/api/metrics")
def get_metrics():
    """Return the currently collected server metrics as JSON."""
    try:
        metrics = collect_metrics()
        
        # Collect top processes
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
            try:
                # To avoid blocking, we won't use interval>0 for cpu_percent here.
                # It might yield 0.0 on the first call.
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by memory usage as a reliable metric
        procs = sorted(procs, key=lambda p: p['memory_info'].rss if p['memory_info'] else 0, reverse=True)[:5]
        
        formatted_procs = []
        for p in procs:
            cpu = p.get('cpu_percent', 0.0)
            mem_mb = (p['memory_info'].rss / (1024 * 1024)) if p['memory_info'] else 0
            formatted_procs.append({
                "name": p['name'],
                "cpu": f"{cpu}%",
                "memory": f"{mem_mb:.1f} MB"
            })
            
        metrics['top_processes'] = formatted_procs
        
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting web dashboard on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
