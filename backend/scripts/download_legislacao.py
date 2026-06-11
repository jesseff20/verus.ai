"""
Script para baixar todos os textos de legislacao do planalto.gov.br
e salvar como arquivos .txt locais em backend/data/legislacao/.

Uso: python backend/scripts/download_legislacao.py
(run from the repo root or the backend directory)
"""
import os
import sys
import time
import re
import ast
import unicodedata

import requests
from bs4 import BeautifulSoup

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, 'data', 'legislacao')


def load_legislacoes():
    """Load LEGISLACOES list from seed_legislacao.py without Django."""
    seed_path = os.path.join(
        BACKEND_DIR, 'apps', 'kb', 'management', 'commands', 'seed_legislacao.py'
    )
    with open(seed_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # Extract the LEGISLACOES = [...] assignment using AST
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'LEGISLACOES':
                    # Evaluate the list literal safely
                    return ast.literal_eval(node.value)
    raise RuntimeError("Could not find LEGISLACOES in seed_legislacao.py")


def slugify(name: str) -> str:
    """Convert law name to a filesystem-safe slug."""
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_str.lower()).strip('-')
    slug = re.sub(r'-+', '-', slug)
    return slug


SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
})


def download_and_extract(url: str, timeout: int = 60, retries: int = 3) -> str:
    """Download HTML and extract clean text (same logic as seed_legislacao)."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = SESSION.get(url, timeout=timeout)
            response.raise_for_status()

            if response.encoding and response.encoding.lower() != 'utf-8':
                response.encoding = response.apparent_encoding or 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            lines = [line for line in text.splitlines() if line.strip()]
            return '\n'.join(lines)

        except (requests.RequestException, ConnectionError) as e:
            last_error = e
            if attempt < retries:
                wait = 2 ** attempt
                print(f"    Retry {attempt}/{retries}: {e}. Waiting {wait}s...")
                time.sleep(wait)

    raise last_error


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    legislacoes = load_legislacoes()
    total = len(legislacoes)
    success = 0
    failed = 0
    skipped = 0

    print(f"Downloading {total} laws to {DATA_DIR}\n")

    for i, leg in enumerate(legislacoes, 1):
        slug = slugify(leg['name'])
        filepath = os.path.join(DATA_DIR, f"{slug}.txt")

        # Skip if already downloaded
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            print(f"[{i}/{total}] SKIP (exists): {leg['name']}")
            skipped += 1
            continue

        try:
            print(f"[{i}/{total}] Downloading: {leg['name']}...")
            text = download_and_extract(leg['url'])

            if not text or len(text.strip()) < 100:
                print(f"[{i}/{total}] WARN: Text too short ({len(text)} chars), saving anyway")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"[{i}/{total}] OK: {slug}.txt ({len(text)} chars)")
            success += 1

            # Small delay to be polite to the server
            time.sleep(1)

        except Exception as e:
            failed += 1
            print(f"[{i}/{total}] FAILED: {leg['name']}: {e}")

    print(f"\nDone: {success} downloaded, {skipped} skipped, {failed} failed (total {total})")


if __name__ == '__main__':
    main()
