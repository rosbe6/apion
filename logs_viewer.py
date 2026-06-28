#!/usr/bin/env python3
"""Multi-log web dashboard with tabs"""

from flask import Flask, render_template_string, Response
import os
import time

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Apion Bot - Logs Viewer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
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
            margin-bottom: 20px;
            padding: 15px;
            background: #252526;
            border-radius: 5px;
            border-left: 4px solid #007acc;
        }
        .header h1 {
            color: #4ec9b0;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .status {
            display: flex;
            gap: 20px;
            font-size: 12px;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ec9b0;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
            border-bottom: 2px solid #404040;
        }
        .tab-btn {
            padding: 10px 20px;
            background: #252526;
            border: none;
            color: #858585;
            cursor: pointer;
            font-family: monospace;
            font-size: 13px;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab-btn:hover {
            color: #d4d4d4;
        }
        .tab-btn.active {
            color: #4ec9b0;
            border-bottom-color: #4ec9b0;
        }
        .logs {
            background: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 5px;
            padding: 15px;
            height: 600px;
            overflow-y: auto;
            font-size: 12px;
            display: none;
        }
        .logs.active {
            display: block;
        }
        .log-line {
            margin-bottom: 4px;
            padding: 4px;
            border-radius: 3px;
            word-break: break-word;
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
        .log-line.success {
            color: #6a9955;
        }
        .footer {
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            color: #858585;
            font-size: 11px;
        }
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
            <h1>🚀 Apion Bot - Logs En Vivo</h1>
            <div class="status">
                <div class="status-item">
                    <div class="status-dot"></div>
                    <span>En tiempo real</span>
                </div>
                <div class="status-item">
                    <span id="time"></span>
                </div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('bot')">🤖 Bot</button>
            <button class="tab-btn" onclick="switchTab('paypal')">💳 PayPal API</button>
            <button class="tab-btn" onclick="switchTab('promerica')">🏦 Promerica API</button>
        </div>

        <div id="bot" class="logs active">
            <div class="log-line info">Conectando a logs del bot...</div>
        </div>
        <div id="paypal" class="logs">
            <div class="log-line info">Conectando a logs de PayPal...</div>
        </div>
        <div id="promerica" class="logs">
            <div class="log-line info">Conectando a logs de Promerica...</div>
        </div>

        <div class="footer">
            <p>📊 Dashboard de logs en tiempo real | Última actualización: <span id="last-update">--:--:--</span></p>
        </div>
    </div>

    <script>
        let streams = {};

        function updateTime() {
            const now = new Date();
            document.getElementById('time').textContent = now.toLocaleTimeString();
        }
        updateTime();
        setInterval(updateTime, 1000);

        function switchTab(tab) {
            document.querySelectorAll('.logs').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');

            if (!streams[tab]) {
                connectToStream(tab);
            }
        }

        function connectToStream(logType) {
            const logDiv = document.getElementById(logType);
            logDiv.innerHTML = '';

            const eventSource = new EventSource(`/stream/${logType}`);

            eventSource.onmessage = function(event) {
                const line = event.data;
                if (!line) return;

                const logLine = document.createElement('div');
                logLine.className = 'log-line';

                if (line.includes('ERROR') || line.includes('❌')) {
                    logLine.classList.add('error');
                } else if (line.includes('WARNING') || line.includes('⚠️')) {
                    logLine.classList.add('warning');
                } else if (line.includes('DEBUG')) {
                    logLine.classList.add('debug');
                } else if (line.includes('✅') || line.includes('SUCCESS')) {
                    logLine.classList.add('success');
                } else {
                    logLine.classList.add('info');
                }

                logLine.textContent = line;
                logDiv.appendChild(logLine);
                logDiv.scrollTop = logDiv.scrollHeight;
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            };

            eventSource.onerror = function() {
                logDiv.innerHTML = '<div class="log-line error">❌ Conexión perdida. Reconectando...</div>';
                eventSource.close();
                setTimeout(() => connectToStream(logType), 3000);
            };

            streams[logType] = eventSource;
        }

        connectToStream('bot');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/stream/<log_type>')
def stream(log_type):
    """Stream logs based on type"""
    log_files = {
        'bot': '/home/bot/apion/logs/bot.log',
        'paypal': '/home/bot/apion/logs/paypal.log',
        'promerica': '/home/bot/apion/logs/promerica.log'
    }

    log_file = log_files.get(log_type)
    if not log_file or not os.path.exists(log_file):
        def error_generator():
            yield f"data: ❌ Archivo de logs no encontrado: {log_type}\n\n"
        return Response(error_generator(), mimetype='text/event-stream')

    def generate():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        line = line.rstrip('\n')
                        yield f"data: {line}\n\n"
                    else:
                        time.sleep(0.1)
        except Exception as e:
            yield f"data: ❌ Error: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
