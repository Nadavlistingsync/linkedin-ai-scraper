from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
import json
from datetime import datetime
import logging

# Import our modules
import sys
sys.path.append('..')

from config import Config
from linkedin_scraper import LinkedInScraper
from data_processor import DataProcessor
from utils import setup_logging

app = Flask(__name__)

# Global variables for job tracking
current_job = None
job_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'total_profiles': 0,
    'found_profiles': 0,
    'start_time': None,
    'end_time': None,
    'error': None
}

def setup_web_logging():
    """Setup logging for web application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_web_logging()

@app.route('/')
def index():
    """Main page"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn AI Agent Scraper</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                color: #fff;
                font-size: 2.5em;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="email"], input[type="password"] {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                box-sizing: border-box;
            }
            .btn {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
                margin: 5px;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .progress-container {
                margin: 20px 0;
                display: none;
            }
            .progress-bar {
                width: 100%;
                height: 20px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(45deg, #00b894, #00cec9);
                transition: width 0.3s ease;
                border-radius: 10px;
            }
            .status {
                margin: 20px 0;
                padding: 15px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                display: none;
            }
            .download-section {
                margin-top: 30px;
                text-align: center;
                display: none;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #00b894;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 LinkedIn AI Agent Scraper</h1>
            
            <form id="scrapingForm">
                <div class="form-group">
                    <label for="email">LinkedIn Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">LinkedIn Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn" id="startBtn">🚀 Start Scraping</button>
                <button type="button" class="btn" id="stopBtn" style="display: none;">⏹️ Stop Scraping</button>
            </form>
            
            <div class="progress-container" id="progressContainer">
                <h3>Progress</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p id="progressText">Initializing...</p>
            </div>
            
            <div class="status" id="status">
                <h3>Status</h3>
                <div id="statusContent"></div>
            </div>
            
            <div class="stats" id="stats" style="display: none;">
                <div class="stat-card">
                    <div class="stat-number" id="totalProfiles">0</div>
                    <div>Total Profiles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="foundProfiles">0</div>
                    <div>Found Profiles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="progressPercent">0%</div>
                    <div>Progress</div>
                </div>
            </div>
            
            <div class="download-section" id="downloadSection">
                <h3>📊 Download Results</h3>
                <button class="btn" onclick="downloadCSV()">📥 Download CSV</button>
                <button class="btn" onclick="downloadSummary()">📋 Download Summary</button>
            </div>
        </div>

        <script>
            let statusInterval;
            
            document.getElementById('scrapingForm').addEventListener('submit', function(e) {
                e.preventDefault();
                startScraping();
            });
            
            document.getElementById('stopBtn').addEventListener('click', function() {
                stopScraping();
            });
            
            function startScraping() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                fetch('/api/start_scraping', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        document.getElementById('startBtn').style.display = 'none';
                        document.getElementById('stopBtn').style.display = 'inline-block';
                        document.getElementById('progressContainer').style.display = 'block';
                        document.getElementById('status').style.display = 'block';
                        document.getElementById('stats').style.display = 'grid';
                        
                        // Start polling for status
                        statusInterval = setInterval(updateStatus, 2000);
                    }
                })
                .catch(error => {
                    alert('Error: ' + error);
                });
            }
            
            function stopScraping() {
                fetch('/api/stop_scraping', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    clearInterval(statusInterval);
                    document.getElementById('startBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                });
            }
            
            function updateStatus() {
                fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const progressFill = document.getElementById('progressFill');
                    const progressText = document.getElementById('progressText');
                    const statusContent = document.getElementById('statusContent');
                    const totalProfiles = document.getElementById('totalProfiles');
                    const foundProfiles = document.getElementById('foundProfiles');
                    const progressPercent = document.getElementById('progressPercent');
                    
                    progressFill.style.width = data.progress + '%';
                    progressText.textContent = data.message;
                    statusContent.innerHTML = `
                        <p><strong>Status:</strong> ${data.running ? 'Running' : 'Stopped'}</p>
                        <p><strong>Message:</strong> ${data.message}</p>
                        ${data.error ? `<p><strong>Error:</strong> ${data.error}</p>` : ''}
                        ${data.start_time ? `<p><strong>Started:</strong> ${new Date(data.start_time).toLocaleString()}</p>` : ''}
                        ${data.end_time ? `<p><strong>Ended:</strong> ${new Date(data.end_time).toLocaleString()}</p>` : ''}
                    `;
                    
                    totalProfiles.textContent = data.total_profiles;
                    foundProfiles.textContent = data.found_profiles;
                    progressPercent.textContent = Math.round(data.progress) + '%';
                    
                    if (!data.running && data.total_profiles > 0) {
                        clearInterval(statusInterval);
                        document.getElementById('startBtn').style.display = 'inline-block';
                        document.getElementById('stopBtn').style.display = 'none';
                        document.getElementById('downloadSection').style.display = 'block';
                    }
                });
            }
            
            function downloadCSV() {
                window.location.href = '/api/download_csv';
            }
            
            function downloadSummary() {
                window.location.href = '/api/download_summary';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping job"""
    global current_job, job_status
    
    if job_status['running']:
        return jsonify({'error': 'Job already running'}), 400
    
    # Get credentials from request
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Reset job status
    job_status.update({
        'running': True,
        'progress': 0,
        'message': 'Initializing scraper...',
        'total_profiles': 0,
        'found_profiles': 0,
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'error': None
    })
    
    # For Vercel, we'll return a message that this is a demo
    # In production, you'd need to handle the actual scraping differently
    job_status['message'] = 'Demo mode - Scraping would start here'
    job_status['progress'] = 50
    job_status['running'] = False
    job_status['total_profiles'] = 1000
    job_status['found_profiles'] = 1000
    
    return jsonify({'message': 'Demo mode - Scraping simulation started'})

@app.route('/api/status')
def get_status():
    """Get current job status"""
    return jsonify(job_status)

@app.route('/api/stop_scraping', methods=['POST'])
def stop_scraping():
    """Stop the current scraping job"""
    global job_status
    
    if job_status['running']:
        job_status['running'] = False
        job_status['message'] = 'Stopping scraper...'
        return jsonify({'message': 'Stopping scraper...'})
    else:
        return jsonify({'error': 'No job running'}), 400

@app.route('/api/download_csv')
def download_csv():
    """Download the CSV file"""
    return jsonify({'message': 'Demo mode - CSV download would work here'})

@app.route('/api/download_summary')
def download_summary():
    """Download the summary report"""
    return jsonify({'message': 'Demo mode - Summary download would work here'})

# For Vercel serverless
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 