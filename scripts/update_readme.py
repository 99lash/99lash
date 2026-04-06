import os
import datetime
from dateutil.relativedelta import relativedelta
import requests

# Configuration
BIRTHDATE = datetime.datetime(2004, 9, 21)
USERNAME = "99lash" # Your GitHub username

def get_uptime():
    now = datetime.datetime.now()
    diff = relativedelta(now, BIRTHDATE)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"

def get_github_stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # GraphQL Query for total stats
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10) {
              edges { size node { name } }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
        repositoriesContributedTo(first: 100) {
          totalCount
        }
      }
    }
    """
    
    variables = {"login": USERNAME}
    response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    if response.status_code != 200:
        return {"repos": "Error", "stars": "Error", "followers": "Error", "contributed": "Error", "commits": "Error", "loc": "Error"}
    
    data = response.json()["data"]["user"]
    
    repos_count = data["repositories"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in data["repositories"]["nodes"])
    followers = data["followers"]["totalCount"]
    commits = data["contributionsCollection"]["totalCommitContributions"] + data["contributionsCollection"]["restrictedContributionsCount"]
    contributed_to = data["repositoriesContributedTo"]["totalCount"]
    
    # LOC is expensive to calculate via API, using a placeholder for now
    # but we can improve this later with a specific LOC action if needed.
    return {
        "repos": repos_count,
        "stars": stars,
        "followers": followers,
        "contributed": contributed_to,
        "commits": commits,
        "loc": "Heavy Load...",
    }

def merge_fetch(ascii_path, stats):
    with open(ascii_path, "r") as f:
        ascii_lines = f.readlines()

    uptime = get_uptime()

    # Define the right-side content according to finalized plan
    right_side = [
        f"ash @iash ------------------------",
        f"OS: Linux - Fedora",
        f"Uptime: {uptime}",
        f"Shell: Oh My Zsh",
        f"Location: Manila, Philippines (127.0.0.1)",
        "",
        f"- Languages & Frameworks -",
        f"Languages: Java, JavaScript, Python, PHP",
        f"Tools: VS Code, Git, Docker, Postman, Redis",
        f"Databases: PostgreSQL, MySQL, SQLite",
        f"Frameworks: FastAPI, Express.js, Laravel, React, Tailwind CSS",
        "",
        f"- Hobbies -",
        f"Software: Open Source, Tinkering",
        f"Real Life: Cycling, Grass Touching, Programming",
        "",
        f"- GitHub Stats -",
        f"Repos: {stats['repos']} {{Contributed: {stats['contributed']}}} | Stars: {stats['stars']}",
        f"Commits: {stats['commits']} | Streaks: Active",
        f"LOC: {stats['loc']}",
    ]

    # Combine ASCII (left) and Stats (right)
    combined = []
    max_ascii_width = max(len(line.rstrip()) for line in ascii_lines)
    
    for i in range(max(len(ascii_lines), len(right_side))):
        left = ascii_lines[i].rstrip().ljust(max_ascii_width + 5) if i < len(ascii_lines) else " " * (max_ascii_width + 5)
        right = right_side[i] if i < len(right_side) else ""
        combined.append(left + right)

    return "\n".join(combined)

if __name__ == "__main__":
    token = os.getenv("GH_TOKEN", "")
    stats = get_github_stats(token)
    final_fetch = merge_fetch("ascii-art.txt", stats)
    
    # Read README template and replace placeholder
    with open("README.md.template", "r") as f:
        template = f.read()
    
    new_readme = template.replace("{{ FETCH_SECTION }}", f"```text\n{final_fetch}\n```")
    
    with open("README.md", "w") as f:
        f.write(new_readme)
