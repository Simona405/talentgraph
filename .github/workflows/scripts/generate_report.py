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
                nodes { ... on Repository {
                  name owner { login } stargazerCount description url
                  primaryLanguage { name }
                }}
              }
            }
            """,
            "variables": {"q": search_query}
        },
        headers={"Authorization": f"Bearer {gh_token}"}
    )

    repos = response.json().get("data", {}).get("search", {}).get("nodes", [])
    top_repos = [r for r in repos if r and r["stargazerCount"] > 0][:10]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    md = f"""# GitHub AI 周报 · {today}

> 自动追踪最近 7 天高星 AI 开源项目（大模型、智能体、行业应用）

## 🔥 本周 Top {len(top_repos)} 项目

| 项目 | 作者 | Stars | 简介 | 语言 |
|------|------|-------|------|------|
"""
    for r in top_repos:
        desc = (r["description"] or "")[:80]
        lang = r["primaryLanguage"]["name"] if r["primaryLanguage"] else "—"
        md += f"| [{r['name']}]({r['url']}) | [@{r['owner']['login']}](https://github.com/{r['owner']['login']}) | {r['stargazerCount']} | {desc}{'...' if len(r['description'] or '') > 80 else ''} | `{lang}` |\n"

    md += "\n\n---\n🤖 由 GitHub Actions 自动生成"

    os.makedirs("reports", exist_ok=True)
    with open(f"reports/weekly-{today}.md", "w") as f:
        f.write(md)

    print(f"✅ 报告已生成: reports/weekly-{today}.md")

if __name__ == "__main__":
    main()
