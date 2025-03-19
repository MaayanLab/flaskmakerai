from flask import Flask, render_template, request
import webbrowser

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = {
            'project_name': request.form['project_name'],
            'creator': request.form['creator'],
            'openai_key': request.form['openai_key'],
            'basename': request.form['basename']
        }
        return render_template('index.html', data=data)
    return render_template('index.html')

if __name__ == '__main__':
    # Set host and port
    host = '127.0.0.1'
    port = 5000
    
    # Open browser
    url = f'http://{host}:{port}'
    webbrowser.open(url)
    
    # Run the Flask app
    app.run(host=host, port=port, debug=True)