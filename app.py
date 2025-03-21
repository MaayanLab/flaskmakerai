from flask import Flask, render_template, request, redirect, jsonify, send_from_directory
import webbrowser
import json
import os
import openai

app = Flask(__name__)

# In-memory storage for chat messages and project progress
chat_history = []
project_progress = {}

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

# Function to save config
def save_config(config):
    os.makedirs('secrets', exist_ok=True)
    with open('secrets/config.json', 'w') as f:
        json.dump(config, f)

def get_text_completion(prompt, api_key, model):
    client = openai.OpenAI(api_key=api_key)
    
    role_prompt = '''
    You are a specialized Flask application generator. Your task is to analyze user requests and generate appropriate code.

    When responding to a request about creating a Flask app:
    1. Generate a JSON object with the following structure:
    {
        "app.py": "<Flask application code with proper error handling and best practices>",
        "docker": "<Production-ready Dockerfile with multi-stage builds and security considerations>"
    }

    The generated code should:
    - Follow Flask best practices and patterns
    - Include proper error handling and logging
    - Use secure defaults and configurations
    - Include helpful comments explaining key components
    - Follow PEP 8 style guidelines for Python code
    - Include necessary requirements.txt entries
    - Implement proper security headers and CORS settings when applicable

    For the Dockerfile:
    - Use multi-stage builds for smaller image size
    - Follow Docker best practices
    - Include proper security considerations
    - Set appropriate environment variables
    - Use non-root user for security
    - Include health checks

    For any other prompt:
    - Provide a clear, detailed response
    - Include code examples when relevant
    - Explain any technical concepts
    - Suggest best practices and improvements
    '''

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content

def save_project_files(project_name, response):
    try:
        data = json.loads(response)
        if 'app.py' in data and 'docker' in data:
            project_dir = os.path.join('projects', project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            with open(os.path.join(project_dir, 'app.py'), 'w') as f:
                f.write(data['app.py'])
            with open(os.path.join(project_dir, 'Dockerfile'), 'w') as f:
                f.write(data['docker'])
            
            # Update progress
            if project_name not in project_progress:
                project_progress[project_name] = {'Backend': False, 'Frontend': False, 'Dockerization': False, 'Deployment': False}
            project_progress[project_name]['Backend'] = True
            project_progress[project_name]['Dockerization'] = True
            
            return True
        return False
    except json.JSONDecodeError:
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()
    prefilled_data = {
        'creator': config.get('creator', ''),
        'openai_key': config.get('openai_key', ''),
        'projects': config.get('projects', [])
    }

    error = None
    if request.method == 'POST':
        project_name = request.form.get('project_name', '')
        creator = request.form.get('creator', '')
        basename = request.form.get('basename', '')
        
        if not all([project_name, creator, basename]):
            error = "All fields are required for submission."
        elif project_name in prefilled_data['projects']:
            error = f"Project name '{project_name}' already exists. Please choose a different name."
        else:
            data = {
                'project_name': project_name,
                'creator': creator,
                'openai_key': request.form.get('openai_key', prefilled_data['openai_key']),
                'basename': basename
            }
            config['creator'] = data['creator']
            config['openai_key'] = data['openai_key']
            config['projects'].append(data['project_name'])
            save_config(config)
            return redirect(f"/chat?project_name={data['project_name']}")
    
    return render_template('index.html', prefilled_data=prefilled_data, error=error)

@app.route('/delete_key', methods=['POST'])
def delete_key():
    config = load_config()
    config['openai_key'] = ''
    save_config(config)
    return redirect('/')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    project_name = request.args.get('project_name', 'Unknown Project')
    config = load_config()
    api_key = config.get('openai_key', '')

    if request.method == 'POST':
        user_input = request.form.get('message', '').strip()
        model = request.form.get('model', 'gpt-4o-mini')
        if user_input:
            if not api_key:
                return jsonify({'error': 'No OpenAI API key found in config.'})
            try:
                bot_response = get_text_completion(user_input, api_key, model)
                files_saved = save_project_files(project_name, bot_response)
                
                chat_history.append({'sender': 'You', 'text': user_input})
                if files_saved:
                    bot_response = "I've created the files! You can inspect `app.py` and `