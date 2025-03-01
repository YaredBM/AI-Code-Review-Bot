import os
import openai
import requests
from github import Github, GithubIntegration
from flask import Flask, request, jsonify

app = Flask(__name__)

# GitHub App Credentials
github_app_id = os.getenv("GITHUB_APP_ID")
github_private_key = os.getenv("GITHUB_PRIVATE_KEY")
github_token = os.getenv("GITHUB_TOKEN")

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_review(code_snippet):
    """Sends code snippet to OpenAI API for review and feedback."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI code reviewer. Provide feedback and suggest improvements."},
            {"role": "user", "content": f"Review this code:
```python
{code_snippet}
```"}
        ]
    )
    return response["choices"][0]["message"]["content"]

@app.route("/webhook", methods=["POST"])
def github_webhook():
    """Handles GitHub webhook events."""
    event = request.json
    if "pull_request" in event:
        pr = event["pull_request"]
        repo_name = event["repository"]["full_name"]
        pr_number = pr["number"]
        process_pull_request(repo_name, pr_number)
    return jsonify({"status": "ok"})

def process_pull_request(repo_name, pr_number):
    """Fetch PR changes, analyze with AI, and post a comment."""
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    comments = []
    for file in pr.get_files():
        if file.filename.endswith(".py"):  # Only analyze Python files for now
            code_diff = requests.get(file.raw_url).text
            feedback = get_ai_review(code_diff)
            comments.append(f"**File:** {file.filename}\n{feedback}")
    
    if comments:
        pr.create_issue_comment("\n\n".join(comments))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
