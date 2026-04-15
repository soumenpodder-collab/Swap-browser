from flask import Flask, request, jsonify, render_template_string
import json
import os
import uuid

app = Flask(__name__)
STORAGE_DIR = "projects"

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# --- THE FRONTEND PAGE ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>NexusDB | Dashboard</title>
    <style>
        :root { --primary: #2563eb; --bg: #f8fafc; --card: #ffffff; --text: #1e293b; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; }
        
        /* Navigation */
        nav { background: #1e293b; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        .nav-links button { background: none; border: none; color: #cbd5e1; cursor: pointer; margin-left: 15px; font-size: 14px; }
        .nav-links button.active { color: white; font-weight: bold; border-bottom: 2px solid var(--primary); }

        .container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
        .card { background: var(--card); border-radius: 12px; padding: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
        
        /* Buttons & Inputs */
        button.main-btn { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
        input { padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; width: 250px; }

        /* Table Design (Frontend View) */
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #f1f5f9; text-align: left; padding: 12px; font-size: 14px; }
        td { padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }

        /* JSON Design (Backend View) */
        pre { background: #1e293b; color: #38bdf8; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 13px; }
        
        .hidden { display: none; }
    </style>
</head>
<body>

<nav>
    <strong>NexusDB</strong>
    <div class="nav-links">
        <button id="btn-gen" class="active" onclick="showTab('generator')">API Generator</button>
        <button id="btn-front" onclick="showTab('frontend')">Frontend View</button>
        <button id="btn-back" onclick="showTab('backend')">Backend JSON</button>
    </div>
</nav>

<div class="container">
    <div id="tab-generator" class="card">
        <h2>Generate New Project</h2>
        <p>Create a unique endpoint for your web forms.</p>
        <button class="main-btn" onclick="createAPI()">Generate API Key</button>
        <div id="gen-result" style="margin-top:15px; font-family:monospace; color:var(--primary); font-weight:bold;"></div>
    </div>

    <div class="card">
        <h3>Database Access</h3>
        <input type="text" id="userKey" placeholder="Enter API Key">
        <button class="main-btn" onclick="refreshData()">Load Data</button>
    </div>

    <div id="tab-frontend" class="card hidden">
        <h2>Data Rows</h2>
        <div id="table-container">
            <p style="color:gray">No data loaded yet.</p>
        </div>
    </div>

    <div id="tab-backend" class="card hidden">
        <h2>Raw JSON Output</h2>
        <div id="json-container">
            <p style="color:gray">No data loaded yet.</p>
        </div>
    </div>
</div>

<script>
    let currentData = [];

    function showTab(tabName) {
        // Switch visibility
        document.getElementById('tab-generator').classList.add('hidden');
        document.getElementById('tab-frontend').classList.add('hidden');
        document.getElementById('tab-backend').classList.add('hidden');
        document.getElementById('tab-' + tabName).classList.remove('hidden');

        // Update nav styling
        document.querySelectorAll('.nav-links button').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-' + tabName.substring(0,4)).classList.add('active');
    }

    async function createAPI() {
        const res = await fetch('/generate-key', { method: 'POST' });
        const data = await res.json();
        document.getElementById('gen-result').innerText = "Your Key: " + data.key;
    }

    async function refreshData() {
        const key = document.getElementById('userKey').value;
        const res = await fetch('/view/' + key);
        const data = await res.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }

        currentData = data.submissions;
        renderTable();
        renderJSON();
    }

    function renderTable() {
        if (currentData.length === 0) return;
        
        // Get headers from the keys of the first object
        const headers = Object.keys(currentData[0]);
        let html = '<table><thead><tr>';
        headers.forEach(h => html += `<th>${h.toUpperCase()}</th>`);
        html += '</tr></thead><tbody>';

        currentData.forEach(row => {
            html += '<tr>';
            headers.forEach(h => html += `<td>${row[h] || ''}</td>`);
            html += '</tr>';
        });
        html += '</tbody></table>';
        document.getElementById('table-container').innerHTML = html;
    }

    function renderJSON() {
        document.getElementById('json-container').innerHTML = 
            '<pre>' + JSON.stringify(currentData, null, 2) + '</pre>';
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/generate-key', methods=['POST'])
def generate_key():
    new_key = str(uuid.uuid4())[:8]
    # Create an empty file for this user
    with open(f"{STORAGE_DIR}/{new_key}.json", "w") as f:
        f.write("") 
    return jsonify({"key": new_key})

@app.route('/api/<api_key>', methods=['POST'])
def receive_data(api_key):
    project_path = f"{STORAGE_DIR}/{api_key}.json"
    if not os.path.exists(project_path):
        return jsonify({"error": "Invalid API Key"}), 404

    data = request.json if request.is_json else request.form.to_dict()
    with open(project_path, "a") as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({"status": "success"})

# --- THE NEW VIEW ROUTE ---
@app.route('/view/<api_key>', methods=['GET'])
def view_db(api_key):
    project_path = f"{STORAGE_DIR}/{api_key}.json"
    if not os.path.exists(project_path):
        return jsonify({"error": "Key not found"}), 404

    submissions = []
    with open(project_path, "r") as f:
        for line in f:
            if line.strip():
                submissions.append(json.loads(line))
    
    return jsonify({"submissions": submissions})

if __name__ == "__main__":
    app.run(debug=True, port=5000)