import argparse
import json
import re
import shutil
from pathlib import Path


def extract_assistant_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    # Find all assistant segments: text after 'assistant' until next role or end
    pattern = re.compile(r"assistant\s*(.*?)(?=(?:\b(system|user|assistant)\b)|$)", re.IGNORECASE | re.DOTALL)
    matches = [m.group(1).strip() for m in pattern.finditer(s)]
    if matches:
        # join multiple assistant segments with a single space
        cleaned = " ".join(m for m in matches if m)
        return cleaned.strip()
    # fallback: if the whole string starts with assistant-like prefix
    if s.lower().startswith('assistant'):
        return s[len('assistant'):].strip()
    # no assistant token found  as fallback, return original but stripped
    return s.strip()


def clean_file(path: Path, backup: bool = True, preview: bool = False, preview_count: int = 10):
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    if backup:
        bak = path.with_suffix(path.suffix + '.bak')
        shutil.copy(path, bak)

    changed = 0
    previews = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        if 'assistant_summary' in item:
            orig = item['assistant_summary']
            cleaned = extract_assistant_text(orig)
            if cleaned != (orig or '').strip():
                changed += 1
                item['assistant_summary'] = cleaned
            else:
                # still normalize whitespace
                item['assistant_summary'] = (orig or '').strip()
            if i < preview_count:
                previews.append((item.get('qid'), orig, item['assistant_summary']))

    # write back
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {'total': len(data), 'changed': changed, 'previews': previews, 'backup': str(bak) if backup else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', required=True, help='path to json file')
    p.add_argument('--no-backup', action='store_true', help='do not create .bak backup')
    p.add_argument('--preview', action='store_true', help='only preview changes, do not write')
    args = p.parse_args()

    path = Path(args.file)
    if not path.exists():
        print('File not found:', path)
        return

    if args.preview:
        # run without writing: copy to memory and show previews
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        previews = []
        for i, item in enumerate(data[:10]):
            orig = item.get('assistant_summary')
            cleaned = extract_assistant_text(orig)
            previews.append((item.get('qid'), orig, cleaned))
        for qid, orig, cleaned in previews:
            print('---', qid)
            print('ORIG:', repr(orig)[:300])
            print('CLEAN:', repr(cleaned)[:300])
            print()
        return

    result = clean_file(path, backup=not args.no_backup, preview=False)
    print(f"Processed {result['total']} entries, modified {result['changed']} assistant_summary fields.")
    print('Backup created at:', result['backup'])
    print('\nSample previews (qid, orig->clean):')
    for qid, orig, clean in result['previews']:
        print(qid, '->', repr(clean)[:200])


if __name__ == '__main__':
    main()
