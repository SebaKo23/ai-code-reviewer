import os
import sys
from github import Github
from src.reviewer import CodeReviewer


def format_markdown_comment(report) -> str:
    """Formats a ReviewReport object into an elegant Markdown comment for GitHub."""
    comment_body = f"## AI Code Reviewer Report\n\n"
    comment_body += f"**Summary:** {report.summary}\n"
    comment_body += f"**Overall Code Score:** `{report.score}/10`\n\n"
    comment_body += f"### Detailed Comments ({len(report.comments)})\n\n"

    for i, com in enumerate(report.comments, 1):
        severity_emoji = "🔴" if com.severity == "CRITICAL" else "🟡" if com.severity == "WARNING" else "🔵"
        comment_body += f"#### {severity_emoji} [{com.severity}] {com.category}: `{com.file_path}` (Line {com.line_number or 'N/A'})\n"
        comment_body += f"**Issue:** {com.comment}\n\n"
        if com.suggested_fix:
            comment_body += f"**Suggested Fix:**\n```python\n{com.suggested_fix}\n```\n"
        comment_body += "---\n"

    comment_body += "\n*Powered by LangChain + ChromaDB + OpenRouter RAG Pipeline*"
    return comment_body


def run_github_review():
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")

    if not all([github_token, repo_name, pr_number]):
        print("Missing required environment variables (GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER).")
        print("Running in local simulation mode...")
        return

    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    print(f"Fetching diff for Pull Request #{pr_number} in {repo_name}...")
    
    files = pr.get_files()
    diff_text = ""
    for file in files:
        if file.patch:
            diff_text += f"diff --git a/{file.filename} b/{file.filename}\n"
            diff_text += file.patch + "\n"

    if not diff_text.strip():
        print("No code changes found in PR.")
        return

    reviewer = CodeReviewer()
    report = reviewer.review_diff(diff_text)

    comment_body = format_markdown_comment(report)
    pr.create_issue_comment(comment_body)
    print(f"Successfully posted AI review comment to PR #{pr_number}!")


if __name__ == "__main__":
    run_github_review()