import os
import datetime
from dateutil.relativedelta import relativedelta
import requests

# Configuration
BIRTHDATE = datetime.datetime(2004, 9, 21)
USERNAME = "99lash" 
OUTPUT_PATH = "stats.svg"

def get_uptime():
    now = datetime.datetime.now()
    diff = relativedelta(now, BIRTHDATE)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"

def get_github_stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
            diskUsage
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
        print(f"Error: {response.status_code}")
        return None
    
    res_json = response.json()
    if "data" not in res_json or res_json["data"]["user"] is None:
        print(f"Query failed: {res_json}")
        return None

    data = res_json["data"]["user"]
    
    repos_count = data["repositories"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in data["repositories"]["nodes"])
    followers = data["followers"]["totalCount"]
    commits = data["contributionsCollection"]["totalCommitContributions"] + data["contributionsCollection"]["restrictedContributionsCount"]
    contributed_to = data["repositoriesContributedTo"]["totalCount"]
    
    # Estimate LOC using diskUsage (KB) as a rough proxy (1KB ~ 50 lines of code)
    # or just show total disk usage if preferred.
    total_disk_kb = sum(repo["diskUsage"] for repo in data["repositories"]["nodes"])
    loc_estimate = f"{total_disk_kb * 50:,}" if total_disk_kb > 0 else "N/A"

    return {
        "repos": repos_count,
        "stars": stars,
        "followers": followers,
        "contributed": contributed_to,
        "commits": commits,
        "loc": loc_estimate,
        "size": f"{total_disk_kb/1024:.1f} MB"
    }

def escape_xml(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")

def generate_svg(ascii_path, stats):
    with open(ascii_path, "r") as f:
        ascii_lines = [line.rstrip() for line in f.readlines()]

    uptime = get_uptime()

    # Define the right-side content with color markers
    # Format: (text, color_class)
    right_side = [
        (f"ash @iash", "header"),
        ("-" * 30, "dim"),
        (f"OS: Linux - Fedora", "text"),
        (f"Uptime: {uptime}", "text"),
        (f"Shell: Oh My Zsh", "text"),
        (f"Location: Manila, Philippines", "text"),
        ("", "text"),
        ("- Languages & Frameworks -", "label"),
        (f"Languages: Java, JS, Python, PHP", "text"),
        (f"Tools: VS Code, Git, Docker, Redis", "text"),
        (f"Databases: PostgreSQL, MySQL, SQLite", "text"),
        (f"Frameworks: FastAPI, Express, Laravel, React", "text"),
        ("", "text"),
        ("- Hobbies -", "label"),
        (f"Software: Open Source, Tinkering", "text"),
        (f"Real Life: Cycling, Programming", "text"),
        ("", "text"),
        ("- GitHub Stats -", "label"),
        (f"Repos: {stats['repos']} (Contributed: {stats['contributed']})", "text"),
        (f"Stars: {stats['stars']} | Followers: {stats['followers']}", "text"),
        (f"Commits: {stats['commits']} | Streaks: Active", "text"),
        (f"Total Size: {stats['size']} | LOC Est: {stats['loc']}", "text"),
    ]

    # Calculate dimensions
    line_height = 20
    max_lines = max(len(ascii_lines), len(right_side))
    height = (max_lines * line_height) + 40
    
    # Find max width of ASCII to offset the right side
    max_ascii_width_chars = max(len(line) for line in ascii_lines)
    ascii_offset = 15 # Padding
    right_side_x = (max_ascii_width_chars * 8.5) + 40 # Roughly 8.5px per char for monospace 14px

    svg_header = f"""<svg width="850" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .text {{ font: 14px 'Fira Code', 'Courier New', monospace; fill: #d1d5db; }}
    .header {{ font: bold 16px 'Fira Code', 'Courier New', monospace; fill: #60a5fa; }}
    .label {{ font: bold 14px 'Fira Code', 'Courier New', monospace; fill: #34d399; }}
    .dim {{ font: 14px 'Fira Code', 'Courier New', monospace; fill: #4b5563; }}
    .ascii {{ font: 12px monospace; fill: #9ca3af; white-space: pre; }}
  </style>
  <rect width="100%" height="100%" fill="transparent"/>
"""

    svg_content = []
    
    # Center the two sides vertically if one is shorter
    ascii_start_y = 30
    right_start_y = 30
    
    if len(ascii_lines) < len(right_side):
        ascii_start_y += (len(right_side) - len(ascii_lines)) * line_height // 2
    elif len(right_side) < len(ascii_lines):
        right_start_y += (len(ascii_lines) - len(right_side)) * line_height // 2

    # Add ASCII
    for i, line in enumerate(ascii_lines):
        y = ascii_start_y + (i * line_height)
        svg_content.append(f'  <text x="20" y="{y}" class="ascii">{escape_xml(line)}</text>')

    # Add Stats
    for i, (text, cls) in enumerate(right_side):
        if not text: continue
        y = right_start_y + (i * line_height)
        svg_content.append(f'  <text x="{right_side_x}" y="{y}" class="{cls}">{escape_xml(text)}</text>')

    svg_footer = "</svg>"
    
    return svg_header + "\n".join(svg_content) + "\n" + svg_footer

if __name__ == "__main__":
    token = os.getenv("GH_TOKEN", "")
    if not token:
        print("GH_TOKEN not found")
        exit(1)
        
    stats = get_github_stats(token)
    if stats:
        svg_output = generate_svg("ascii-art.txt", stats)
        with open(OUTPUT_PATH, "w") as f:
            f.write(svg_output)
        print(f"Successfully generated {OUTPUT_PATH}")
    else:
        print("Failed to gather stats")
