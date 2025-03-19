from flask import Flask, render_template, request
import webbrowser
import json
import os

app = Flask(__name__)

# Function to load config from secrets/config.json
def load_config():
    config_path = os.path.join('secrets', 'config.json')
    default_config = {'creator': '', 'openai_key': '', 'projects': []}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            if 'projects' not in config:
                config['projects'] = []
            return config
    return default_config

@app.route('/', methods=['GET', 'POST'])
def index():
    # Load existing config
    config = load_config()
    prefilled_data = {
        'creator': config.get('creator', ''),
        'openai_key': config.get('openai_key', ''),
        'projects': config.get('projects', [])
    }

    error = None
    if request.method == 'POST':
        project_name = request.form['project_name']
        # Check if project name already exists
        if project_name in prefilled_data['projects']:
            error = f"Project name '{project_name}' already exists. Please choose a different name."
        else:
            # Process form submission
            data = {
                'project_name': project_name,
                'creator': request.form['creator'],
                'openai_key': request.form.get('openai_key', prefilled_data['openai_key']),  # Use existing key if not provided
                'basename': request.form['basename']
            }
            # Update config
            config['creator'] = data['creator']
            config['openai_key'] = data['openai_key']
            config['projects'].append(data['project_name'])
            # Save to config.json
            os.makedirs('secrets', exist_ok=True)
            with open('secrets/config.json', 'w') as f:
                json.dump(config, f)
            # Don't display the key in the interface
            display_data = {
                'project_name': data['project_name'],
                'creator': data['creator'],
                'basename': data['basename']
            }
            return render_template('index.html', data=display_data, prefilled_data=prefilled_data, error=error)
    
    return render_template('index.html', prefilled_data=prefilled_data, error=error)

if __name__ == '__main__':
    # Set host and port
    host = '127.0.0.1'
    port = 5000
    url = f'http://{host}:{port}'
    webbrowser.open(url)
    
    # Watch additional files like config.json for auto-reload
    extra_files = [os.path.join('secrets', 'config.json')]
    app.run(host=host, port=port, debug=True, extra_files=extra_files)