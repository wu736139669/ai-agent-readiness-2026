# AI Agent Readiness 2026 — Dataset & Scanner

> Companion dataset for the study **“AI Agent Readiness Report 2026: 184 Popular Tool Sites, Tested”**.
> Full write-up: https://toolpantry.app/ai-agent-readiness-report

## Headline results (October 2026, n = 184 reachable sites)

- Only **1.6%** (3 of 184) serve Markdown to AI agents (`Accept: text/markdown`) — and **none** of the llms.txt adopters do
- **31.5%** publish an llms.txt
- **23.9%** expose JSON-LD structured data
- **72.3%** allow major AI crawlers in robots.txt; **4 sites explicitly block them**
- Average readiness score: **2.3 / 9**. Best score: 6/9. No site reached 9/9.
- Check any URL yourself: https://toolpantry.app/agent-ready-checker

## Files

| File | What |
| --- | --- |
| `data/results.csv` | Per-domain results: score + the 7 signals + notes |
| `data/targets.txt` | The 212-domain sample (184 reachable) |
| `scan.py` | The scanner. `python3 scan.py` → rewrites `data/results.csv` |

## Methodology (short)

A curated sample of 212 popular browser-based tool websites (image, PDF, conversion,
developer tools, calculators, SEO/design utilities) was fetched once with a standard
browser user agent over HTTPS. Signals measured: robots.txt AI-crawler rules (GPTBot,
ClaudeBot, PerplexityBot, GrokBot, Bingbot, …), llms.txt / llms-full.txt presence,
Markdown content negotiation (`Accept: text/markdown`), JSON-LD, sitemap.xml, and
`rel="alternate" type="text/markdown"` link relations. Scoring: robots 1, llms.txt 2,
llms-full 1, Markdown 2, JSON-LD 1, sitemap 1, alternate 1 (max 9).
28 domains were unreachable (bot protection, timeouts) and excluded.
See the report for the full methodology and limitations.

## Fix your own site

The reference implementation (9/9) is open source (MIT):
https://github.com/wu736139669/markdown-for-agents-worker

## License

Data: CC0. Code: MIT.
