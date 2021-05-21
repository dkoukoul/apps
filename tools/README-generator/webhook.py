import subprocess
import os

from github_webhook import Webhook
from flask import Flask
from make_readme import generate_READMEs

app = Flask(__name__)   # Standard Flask app
webhook = Webhook(app)  # Defines '/postreceive' endpoint

webhook.secret = open("github_webhook_secret", "r").read().strip()

my_env = os.environ.copy()
my_env["GIT_TERMINAL_PROMPT"] = "0"

login = open("login").read().strip()
token = open("token").read().strip()

def git(cmd, in_folder=None):

    if not isinstance(cmd, list):
        cmd = cmd.split()
    if in_folder:
        cmd = ["-C", in_folder] + cmd
    cmd = ["git"] + cmd
    return subprocess.check_output(cmd, env=my_env).strip().decode("utf-8")


@app.route("/")
def main_route():
    return "You aren't supposed to go on this page using a browser, it's for webhooks push instead."


@webhook.hook()
def on_push(data):

    repository = data["repository"]["full_name"]
    branch = data["ref"].split("/", 2)[2]

    folder = subprocess.check_output(["mktemp", "-d"])
    git(f"clone https://{login}:{token}@github.com/{repository} --single-branch --branch {branch} {folder}")
    generate_READMEs(folder)

    diff_not_empty = bool(subprocess.check_output(f"cd {folder} && git diff HEAD --compact-summary", shell=True).strip().decode("utf-8"))
    if not diff_not_empty:
        return

    git(["commit", "-a", "-m", "Auto-update README", "--author='Yunohost-Bot <>'"], in_folder=folder)
    git(f"push fork origin {branch} --quiet", in_folder=folder)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80123)
