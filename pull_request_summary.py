import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_pull_requests(repo_name, since_date):
    url = f"https://api.github.com/repos/{repo_name}/pulls"
    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "since": since_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch pull requests: {response.status_code}")
        return None

def generate_email_body(repo_name, pull_requests):
    open_prs = [pr for pr in pull_requests if pr['state'] == 'open']
    closed_prs = [pr for pr in pull_requests if pr['state'] == 'closed']
    merged_prs = [pr for pr in closed_prs if pr['merged_at'] is not None]

    email_body = f"Summary of pull requests for {repo_name} in the last week:\n\n"
    email_body += f"Total opened PRs: {len(open_prs)}\n"
    email_body += f"Total closed PRs: {len(closed_prs)}\n"
    email_body += f"Total merged PRs: {len(merged_prs)}\n\n"

    email_body += "Opened PRs:\n"
    for pr in open_prs:
        email_body += f"- {pr['title']} ({pr['html_url']})\n"

    email_body += "\nClosed and Merged PRs:\n"
    for pr in closed_prs:
        state = "Merged" if pr['merged_at'] else "Closed"
        email_body += f"- {pr['title']} ({pr['html_url']}) [{state}]\n"

    return email_body

def generate_summary_email(repo_name, since_date):
    pull_requests = fetch_pull_requests(repo_name, since_date)
    if pull_requests:
        email_body = generate_email_body(repo_name, pull_requests)
        return email_body
    else:
        return None

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    repo_name = data.get('repo_name')
    to_email = data.get('to_email')
    from_email = os.environ.get('FROM_EMAIL')
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = os.environ.get('SMTP_PORT')
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    if not all([repo_name, to_email, from_email, smtp_server, smtp_port, smtp_username, smtp_password]):
        return jsonify({'message': 'Missing required parameters'}), 400

    since_date = datetime.now() - timedelta(days=7)
    email_body = generate_summary_email(repo_name, since_date)
    if email_body:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Weekly Pull Request Summary Report"
        msg.attach(MIMEText(email_body, 'plain'))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        return jsonify({'message': 'Email sent successfully'}), 200
    else:
        return jsonify({'message': 'Failed to generate email body'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)