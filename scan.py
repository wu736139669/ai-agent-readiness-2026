#!/usr/bin/env python3
"""Batch AI-agent-readiness scan — companion to the 2026 report.

Checks each domain in data/targets.txt for the same 7 signals as
/api/check, and writes data/results.csv.

Run: python3 scan.py
"""
import csv
import pathlib
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import urllib3

urllib3.disable_warnings()

ROOT = pathlib.Path(__file__).resolve().parent
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36 ToolPantryStudy/1.0 (+https://toolpantry.app)')
TIMEOUT = 15
AI_BOTS = ['gptbot', 'oai-searchbot', 'chatgpt-user', 'claudebot', 'anthropic-ai', 'perplexitybot', 'grokbot', 'xai-searchbot', 'bingbot']


def get(url, headers=None, tries=3):
    h = {'user-agent': UA, 'accept-language': 'en-US,en;q=0.8'}
    if headers:
        h.update(headers)
    last = None
    for i in range(tries):
        try:
            return requests.get(url, headers=h, timeout=TIMEOUT, allow_redirects=True, verify=False)
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last


def parse_robots(text):
    agents = []
    wildcard = False
    blocked = set()
    for line in text.split('\n'):
        clean = re.sub(r'#.*', '', line).strip()
        if not clean:
            continue
        m = re.match(r'user-agent:\s*(.+)', clean, re.I)
        if m:
            agents = [a.lower() for a in re.split(r'[,\s]+', m.group(1)) if a]
            continue
        m = re.match(r'disallow:\s*(.*)', clean, re.I)
        if m and agents:
            if m.group(1).strip() == '/':
                for a in agents:
                    if a == '*':
                        wildcard = True
                    else:
                        blocked.add(a)
    if wildcard:
        return False, 'disallows all'
    hits = [b for b in AI_BOTS if b in blocked]
    if hits:
        return False, 'blocks ' + ','.join(hits)
    return True, 'allows AI bots'


def check(domain):
    row = {'domain': domain, 'fetched': '', 'robots': 0, 'llms': 0, 'llmsfull': 0,
           'markdown': 0, 'jsonld': 0, 'sitemap': 0, 'alternate': 0, 'score': 0, 'notes': ''}
    base = None
    for scheme in ('https', 'http'):
        try:
            r = get(f'{scheme}://{domain}/')
            if r.status_code < 500:
                base = f'{scheme}://{domain}'
                row['fetched'] = scheme
                break
        except Exception:
            continue
    if not base:
        row['notes'] = 'unreachable'
        return row

    html = r.text if r.ok else ''
    if html:
        row['jsonld'] = 1 if 'application/ld+json' in html else 0
        if re.search(r'rel=["\']alternate["\'][^>]*text/markdown|text/markdown[^>]*rel=["\']alternate["\']', html, re.I):
            row['alternate'] = 1

    try:
        rr = get(base + '/robots.txt')
        if rr.ok and rr.text.strip():
            ok, note = parse_robots(rr.text[:200000])
            row['robots'] = 1 if ok else 0
            if not ok:
                row['notes'] = (row['notes'] + '; ' + note).strip('; ')
    except Exception:
        pass

    for key, path in (('llms', '/llms.txt'), ('llmsfull', '/llms-full.txt')):
        try:
            lr = get(base + path)
            if lr.ok and lr.text.strip():
                row[key] = 1
        except Exception:
            pass

    try:
        mr = get(base + '/', headers={'accept': 'text/markdown, text/html;q=0.9'})
        ct = (mr.headers.get('content-type') or '').lower()
        if mr.ok and 'text/markdown' in ct:
            row['markdown'] = 1
    except Exception:
        pass

    try:
        sr = get(base + '/sitemap.xml')
        if sr.ok and ('<urlset' in sr.text[:10000] or '<sitemapindex' in sr.text[:10000]):
            row['sitemap'] = 1
    except Exception:
        pass

    weights = {'robots': 1, 'llms': 2, 'llmsfull': 1, 'markdown': 2, 'jsonld': 1, 'sitemap': 1, 'alternate': 1}
    row['score'] = sum(row[k] * w for k, w in weights.items())
    return row


def main():
    targets = [d.strip() for d in (ROOT / 'data' / 'targets.txt').read_text().splitlines() if d.strip()]
    print(f'scanning {len(targets)} domains ...')
    rows = []
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for row in ex.map(check, targets):
            rows.append(row)
            done += 1
            if done % 20 == 0:
                print(f'  {done}/{len(targets)}', flush=True)

    rows.sort(key=lambda r: (-r['score'], r['domain']))
    out = ROOT / 'research' / 'results.csv'
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    reached = [r for r in rows if r['fetched']]
    print(f'done: {len(rows)} domains, {len(reached)} reachable, {len(rows) - len(reached)} unreachable')
    print('with llms.txt:', sum(r['llms'] for r in reached))
    print('with markdown negotiation:', sum(r['markdown'] for r in reached))
    print('csv:', out)


if __name__ == '__main__':
    main()
