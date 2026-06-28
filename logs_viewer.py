#!/usr/bin/env python3
"""Real-time web dashboard para ver logs del bot"""

from flask import Flask, render_template_string, Response
import os
import time
import threading

app = Flask(__name__)

# Variable para trackear la posición del archivo
file_position = 0
file_lock = threading.Lock()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Apion Bot - Logs Viewer (En Vivo)</title>
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
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .logs {
            background: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 5px;
            padding: 15px;
            height: 600px;
            overflow-y: auto;
            font-size: 13px;
        }
        .log-line {
            margin-bottom: 5px;
            padding: 5px;
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
        .footer {
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            color: #858585;
            font-size: 12px;
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

        <div class="logs" id="logs">
            <div class="log-line info">Conectando a logs en vivo...</div>
        </div>

        <div class="footer">
            <p>📊 Dashboard de logs en tiempo real | Última línea: <span id="last-update">--:--:--</span></p>
        </div>
    </div>

    <script>
        const logsDiv = document.getElementById('logs');

        function updateTime() {
            const now = new Date();
            document.getElementById('time').textContent = now.toLocaleTimeString();
        }
        updateTime();
        setInterval(updateTime, 1000);

        function connectToStream() {
            const eventSource = new EventSource('/stream');

            eventSource.onmessage = function(event) {
                const line = event.data;
                if (!line) return;

                const logLine = document.createElement('div');
                logLine.className = 'log-line';

                if (line.includes('ERROR')) {
                    logLine.classList.add('error');
                } else if (line.includes('WARNING')) {
                    logLine.classList.add('warning');
                } else if (line.includes('DEBUG')) {
                    logLine.classList.add('debug');
                } else {
                    logLine.classList.add('info');
                }

                logLine.textContent = line;
                logsDiv.appendChild(logLine);

                // Desplazarse al final
                logsDiv.scrollTop = logsDiv.scrollHeight;

                // Actualizar timestamp
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            };

            eventSource.onerror = function() {
                logsDiv.innerHTML = '<div class="log-line error">❌ Conexión perdida. Reconectando...</div>';
                eventSource.close();
                setTimeout(connectToStream, 3000);
            };
        }

        connectToStream();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/stream')
def stream():
    """Envía los logs en tiempo real usando Server-Sent Events"""
    log_file = '/home/bot/apion/logs/bot.log'

    if not os.path.exists(log_file):
        def error_generator():
            yield f"data: ❌ Archivo de logs no encontrado\n\n"
        return Response(error_generator(), mimetype='text/event-stream')

    def generate():
        global file_position

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Ir al final del archivo
                f.seek(0, 2)
                file_position = f.tell()

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
