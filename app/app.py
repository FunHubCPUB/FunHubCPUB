from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # change this!

# Config
OUTPUT_DIR = 'generated_pages'
GITHUB_REPO_DIR = '/home/Cannawesome/FunHubCPUB/'  # full path

# Dummy login (for demo purposes only)
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

        html_content = render_template('page_template.html', title=title, body=body)

        filepath = os.path.join(GITHUB_REPO_DIR, f'app/generated_pages/{slug}.html')
        with open(filepath, 'w') as f:
            f.write(html_content)

        # Commit and push to GitHub
        commit_message = f"Add page: {slug}"
        try:
            start_ssh_agent()
            subprocess.run(['ssh-add', '/home/Cannawesome/id_rsa.pub'])
            subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'add', '.'])
            subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'commit', '-m', commit_message])
            subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'push'])

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
