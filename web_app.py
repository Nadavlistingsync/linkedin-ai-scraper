from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
import json
from datetime import datetime
import logging

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
            logging.FileHandler('web_app.log'),
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
                
                fetch('/start_scraping', {
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
                fetch('/stop_scraping', {
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
                fetch('/status')
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
                window.location.href = '/download_csv';
            }
            
            function downloadSummary() {
                window.location.href = '/download_summary';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/start_scraping', methods=['POST'])
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
    
    # Start scraping in background thread
    def run_scraping():
        global current_job, job_status
        
        try:
            # Set environment variables
            os.environ['LINKEDIN_EMAIL'] = email
            os.environ['LINKEDIN_PASSWORD'] = password
            
            # Initialize scraper
            config = Config()
            scraper = LinkedInScraper(config)
            data_processor = DataProcessor(config.OUTPUT_CSV)
            
            job_status['message'] = 'Logging into LinkedIn...'
            
            # Login
            if not scraper.login():
                job_status['error'] = 'Failed to login to LinkedIn. Check credentials.'
                job_status['running'] = False
                return
            
            job_status['message'] = 'Starting comprehensive search...'
            job_status['progress'] = 10
            
            # Run searches
            all_profiles = []
            total_keywords = len(config.SEARCH_KEYWORDS) + len(config.TARGET_COMPANIES)
            current_search = 0
            
            # Search by keywords
            for keyword in config.SEARCH_KEYWORDS:
                if not job_status['running']:
                    break
                
                job_status['message'] = f'Searching: {keyword}'
                profiles = scraper.search_profiles(keyword, max_pages=2)
                all_profiles.extend(profiles)
                
                current_search += 1
                job_status['progress'] = 10 + (current_search / total_keywords) * 70
                job_status['found_profiles'] = len(all_profiles)
                
                time.sleep(2)  # Rate limiting
            
            # Search by companies
            for company in config.TARGET_COMPANIES:
                if not job_status['running']:
                    break
                
                job_status['message'] = f'Searching company: {company}'
                profiles = scraper.search_by_company(company)
                all_profiles.extend(profiles)
                
                current_search += 1
                job_status['progress'] = 10 + (current_search / total_keywords) * 70
                job_status['found_profiles'] = len(all_profiles)
                
                time.sleep(2)  # Rate limiting
            
            job_status['message'] = 'Processing and saving profiles...'
            job_status['progress'] = 80
            
            # Process profiles
            if all_profiles:
                # Load existing profiles for deduplication
                existing_df = data_processor.load_existing_profiles()
                
                # Deduplicate profiles
                deduplicated_profiles = data_processor.deduplicate_profiles(all_profiles, existing_df)
                
                # Filter by quality
                filtered_profiles = data_processor.filter_by_quality(
                    deduplicated_profiles,
                    min_confidence=config.CONFIDENCE_THRESHOLD,
                    min_completeness=config.MIN_PROFILE_COMPLETENESS
                )
                
                # Sort by quality
                sorted_profiles = data_processor.sort_by_quality(filtered_profiles)
                
                # Save to CSV
                success = data_processor.save_profiles_to_csv(sorted_profiles)
                
                if success:
                    # Generate summary report
                    summary = data_processor.generate_summary_report(sorted_profiles)
                    data_processor.export_summary_report(summary)
                    
                    job_status['message'] = f'Successfully saved {len(sorted_profiles)} profiles!'
                    job_status['total_profiles'] = len(sorted_profiles)
                    job_status['progress'] = 100
                else:
                    job_status['error'] = 'Failed to save profiles to CSV'
            else:
                job_status['error'] = 'No profiles found during search'
            
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            job_status['error'] = f'Scraping failed: {str(e)}'
        
        finally:
            job_status['running'] = False
            job_status['end_time'] = datetime.now().isoformat()
            
            if scraper:
                scraper.close()
    
    # Start the scraping thread
    current_job = threading.Thread(target=run_scraping)
    current_job.daemon = True
    current_job.start()
    
    return jsonify({'message': 'Scraping started successfully'})

@app.route('/status')
def get_status():
    """Get current job status"""
    return jsonify(job_status)

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    """Stop the current scraping job"""
    global job_status
    
    if job_status['running']:
        job_status['running'] = False
        job_status['message'] = 'Stopping scraper...'
        return jsonify({'message': 'Stopping scraper...'})
    else:
        return jsonify({'error': 'No job running'}), 400

@app.route('/download_csv')
def download_csv():
    """Download the CSV file"""
    config = Config()
    csv_file = config.OUTPUT_CSV
    
    if os.path.exists(csv_file):
        return send_file(csv_file, as_attachment=True, download_name='ai_agent_profiles.csv')
    else:
        return jsonify({'error': 'CSV file not found'}), 404

@app.route('/download_summary')
def download_summary():
    """Download the summary report"""
    summary_file = 'scraping_summary.txt'
    
    if os.path.exists(summary_file):
        return send_file(summary_file, as_attachment=True, download_name='scraping_summary.txt')
    else:
        return jsonify({'error': 'Summary file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 