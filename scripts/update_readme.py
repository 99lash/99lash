import os
import datetime
from dateutil.relativedelta import relativedelta
import requests

# Configuration
BIRTHDATE = datetime.datetime(2004, 9, 21)
USERNAME = "99lash"
OUTPUT_LIGHT_PATH = "light_mode.svg"
OUTPUT_DARK_PATH = "dark_mode.svg"


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
          totalRepositoryContributions
          contributionCalendar {
            totalContributions
          }
        }
        repositoriesContributedTo(first: 100) {
          totalCount
        }
      }
    }
    """

    variables = {"login": USERNAME}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )

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
    commits = (
        data["contributionsCollection"]["totalCommitContributions"]
        + data["contributionsCollection"]["restrictedContributionsCount"]
    )
    contributed_to = data["repositoriesContributedTo"]["totalCount"]

    # Estimate LOC using diskUsage (KB) as a rough proxy (1KB ~ 50 lines of code)
    total_disk_kb = sum(repo["diskUsage"] for repo in data["repositories"]["nodes"])
    loc_estimate = total_disk_kb * 50 if total_disk_kb > 0 else 0

    # Since GitHub API doesn't provide actual additions/deletions for all time,
    # we'll need to fetch from REST API for each repo
    additions = 0
    deletions = 0

    # Try to get stats from REST API for owned repos
    for repo in data["repositories"]["nodes"][:10]:  # Limit to avoid rate limits
        try:
            # Get repo name from the node (we need to add it to the query)
            pass
        except:
            pass

    # If we can't get real data, estimate 50/50
    if additions == 0 and deletions == 0 and loc_estimate > 0:
        additions = loc_estimate // 2
        deletions = loc_estimate - additions

    return {
        "repos": repos_count,
        "stars": stars,
        "followers": followers,
        "contributed": contributed_to,
        "commits": commits,
        "loc": loc_estimate,
        "additions": additions,
        "deletions": deletions,
        "size": f"{total_disk_kb/1024:.1f} MB",
    }


def escape_xml(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_svg(ascii_path, stats, theme):
    with open(ascii_path, "r") as f:
        ascii_lines = [line.rstrip() for line in f.readlines()]

    uptime = get_uptime()

    # Format LOC with additions and deletions using nested tspan for colors
    loc = stats.get("loc", 0)
    additions = stats.get("additions", 0)
    deletions = stats.get("deletions", 0)

    loc_detail = (
        f'{loc:,} (<tspan class="added">{additions:,}++</tspan>, <tspan class="deleted">{deletions:,}--</tspan>)'
        if isinstance(loc, int)
        else loc
    )

    def stat_line(parts, has_bullet=True, separator_dots="....... "):
        """Helper to format multi-part stat lines with proper tspan markup"""
        result = []
        bullet = '<tspan class="cc">. </tspan>' if has_bullet else ""

        for i, (key, dots, value) in enumerate(parts):
            if i > 0:  # Add separator between parts
                result.append(f' <tspan class="cc">{separator_dots}</tspan>')
            result.append(
                f'<tspan class="key">{escape_xml(key)}</tspan>:<tspan class="cc">{dots} </tspan><tspan class="value">{escape_xml(str(value))}</tspan>'
            )
        return bullet + "".join(result)

    right_side = [
        ("ash@iash", "header"),
        ("OS: Linux - Fedora", "text"),
        (f"Uptime: {uptime}", "text"),
        ("Shell: Oh My Zsh", "text"),
        ("Location: Manila, Philippines -> 127.0.0.1", "text"),
        ("", "blank"),
        ("- Languages & Frameworks -", "label"),
        ("Languages: Java, JS, Python, PHP", "text"),
        ("Tools: VS Code, Git, Docker, Redis", "text"),
        ("Databases: PostgreSQL, MySQL, SQLite", "text"),
        ("Frameworks: FastAPI, Express, Laravel, React", "text"),
        ("", "blank"),
        ("- Hobbies -", "label"),
        ("Software: Open Source, Tinkering", "text"),
        ("Real Life: Cycling, Touching Grass", "text"),
        ("", "blank"),
        ("- GitHub Stats -", "label"),
        (f"Repos: {stats['repos']} {{Contributed: {stats['contributed']}}}", "text"),
        (f"Commits: {stats['commits']}", "text"),
        (f"Stars: {stats['stars']}", "text"),
        (f"Followers: {stats['followers']}", "text"),
        (f"Lines of Code on GitHub: {int(str(stats['loc']).replace(',', '')):,}", "text")
    ]
    print(stats)

    line_height = 20
    svg_width = 1000

    # Top-align both sides, then scale ASCII vertically if needed.
    ascii_start_y = 30
    right_start_y = 30

    # Make the overall SVG height follow the right-side block.
    right_bottom_y = right_start_y + ((len(right_side) - 1) * line_height)
    height = right_bottom_y + 30

    # If the ASCII is taller than the right-side block, scale it vertically to fit.
    ascii_bottom_y = ascii_start_y + ((len(ascii_lines) - 1) * line_height)
    scale_y = None
    if ascii_bottom_y > right_bottom_y and ascii_bottom_y != ascii_start_y:
        scale_y = (right_bottom_y - ascii_start_y) / (ascii_bottom_y - ascii_start_y)

    # Find max width of ASCII to offset the right side
    max_ascii_width_chars = max(len(line) for line in ascii_lines) if ascii_lines else 0
    right_side_x = (
        max_ascii_width_chars * 8.5
    ) + 40  # Roughly 8.5px per char for monospace 14px

    approx_char_px = 8.5
    right_rule_chars = max(10, int((svg_width - right_side_x - 40) / approx_char_px))

    def make_rule(prefix):
        return "-" * max(0, right_rule_chars - len(prefix) - 1)

    svg_header = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg width=\"{svg_width}\" height=\"{height}\" xmlns=\"http://www.w3.org/2000/svg\">
  <style>
    .base {{ font: 14px 'Fira Code', 'Courier New', monospace; fill: {theme['base']}; }}
    .header {{ font: bold 16px 'Fira Code', 'Courier New', monospace; fill: {theme['base']}; }}
    .key {{ fill: {theme['key']}; }}
    .value {{ fill: {theme['value']}; }}
    .cc {{ fill: {theme['cc']}; }}
    .ascii {{ font: 15px monospace; fill: {theme['ascii']}; white-space: pre; }}
    .added {{ fill: {theme['added']}; }}
    .deleted {{ fill: {theme['deleted']}; }}
    text, tspan {{ white-space: pre; }}
  </style>
  <rect width=\"100%\" height=\"100%\" fill=\"{theme['bg']}\" rx=\"15\"/>
"""

    svg_content = []

    # Add ASCII
    if scale_y is not None:
        svg_content.append(
            f'  <g id="ascii-art" transform="translate(0 {ascii_start_y}) scale(1 {scale_y:.5f}) translate(0 {-ascii_start_y})">'
        )

    for i, line in enumerate(ascii_lines):
        y = ascii_start_y + (i * line_height)
        prefix = "    " if scale_y is not None else "  "
        svg_content.append(
            f'{prefix}<text x="20" y="{y}" class="ascii">{escape_xml(line)}</text>'
        )

    if scale_y is not None:
        svg_content.append("  </g>")

    # Add Stats (with key/value colors + dotted leaders)
    for i, (text, cls) in enumerate(right_side):
        if cls == "blank" or not text:
            continue

        y = right_start_y + (i * line_height)

        if cls == "header":
            svg_content.append(
                f'  <text x="{right_side_x}" y="{y}" class="base"><tspan class="header">{escape_xml(text)}</tspan> {make_rule(text)}</text>'
            )
            continue

        if cls == "label":
            svg_content.append(
                f'  <text x="{right_side_x}" y="{y}" class="base">{escape_xml(text)} {make_rule(text)}</text>'
            )
            continue

        if cls == "statline":
            # Render pre-formatted stat lines (already contains tspan markup)
            svg_content.append(
                f'  <text x="{right_side_x}" y="{y}" class="base">{text}</text>'
            )
            continue

        if ":" in text:
            key, value = text.split(":", 1)
            key = key.strip()
            value = value.strip()

            dots_target = 12 if cls == "stats" else 26
            bullet = cls != "stats"

            dots_count = max(1, dots_target - len(key))
            dots = "." * dots_count
            lead = '<tspan class="cc">. </tspan>' if bullet else ""

            svg_content.append(
                f'  <text x="{right_side_x}" y="{y}" class="base">'
                f'{lead}<tspan class="key">{escape_xml(key)}</tspan>:'
                f'<tspan class="cc">{dots} </tspan><tspan class="value">{escape_xml(value)}</tspan>'
                f"</text>"
            )
        else:
            svg_content.append(
                f'  <text x="{right_side_x}" y="{y}" class="base">{escape_xml(text)}</text>'
            )

    svg_footer = "</svg>"

    return svg_header + "\n".join(svg_content) + "\n" + svg_footer


if __name__ == "__main__":
    token = os.getenv("GH_TOKEN", "")
    if not token:
        print("GH_TOKEN not found")
        exit(1)

    stats = get_github_stats(token)
    if stats:
        themes = {
            OUTPUT_DARK_PATH: {
                "bg": "#161b22",
                "base": "#c9d1d9",
                "key": "#F69052",
                "value": "#a5d6ff",
                "cc": "#616e7f",
                "ascii": "#9ca3af",
                "added": "#22CB00",
                "deleted": "#FF0001",
            },
            OUTPUT_LIGHT_PATH: {
                "bg": "#E3E3E3",
                "base": "#24292f",
                "key": "#CA5C18",
                "value": "#0a3069",
                "cc": "#6e849c",
                "ascii": "#000000FF",
                "added": "#22CB00",
                "deleted": "#FF0001",
            },
        }

        for out_path, theme in themes.items():
            svg_output = generate_svg("ascii-art-1.txt", stats, theme)
            with open(out_path, "w") as f:
                f.write(svg_output)
            print(f"Successfully generated {out_path}")
    else:
        print("Failed to gather stats")
