import unittest, tempfile, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from grammar import load, correct, review_answer, write_json, validate
ROOT=Path(__file__).resolve().parents[1]
class GrammarTests(unittest.TestCase):
    def test_import(self):
        for name in ['grammar.json','Grammar.xlsx']:
            d=load(ROOT/'assets'/name)
            self.assertEqual(len(d['levels']),6)
            self.assertEqual(sum(len(l['exercises']) for v in d['levels'] for l in v['lessons']),30)
    def test_answers(self):
        q={'answer':'我是学生。','acceptedAnswers':['我是學生']}
        self.assertTrue(correct(q,'我 是 学生'));self.assertTrue(correct(q,'我是學生'));self.assertFalse(correct(q,'我是老师'))
    def test_review(self):
        q={'id':'Q1','answer':'是'};s={};now=datetime.now(timezone.utc)
        review_answer(s,q,'有',False,now);r=s['review']['Q1'];self.assertEqual(r['wrong'],1);self.assertEqual(datetime.fromisoformat(r['due']),now+timedelta(minutes=10))
        review_answer(s,q,'是',True,now);self.assertEqual(datetime.fromisoformat(r['due']),now+timedelta(days=1))
        review_answer(s,q,'是',True,now);self.assertEqual(r['streak'],2)
    def test_duplicate(self):
        d=load(ROOT/'assets/grammar.json');d['levels'].append(d['levels'][0]);self.assertRaises(ValueError,validate,d)
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'progress.json';write_json(p,{'best':{'G001':100}});self.assertEqual(json.loads(p.read_text())['best']['G001'],100)
