#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 파일의 print문 검사
stdout 오염을 방지하기 위해 file=sys.stderr가 없는 print문 탐지
"""

import os
import re
import sys
from pathlib import Path

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

def check_file(filepath):
    """
    파일에서 잘못된 print문 검사

    Returns:
        (violations, total_prints)
    """
    violations = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # print문 찾기
        if re.search(r'^\s*print\(', line):
            # JSON 출력은 허용 (print(json.dumps(...)))
            if 'json.dumps' in line:
                continue

            # file=sys.stderr가 있으면 OK
            if 'file=sys.stderr' in line:
                continue

            # logger 사용은 OK
            if 'logger.' in line:
                continue

            # 위반 발견
            violations.append({
                'line_num': i,
                'content': line.strip()
            })

    return violations

def check_all_files(directory='.'):
    """
    디렉토리의 모든 Python 파일 검사
    """
    print("=" * 80)
    print("PYTHON PRINT STATEMENT CHECKER")
    print("=" * 80)
    print()

    total_violations = 0
    total_files_checked = 0
    files_with_issues = []

    # Python 파일 찾기 (venv 제외)
    for filepath in Path(directory).rglob('*.py'):
        # venv, __pycache__ 제외
        if '.venv' in str(filepath) or '__pycache__' in str(filepath):
            continue

        # 테스트/체크 스크립트 제외
        if filepath.name in ['check_print_statements.py', 'fix_prints.py', 'log_manager.py']:
            continue

        total_files_checked += 1
        violations = check_file(filepath)

        if violations:
            files_with_issues.append((filepath, violations))
            total_violations += len(violations)

    # 결과 출력
    if total_violations == 0:
        print(f"✅ All {total_files_checked} Python files are clean!")
        print()
        return 0
    else:
        print(f"❌ Found {total_violations} violations in {len(files_with_issues)} files:")
        print()

        for filepath, violations in files_with_issues:
            print(f"📁 {filepath}")
            for v in violations:
                print(f"   Line {v['line_num']}: {v['content']}")
            print()

        print("=" * 80)
        print("FIX INSTRUCTIONS:")
        print("=" * 80)
        print()
        print("Replace print statements with one of:")
        print("  1. logger.info(\"...\")     # For logs")
        print("  2. print(..., file=sys.stderr)  # For quick debugging")
        print("  3. print(json.dumps(...))  # For JSON output only")
        print()
        print("See PYTHON_LOGGING_RULES.md for details")
        print()

        return 1

if __name__ == "__main__":
    exit_code = check_all_files()
    sys.exit(exit_code)
