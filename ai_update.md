Skip to content
Chat history

You said:
I've heard about the new kind of programming which is basically instructions for AI in english. How does it work
ChatGPT said:
You’re talking about natural language programming (sometimes called prompt programming or AI-assisted coding), where you write instructions in plain English (or another natural language) and an AI system interprets them into code or directly executes them.

At a high level, it works like this:

1. You give high-level instructions in natural language
Instead of writing Python or C++ directly, you describe what you want in plain language.
Example:

“Create a function that takes a list of numbers and returns only the prime ones.”

2. The AI model parses and interprets your intent
Large Language Models (LLMs) like GPT-5, Claude, or Code Llama are trained on massive datasets of code and natural language.

They learn statistical relationships between words, code tokens, and problem structures.

When you give instructions, the model uses its learned patterns to:

Understand intent (what you mean).

Decide how to implement it in the target language.

Output structured code or even run the instructions directly.

3. Code generation or direct execution
There are two main modes:

Code generation: The AI writes actual source code (Python, JavaScript, etc.) for you to run or integrate into a project.

Direct execution: Some systems skip generating code for you and instead execute instructions internally.
For example, telling an AI database agent:

“Show me the average sales in Europe for last quarter”
might make it generate and run a SQL query behind the scenes, without you seeing the code.

4. Iterative refinement loop
Because natural language is inherently ambiguous, you refine by conversation:

You run the AI-generated code (or let it execute internally).

If the result isn’t right, you clarify or adjust your instructions.

This loop is much faster than manually rewriting from scratch.

5. Underlying mechanisms
Training: Models are trained on paired datasets of code + comments, documentation, and Q&A discussions.

Parsing: Your request is tokenized and embedded in a vector space where semantic meaning is captured.

Inference: The model predicts the most likely sequence of code tokens or actions that match your instructions.

Tool use: Advanced setups let the AI call compilers, run code, access APIs, or manipulate files as part of the “execution.”

If you want, I can show you a minimal practical example where English-only instructions become a working program without manually writing a single line of code.
It’ll demonstrate exactly how this “English programming” works in practice.

You said:
I got this repo https://github.com/rubenayla/invest

I'm interested in this for investing, so an AI can do  the analysis for me, filter stuff and check relevant parameters. You think it's a good fit?
ChatGPT said:

Thought for 57s
Short answer: yes—your invest repo is a solid base to bolt on an AI “analyst” that screens, pulls data, runs DCF/RIM, and writes a brief memo. You already have valuation cores (e.g., RIM/DCFs) and a watchlist mindset; you mainly need (1) a clean data layer, (2) factor calculations, and (3) a narrow natural-language interface that maps English → actions → your code.

Minimal architecture (fits your style)
invest/
    src/
        data_providers/
            yahoo.py        # quick free prices, key ratios
            edgar.py        # 10-K/10-Q fetching & parsing (MD&A, risk)
        factors/
            quality.py      # ROIC, margin stability, FCF conversion
            value.py        # EV/EBIT, P/FCF, yield metrics
            growth.py       # 3/5/10y CAGR, reinvestment rate
        models/
            dcf.py          # your DCF
            rim.py          # your Residual Income Model
        policy/
            universe.py     # S&P500, JP large-cap, custom watchlist
            risk.py         # leverage/credit floors, drawdown guardrails
        nlp/
            schema.py       # Pydantic JSON schema for intents
            parse.py        # strict parser (regex + Pydantic); optional LLM
            planner.py      # maps intent → tool calls (screen → fetch → score → value)
        report/
            memo.py         # 1-page memo generator (numbers first, sources)
    scripts/
        ai_cli.py           # English in, results out (terminal)
    tests/
        test_parse.py, test_factors.py, test_models.py
Workflow (deterministic, then optional LLM)
Parse the English request into a strict JSON intent (no free-form execution).

Plan: choose tools (screen → fetch → compute factors → run DCF/RIM).

