#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
print문을 logger로 일괄 변환
"""

import re

def fix_prints(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # JSON 출력만 stdout으로 남기고 나머지는 logger로 변환
    # 마지막 print(json.dumps(...))만 남기고 나머지 모두 변환

    lines = content.split('\n')
    new_lines = []

    for i, line in enumerate(lines):
        # JSON 출력 라인은 그대로 유지 (마지막 부분)
        if 'print(json.dumps(' in line:
            new_lines.append(line)
            continue

        # 일반 print문 변환
        if re.match(r'\s*print\(', line):
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent

            # print("[PHASE ...") 패턴
            if '[PHASE' in line or 'PHASE' in line:
                msg = re.search(r'print\(["\'](.+?)["\']\)', line)
                if msg:
                    new_lines.append(f'{indent_str}logger.section("{msg.group(1)}")')
                else:
                    new_lines.append(line.replace('print(', 'logger.info('))

            # print("=" * 80) 패턴
            elif '"="' in line or "'='" in line:
                # 섹션 구분자는 제거 (logger.section이 처리)
                continue

            # print() 빈 줄
            elif line.strip() == 'print()':
                # 빈 줄은 제거
                continue

            # print(f"[OK] ...")
            elif '[OK]' in line:
                msg = re.search(r'print\(f?"?\[OK\]\s*(.+?)["\']\)', line)
                if msg:
                    new_lines.append(f'{indent_str}logger.info({msg.group(1)})')
                else:
                    new_lines.append(line.replace('print(f"[OK]', 'logger.info(f"').replace('[OK] ', ''))

            # print(f"[WARN] ...")
            elif '[WARN]' in line:
                new_lines.append(line.replace('print(f"[WARN]', 'logger.warn(f"').replace('[WARN] ', ''))

            # print(f"[ERROR] ...")
            elif '[ERROR]' in line:
                new_lines.append(line.replace('print(f"[ERROR]', 'logger.error(f"').replace('[ERROR] ', ''))

            # print(f"[INFO] ...")  (이미 stderr로 리다이렉트된 것들)
            elif 'file=sys.stderr' in line:
                # 이미 처리됨 - logger로 변환
                new_lines.append(line.replace('print(f"[INFO]', 'logger.info(f"').replace('[INFO] ', '').replace(', file=sys.stderr', ''))

            # 기타 print문
            else:
                new_lines.append(line.replace('print(', 'logger.info('))

        else:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"[OK] Fixed {file_path}")

if __name__ == "__main__":
    fix_prints("auto_recommendation_engine.py")
