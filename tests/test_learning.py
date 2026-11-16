from collections import Counter
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from learning import Entry, Session, compact, load_excel, read_deck, save_deck, tokens, shuffled_tokens

ROOT = Path(__file__).resolve().parents[1]


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.entries, _ = read_deck(ROOT / 'assets/vocab.json')

    def test_four_unique_answers_both_directions(self):
        for reverse in (False, True):
            s = Session(self.entries, reverse=reverse, rng=random.Random(1))
            for _ in range(24):
                e = s.next()
                options = s.options()
                self.assertEqual(len(set(options)), 4)
                self.assertIn(s.answer(e), options)

    def test_alternative_meanings_never_used_as_distractors(self):
        items = self.entries + [Entry('你好', '', 'Chào bạn')]
        s = Session(items)
        s.current = items[0]
        for _ in range(20):
            self.assertNotIn('Chào bạn', s.options())

    def test_alternative_hanzi_excluded_in_reverse(self):
        items = self.entries + [Entry('您好', '', 'Xin chào')]
        s = Session(items, reverse=True)
        s.current = items[0]
        for _ in range(20):
            self.assertNotIn('您好', s.options())

    def test_insufficient_data(self):
        self.assertIsNone(Session(self.entries[:3]).next())

    def test_no_repeat_within_round(self):
        s = Session(self.entries)
        self.assertEqual(len({s.next() for _ in self.entries}), len(self.entries))

    def test_score_locked_after_first_answer(self):
        s = Session(self.entries)
        e = s.next()
        self.assertFalse(s.submit('sai'))
        self.assertIsNone(s.submit(s.answer(e)))
        self.assertEqual((s.correct, s.total), (0, 1))
        e = s.next()
        self.assertTrue(s.submit(s.answer(e)))
        self.assertEqual((s.correct, s.total), (1, 2))

    def test_skip_not_counted_as_wrong(self):
        s = Session(self.entries)
        s.next()
        s.next()
        self.assertEqual((s.total, s.skipped), (0, 1))

    def test_repeated_tokens_and_punctuation(self):
        text = '我 的 朋友 喜欢 我 的 猫 。'
        for _ in range(20):
            parts = shuffled_tokens(text)
            self.assertEqual(Counter(parts), Counter(tokens(text)))
            self.assertNotEqual(parts, tokens(text))
        s = Session([Entry(text, '', 'Bạn của tôi thích con mèo của tôi.')], mode='sentence')
        s.next()
        self.assertTrue(s.submit(compact(text)))
        s.next()
        self.assertFalse(s.submit(compact(text).replace('。', '')))

    def test_character_fallback(self):
        self.assertEqual(tokens('我喜欢中文'), ['我', '喜', '欢', '中', '文'])

    def test_existing_three_column_excel(self):
        rows, skipped = load_excel(ROOT/'assets/du_lieu_mau.xlsx', 'TuVung')
        self.assertEqual(len(rows), 12)
        self.assertFalse(skipped)
        self.assertEqual(rows[0].hanviet, '')

    def test_optional_header(self):
        rows, _ = load_excel(ROOT/'assets/du_lieu_mau.xlsx', 'TuVung', header=False)
        self.assertEqual(rows[0].hanzi, 'Hantu')

    def test_four_columns_bad_rows_duplicates(self):
        # Fake workbook exercises input handling without authoring test spreadsheets.
        class Sheet:
            def reset_dimensions(self): pass
            def iter_rows(self, **kwargs):
                return iter([('A','B','C','D'), ('学生','xuésheng','Học sinh','Học sinh'),
                             (None,None,None,None), ('水','shuǐ',None,'Thủy'),
                             ('学生','xuésheng','Học sinh','Học sinh')])
        class Book:
            def __getitem__(self, name): return Sheet()
            def close(self): pass
        with patch('learning.validate_xlsx'), patch('openpyxl.load_workbook', return_value=Book()):
            rows, skipped = load_excel('unused.xlsx','Data')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].hanviet, 'Học sinh')
        self.assertEqual(skipped, [4])

    def test_offline_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'deck.json'
            save_deck(path, self.entries, 'Từ vựng')
            entries, title = read_deck(path)
            self.assertEqual(entries, self.entries)
            self.assertEqual(title, 'Từ vựng')


if __name__ == '__main__':
    unittest.main()