Execute with your code; log provenance (tickers, endpoints, timestamps).

Report: table + short memo; never hide assumptions.

Example intent schema (safe & debuggable)
# src/nlp/schema.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Screen(BaseModel):
    region: Literal['US','EU','JP','ALL']='US'
    min_mktcap: Optional[float]=None        # USD millions
    filters: List[str] = Field(default_factory=list)  # e.g. ["ROIC>15", "EV/EBIT<12", "5Y_CAGR>10"]

class Analyze(BaseModel):
    tickers: List[str]
    models: List[Literal['dcf','rim']] = ['rim']
    scenarios: List[Literal['bear','base','bull']] = ['base']

class Intent(BaseModel):
    action: Literal['screen','analyze','explain']
    screen: Optional[Screen]=None
    analyze: Optional[Analyze]=None
Rule-first parser (works without an LLM)
# src/nlp/parse.py
import re
from .schema import Intent, Screen, Analyze

def parse(text: str) -> Intent:
    t = text.lower()
    if t.startswith('screen'):
        filters = re.findall(r'(roic>\d+|ev/ebit<\d+|p/fcf<\d+|5y_cagr>\d+)', t.replace(' ', ''))
        region = 'US' if 'us' in t else ('EU' if 'eu' in t else 'ALL')
        mcap = re.search(r'mktcap>(\d+)', t.replace(' ', ''))
        return Intent(action='screen', screen=Screen(
            region=region,
            min_mktcap=float(mcap.group(1)) if mcap else None,
            filters=filters
        ))
    if t.startswith('analyze'):
        tickers = re.findall(r'[A-Z]{1,5}', text)
        return Intent(action='analyze', analyze=Analyze(tickers=tickers))
    return Intent(action='explain')
CLI entry (English → results)
# scripts/ai_cli.py
import sys
from src.nlp.parse import parse
from src.policy.universe import get_universe
from src.factors.quality import compute_quality
from src.factors.value import compute_value
from src.models.rim import price_rim
from src.models.dcf import price_dcf
from src.report.memo import write_memo

def main():
    text = ' '.join(sys.argv[1:])
    intent = parse(text)

    if intent.action == 'screen':
        df = get_universe(intent.screen.region)
        df = compute_quality(df, intent.screen.filters)
        df = compute_value(df, intent.screen.filters)
        print(df.sort_values('score', ascending=False).head(20).to_string(index=False))
        return

    if intent.action == 'analyze':
        results = []
        for t in intent.analyze.tickers:
            rim = price_rim(t)
            dcf = price_dcf(t)
            results.append({'ticker': t, 'rim': rim, 'dcf': dcf})
            write_memo(t, rim=rim, dcf=dcf)
        for r in results:
            print(r)

if __name__ == '__main__':
    main()
Env & tooling (your preferences)
uv venv .venv
source .venv/bin/activate
uv pip install -e .[dev]
ruff check .
pytest -q
Why this works
First principles: English is only used to select computations. The math and data live in your repo, so results are reproducible and auditable.

Safety: Strict schemas prevent “agent drift.” Even if you later add an LLM, it must output Intent JSON or it’s rejected.

Speed: Start rule-based. Add an LLM only to expand phrasing coverage (same JSON contract).

What I need from you (no assumptions)
Data sources: OK to start with yfinance only, or do you want EDGAR parsing and paid APIs (FMP, TIKR) now?

Universe: US only, or also EU/JP? Any exclusions (China, microcaps, low-liquidity)?

Valuation defaults: WACC method, terminal growth limits, tax rate handling, stock-based comp treatment.

Risk policy: Max Net Debt/EBITDA, interest coverage floor, cyclicals handling.

Output: CLI only, or also a Markdown/PDF memo per ticker (your choice of template)?

If you confirm those, I’ll give you the exact files to drop into src/ and a couple of pytest tests to lock behavior.




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
