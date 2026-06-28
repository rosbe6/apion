#!/usr/bin/env python3
"""Simple web dashboard para ver logs del bot en vivo"""

from flask import Flask, render_template_string
import os
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Apion Bot - Logs Viewer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Monaco', 'Menlo', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            line-height: 1.5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #252526;
            border-radius: 5px;
            border-left: 4px solid #007acc;
        }
        .header h1 {
            color: #4ec9b0;
            font-size: 24px;
        }
        .status {
            display: flex;
            gap: 20px;
            font-size: 14px;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4ec9b0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .logs {
            background: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 5px;
            padding: 15px;
            max-height: 600px;
            overflow-y: auto;
            font-size: 13px;
        }
        .log-line {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 3px;
        }
        .log-line.error {
            color: #f48771;
            background: rgba(244, 135, 113, 0.1);
            border-left: 2px solid #f48771;
            padding-left: 8px;
        }
        .log-line.info {
            color: #9cdcfe;
        }
        .log-line.debug {
            color: #858585;
        }
        .log-line.warning {
            color: #ce9178;
            background: rgba(206, 145, 120, 0.1);
            border-left: 2px solid #ce9178;
            padding-left: 8px;
        }
        .footer {
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            color: #858585;
            font-size: 12px;
        }
        /* Scrollbar personalizada */
        .logs::-webkit-scrollbar {
            width: 8px;
        }
        .logs::-webkit-scrollbar-track {
            background: #1e1e1e;
        }
        .logs::-webkit-scrollbar-thumb {
            background: #404040;
            border-radius: 4px;
        }
        .logs::-webkit-scrollbar-thumb:hover {
            background: #505050;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Apion Bot - Logs Viewer</h1>
            <div class="status">
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>En vivo</span>
                </div>
                <div class="status-item">
                    <span>Actualiza cada 5 segundos</span>
                </div>
                <div class="status-item">
                    <span id="time"></span>
                </div>
            </div>
        </div>

        <div class="logs" id="logs">
            <div class="log-line info">Cargando logs...</div>
        </div>

        <div class="footer">
            <p>📊 Dashboard de logs | Auto-refresh cada 5s | Última actualización: <span id="last-update"></span></p>
        </div>
    </div>

    <script>
        function updateTime() {
            const now = new Date();
            document.getElementById('time').textContent = now.toLocaleTimeString();
            document.getElementById('last-update').textContent = now.toLocaleTimeString();
        }
        updateTime();
        setInterval(updateTime, 1000);

        // Desplazarse al final automáticamente
        document.addEventListener('DOMContentLoaded', function() {
            const logs = document.getElementById('logs');
            setTimeout(() => {
                logs.scrollTop = logs.scrollHeight;
            }, 100);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def logs():
    log_file = '/home/bot/apion/logs/bot.log'

    if not os.path.exists(log_file):
        return render_template_string(HTML_TEMPLATE, logs_content="<div class='log-line error'>❌ Archivo de logs no encontrado</div>")

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Últimas 100 líneas
            lines = lines[-100:]

        logs_html = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Colorear por tipo
            if "ERROR" in line:
                logs_html += f'<div class="log-line error">{line}</div>'
            elif "WARNING" in line:
                logs_html += f'<div class="log-line warning">{line}</div>'
            elif "DEBUG" in line:
                logs_html += f'<div class="log-line debug">{line}</div>'
            else:
                logs_html += f'<div class="log-line info">{line}</div>'

        return render_template_string(
            HTML_TEMPLATE.replace(
                '<div class="log-line info">Cargando logs...</div>',
                logs_html
            )
        )
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, logs_content=f"<div class='log-line error'>Error: {str(e)}</div>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
