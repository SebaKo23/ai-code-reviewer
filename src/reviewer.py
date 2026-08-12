import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from src.config import OPENROUTER_API_KEY
from src.retriever import ContextRetriever


# --- 1. PYDANTIC SCHEMA ---

class ReviewComment(BaseModel):
    file_path: str = Field(description="Ścieżka do pliku, którego dotyczy uwaga (np. src/user_processor.py)")
    line_number: Optional[int] = Field(description="Numer linijki kodu, w której znajduje się błąd/uwaga (jeśli dotyczy konkretnej linii)")
    severity: str = Field(description="Poziom istotności: 'INFO', 'WARNING', lub 'CRITICAL'")
    category: str = Field(description="Kategoria: 'STYLE' (niezgodność ze styleguide), 'BUG' (potencjalny błąd), 'SECURITY' (bezpieczeństwo)")
    comment: str = Field(description="Zwięzły opis problemu i wyjaśnienie, dlaczego to wymaga poprawy")
    suggested_fix: Optional[str] = Field(description="Sugerowany fragment poprawionego kodu Python (jeśli dotyczy)")


class ReviewReport(BaseModel):
    summary: str = Field(description="Krótkie (2-3 zdania) podsumowanie jakości przesyłanego kodu")
    score: int = Field(description="Ocena kodu od 1 do 10 na podstawie zgodności ze styleguide i jakości")
    comments: List[ReviewComment] = Field(description="Lista szczegółowych uwag do kodu")


# --- 2. CODE REVIEWER CLASS ---

class CodeReviewer:
    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is missing in .env file!")

        self.llm = ChatOpenAI(
            model="qwen/qwen-2.5-coder-32b-instruct",
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1
        )
        self.retriever = ContextRetriever()
        self.parser = PydanticOutputParser(pydantic_object=ReviewReport)

    def _build_prompt(self) -> ChatPromptTemplate:
        template = """You are a Senior AI Code Reviewer and Software Architect.
Your task is to review code changes (git diff) for compliance with the Styleguide and clean code best practices.

Here are the guidelines from the project STYLEGUIDE:
---
{styleguide_context}
---

Here is the existing code context from the repository:
---
{code_context}
---

Here is the code diff to analyze (Git Diff):
---
{git_diff}
---

Requirements for your response:
1. Evaluate code consistency with the STYLEGUIDE and detect any potential bugs or security issues.
2. Return ALL comments strictly matching the provided JSON schema.

{format_instructions}
"""
        return ChatPromptTemplate.from_template(
            template=template,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def review_diff(self, diff_text: str) -> ReviewReport:
        context = self.retriever.get_relevant_context(diff_text)
        
        style_str = "\n".join([doc.page_content for doc in context["styleguide_context"]])
        code_str = "\n".join([f"File {doc.metadata.get('source')}:\n{doc.page_content}" for doc in context["code_context"]])
        
        prompt = self._build_prompt()
        chain = prompt | self.llm | self.parser
        
        print("Analyzing code diff via OpenRouter (Llama 3.3 70B)...")
        report = chain.invoke({
            "styleguide_context": style_str if style_str else "No specific styleguide rules.",
            "code_context": code_str if code_str else "No additional code context.",
            "git_diff": diff_text
        })
        
        return report


# --- TEST URUCHOMIENIA ---
if __name__ == "__main__":
    from pathlib import Path
    
    sample_diff = Path("sample.diff")
    if not sample_diff.exists():
        print("Missing sample.diff file!")
    else:
        diff_text = sample_diff.read_text(encoding="utf-8")
        reviewer = CodeReviewer()
        report = reviewer.review_diff(diff_text)
        
        print("\n================ REVIEW REPORT ================")
        print(f"SUMMARY: {report.summary}")
        print(f"CODE SCORE: {report.score}/10")
        print(f"COMMENTS COUNT: {len(report.comments)}\n")
        
        for i, comment in enumerate(report.comments, 1):
            print(f"--- Comment #{i} [{comment.severity}] ({comment.category}) ---")
            print(f"File: {comment.file_path} | Line: {comment.line_number}")
            print(f"Comment: {comment.comment}")
            if comment.suggested_fix:
                print(f"Suggested fix:\n{comment.suggested_fix}\n")