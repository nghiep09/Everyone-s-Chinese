"""Pure Python learning engine. No Android or UI dependency."""
from collections import defaultdict
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import random
import unicodedata
from zipfile import ZipFile


def compact(s):
    return ''.join(unicodedata.normalize('NFC', s).split())


def key(s):
    return ' '.join(unicodedata.normalize('NFC', s).split()).casefold()


@dataclass(frozen=True)
class Entry:
    hanzi: str
    pinyin: str
    meaning: str
    hanviet: str = ''
    row: int = 0


def validate_xlsx(path):
    if Path(path).stat().st_size > 20 * 1024 * 1024:
        raise ValueError('File vượt quá 20 MB. Hãy chia thành file nhỏ hơn.')
    with ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 150 * 1024 * 1024:
            raise ValueError('File Excel quá lớn sau giải nén.')


def sheet_names(path):
    from openpyxl import load_workbook
    validate_xlsx(path)
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        return wb.sheetnames
    finally:
        wb.close()


def load_excel(path, sheet, header=True):
    from openpyxl import load_workbook
    validate_xlsx(path)
    wb = load_workbook(path, read_only=True, data_only=True)
    entries, skipped, seen = [], [], set()
    try:
        ws = wb[sheet]
        # Do not trust incorrect producer-supplied worksheet dimensions.
        ws.reset_dimensions()
        for number, cells in enumerate(ws.iter_rows(max_col=4, values_only=True), 1):
            if number > 20001:
                raise ValueError('Tối đa 20.000 dòng mỗi sheet. Hãy chia bộ học.')
            if header and number == 1:
                continue
            values = [str(c).strip() if c is not None else '' for c in cells]
            if not any(values):
                continue
            a, b, c, d = values
            if not a or not c or any(len(v) > 2000 for v in values):
                skipped.append(number)
                continue
            signature = (compact(a), key(c))
            if signature in seen:
                continue
            seen.add(signature)
            entries.append(Entry(a, b, c, d, number))
        if not entries:
            raise ValueError('Sheet không có dòng hợp lệ. Kiểm tra cột A/C và lựa chọn tiêu đề.')
        return entries, skipped
    finally:
        wb.close()


def tokens(text):
    parts = text.split()
    return parts if len(parts) > 1 else list(compact(text))


def shuffled_tokens(text, rng=None):
    rng = rng or random
    result = tokens(text)
    original = result[:]
    rng.shuffle(result)
    if result == original:
        for i in range(1, len(result)):
            if result[i] != result[0]:
                result[0], result[i] = result[i], result[0]
                break
    return result


class Session:
    def __init__(self, entries, mode='vocab', reverse=False, rng=None):
        self.entries = entries
        self.mode, self.reverse = mode, reverse
        self.rng = rng or random.Random()
        self.total = self.correct = self.skipped = 0
        self.current = None
        self.answered = False
        self.pool = []
        self.valid_answers = defaultdict(set)
        self.answer_labels = {}
        for e in entries:
            a = self.answer(e)
            self.valid_answers[key(self.prompt(e))].add(key(a))
            self.answer_labels.setdefault(key(a), a)
        if mode == 'vocab':
            self.eligible = [e for e in entries if len(self.answer_labels) -
                             len(self.valid_answers[key(self.prompt(e))]) >= 3]
        else:
            self.eligible = [e for e in entries if len(set(tokens(e.hanzi))) >= 2]

    def prompt(self, e):
        return e.meaning if self.reverse or self.mode == 'sentence' else compact(e.hanzi)

    def answer(self, e):
        return compact(e.hanzi) if self.reverse else e.meaning

    def next(self):
        if not self.eligible:
            self.current = None
            return None
        if self.current is not None and not self.answered:
            self.skipped += 1
        if not self.pool:
            self.pool = self.eligible[:]
            self.rng.shuffle(self.pool)
        self.current = self.pool.pop()
        self.answered = False
        return self.current

    def options(self):
        excluded = self.valid_answers[key(self.prompt(self.current))]
        candidates = [v for k, v in self.answer_labels.items() if k not in excluded]
        result = self.rng.sample(candidates, 3) + [self.answer(self.current)]
        self.rng.shuffle(result)
        return result

    def submit(self, response):
        if self.current is None or self.answered:
            return None
        expected = compact(self.current.hanzi) if self.mode == 'sentence' else key(self.answer(self.current))
        actual = compact(response) if self.mode == 'sentence' else key(response)
        correct = actual == expected
        self.answered = True
        self.total += 1
        self.correct += int(correct)
        return correct


def save_deck(path, entries, title):
    """Write a complete snapshot atomically; never destroy a working deck on error."""
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({'title': title, 'entries': [asdict(e) for e in entries]}, ensure_ascii=False), encoding='utf-8')
    os.replace(temp, path)


def read_deck(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    entries = [Entry(**e) for e in data['entries']]
    if not entries:
        raise ValueError('Bộ học trống')
    return entries, str(data['title'])
