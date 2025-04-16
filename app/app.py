from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # change this!
import os

def get_html_file_names(directory):
    """
    Get the names of all .html files in the specified directory.

    Args:
        directory (str): The path to the directory to search.

    Returns:
        list: A list of .html file names (without the directory path).
    """
    if not os.path.exists(directory):
        return []

    return [file for file in os.listdir(directory) if file.endswith('.html')]

# Example usage

# Get the current directory
current_dir = os.getcwd()

# Get the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

# Define the output director, '
OUTPUT_DIR = os.path.join(current_dir, 'generated_pages')

# Define the GitHub repository directory
GITHUB_REPO_DIR = os.path.abspath(os.path.join(current_dir, os.pardir))


# Dummy login (for demo purposes only)pi
USERNAME = 'admin'
PASSWORD = 'PythonAnywhere$$'

def start_ssh_agent():
    # Start the ssh-agent process and capture its output
    result = subprocess.run(["ssh-agent", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Parse and export the SSH_AUTH_SOCK and SSH_AGENT_PID variables
    output = result.stdout
    for line in output.splitlines():
        if "SSH_AUTH_SOCK" in line or "SSH_AGENT_PID" in line:
            key, value = line.split(";", 1)[0].split("=", 1)
            os.environ[key] = value

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('editor'))
        else:
            flash('Wrong username or password!')
    return render_template('login.html')


@app.route('/editor', methods=['GET', 'POST'])
def editor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        body = request.form['body']

        html_content = render_template('page_template.html', title=title, body=body.replace("\n", "<br>"))

        filepath = os.path.join(OUTPUT_DIR, f'{slug}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Get the directory of the current script
        current_script_dir = os.path.dirname(os.path.abspath(__file__))

        # Specify the folder name

        # Construct the full path to the folder

        index_list=get_html_file_names(OUTPUT_DIR)
        html_content_2 = render_template('index.html', pages=index_list)

        filepath_2 = os.path.join(current_script_dir, 'index.html')
        with open(filepath_2, 'w', encoding='utf-8') as f:
            f.write(html_content_2)
        # Commit and push to GitHub
        commit_message = f"Add page: {slug}"
        try:
            start_ssh_agent()
            subprocess.run(['ssh-add', '/home/Cannawesome/id_rsa.pub'])
            subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'add', '.'])
            subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'commit', '-m', commit_message])
            #subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'push'])

        except Exception as e:
            flash(f"Git push failed: {e}")
            return redirect(url_for('editor'))

        return render_template('success.html', slug=slug)

    return render_template('editor.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
