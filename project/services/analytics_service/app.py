from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import sys
import os
import json

# Add project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.logger import setup_logger

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logger = setup_logger(__name__)

# Define paths for Spark jobs and results
SPARK_JOBS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'spark_jobs')
RESULTS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'spark_results')

# Ensure the results directory exists
os.makedirs(RESULTS_PATH, exist_ok=True)

@app.route('/analytics/run', methods=['POST'])
def run_spark_jobs():
    """Endpoint to trigger all Spark analytics jobs."""
    logger.info("Received request to run Spark jobs.")
    
    jobs = [
        'portfolio_analysis.py',
        'volume_analysis.py',
        'profit_analysis.py'
    ]
    
    results = {}
    
    for job_script in jobs:
        script_path = os.path.join(SPARK_JOBS_PATH, job_script)
        if not os.path.exists(script_path):
            error_msg = f"Spark job script not found: {job_script}"
            logger.error(error_msg)
            results[job_script] = {'status': 'error', 'message': error_msg}
            continue
            
        try:
            logger.info(f"Running Spark job: {job_script}...")
            # Using sys.executable to ensure the correct Python interpreter is used
            process = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=True,  # This will raise CalledProcessError if the script fails
                timeout=300  # 5-minute timeout for the job
            )
            logger.info(f"Spark job {job_script} completed successfully.")
            results[job_script] = {
                'status': 'success',
                'output': process.stdout
            }
        except subprocess.CalledProcessError as e:
            error_msg = f"Error running {job_script}: {e.stderr}"
            logger.error(error_msg)
            results[job_script] = {'status': 'error', 'message': error_msg, 'stdout': e.stdout}
        except subprocess.TimeoutExpired:
            error_msg = f"Spark job {job_script} timed out."
            logger.error(error_msg)
            results[job_script] = {'status': 'error', 'message': error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred with {job_script}: {str(e)}"
            logger.error(error_msg)
            results[job_script] = {'status': 'error', 'message': error_msg}
            
    all_successful = all(res['status'] == 'success' for res in results.values())
    
    if all_successful:
        return jsonify({
            'message': 'All Spark jobs completed successfully.',
            'results': results
        }), 200
    else:
        return jsonify({
            'message': 'One or more Spark jobs failed.',
            'results': results
        }), 500


def serve_json_file(filename):
    """Helper function to read and serve a JSON file from the results directory."""
    filepath = os.path.join(RESULTS_PATH, filename)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        logger.warning(f"Analytics file not found: {filename}. Run the Spark jobs first.")
        return jsonify({'error': f'Analytics file not found: {filename}. Please run the analytics jobs first.'}), 404
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {filename}.")
        return jsonify({'error': f'Error reading analytics data from {filename}.'}), 500

@app.route('/analytics/portfolio', methods=['GET'])
def get_portfolio_analysis():
    return serve_json_file('portfolio_analysis.json')

@app.route('/analytics/volume', methods=['GET'])
def get_volume_analysis():
    return serve_json_file('volume_analysis.json')

@app.route('/analytics/profit', methods=['GET'])
def get_profit_analysis():
    return serve_json_file('user_profits.json')
    
@app.route('/analytics/top-performers', methods=['GET'])
def get_top_performers():
    return serve_json_file('top_performers.json')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'analytics_service'})


if __name__ == '__main__':
    logger.info("Starting Analytics Service on port 5005")
    app.run(host='0.0.0.0', port=5005, debug=True, use_reloader=False)
