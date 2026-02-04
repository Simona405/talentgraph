# scripts/generate_report.py
import os
import requests
from datetime import datetime, timedelta

def main():
    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        raise SystemExit("❌ GH_TOKEN not set")

    since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    topics = ["ai", "llm", "gpt", "llama", "rag", "agent", "transformers", "vllm", "langchain", "ollama"]
    query_str = " OR ".join([f"topic:{t}" for t in topics])
    search_query = f"created:>{since} sort:stars-desc ({query_str})"

    response = requests.post(
        "https://api.github.com/graphql",
        json={
            "query": """
            query($q: String!) {
              search(query: $q, type: REPOSITORY, first: 15) {
                nodes {
                  ... on Repository {
                    name
                    owner { login }
                    stargazerCount
                    description
                    url
                    primaryLanguage { name }
                  }
                }
              }
            }
            """,
            "variables": {"q": search_query}
        },
        headers={"Authorization": f"Bearer {gh_token}"}
    )

    # 检查 HTTP 错误
    if response.status_code != 200:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")
        raise SystemExit("GitHub API request failed")

    data = response.json()

    # 检查 GraphQL 错误
    if "errors" in data:
        print("❌ GraphQL Errors:", data["errors"])
        raise SystemExit("GraphQL query failed")

    repos = data.get("data", {}).get("search", {}).get("nodes", [])
    top_repos = [r for r in repos if r and r.get("stargazerCount", 0) > 0][:10]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    md = f"""# GitHub AI 周报 · {today}

> 自动追踪最近 7 天高星 AI 开源项目（大模型、智能体、行业应用）

## 🔥 本周 Top {len(top_repos)} 项目

| 项目 | 作者 | Stars | 简介 | 语言 |
|------|------|-------|------|------|
"""
    for r in top_repos:
        desc = (r.get("description") or "")[:80]
        lang = r.get("primaryLanguage", {}).get("name", "—") if r.get("primaryLanguage") else "—"
        url = r["url"]
        owner = r["owner"]["login"]
        name = r["name"]
        stars = r["stargazerCount"]
        md += f"| [{name}]({url}) | [@{owner}](https://github.com/{owner}) | {stars} | {desc}{'...' if len(r.get('description') or '') > 80 else ''} | `{lang}` |\n"

    md += "\n\n---\n🤖 由 GitHub Actions 自动生成"

    os.makedirs("reports", exist_ok=True)
    filepath = f"reports/weekly-{today}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ 报告已生成: {filepath}")

if __name__ == "__main__":
    main()
