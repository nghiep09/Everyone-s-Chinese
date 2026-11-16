"""Grammar content import, answer checking and durable progress."""
import json, os, unicodedata, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zipfile import is_zipfile
from learning import validate_xlsx

TYPES = {'multiple_choice','fill_blank','reorder','zh_to_vi','vi_to_zh'}

def write_json(path, data):
    path = Path(path); temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)

def normalize(s):
    return re.sub(r'[\s。！？!?.,，、；;：:]+', '', unicodedata.normalize('NFKC', str(s)).casefold())

def correct(q, answer):
    return normalize(answer) in {normalize(a) for a in [q['answer'], *q.get('acceptedAnswers', [])]}

def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get('levels'), list) or not data['levels']:
        raise ValueError('JSON cần có danh sách levels.')
    ids=set()
    def identity(item):
        i=item.get('id');
        if not isinstance(i,str) or not i.strip() or i in ids: raise ValueError('ID thiếu hoặc trùng: '+str(i))
        ids.add(i)
    def required(item, fields):
        for f in fields:
            if not isinstance(item.get(f),str) or not item[f].strip(): raise ValueError(f'Thiếu {f}: {item.get("id")}')
    for level in data['levels']:
        identity(level); required(level,['name'])
        if not isinstance(level.get('lessons'),list): raise ValueError('Thiếu lessons')
        for lesson in level['lessons']:
            identity(lesson); required(lesson,['title','hantu','pinyin','meaning','formula','description'])
            for e in lesson.get('examples',[]):
                identity(e); required(e,['hantu','pinyin','meaning'])
            if not lesson.get('exercises'): raise ValueError('Bài học cần bài tập: '+lesson['id'])
            for q in lesson['exercises']:
                identity(q); required(q,['type','question','answer'])
                if q['type'] not in TYPES: raise ValueError('Loại bài tập không hợp lệ')
                for field in ('options','tokens','acceptedAnswers'):
                    if field in q and (not isinstance(q[field],list) or not all(isinstance(x,str) and x.strip() for x in q[field])): raise ValueError('Danh sách không hợp lệ: '+field)
                if q['type']=='multiple_choice' and (len(q.get('options',[]))<2 or q['answer'] not in q['options']): raise ValueError('Trắc nghiệm thiếu đáp án đúng')
                if q['type']=='reorder' and (len(q.get('tokens',[]))<2 or sorted(normalize(''.join(q['tokens'])))!=sorted(normalize(q['answer']))): raise ValueError('Mảnh ghép không khớp đáp án')
    return data

def load(path):
    path=Path(path)
    if path.stat().st_size>20*1024*1024: raise ValueError('Tệp quá 20 MB')
    if not is_zipfile(path): return validate(json.loads(path.read_text(encoding='utf-8-sig')))
    from openpyxl import load_workbook
    validate_xlsx(path)
    with path.open('rb') as stream:
        wb=load_workbook(stream,read_only=True,data_only=True)
        try:
            def rows(name):
                ws=wb[name]; ws.reset_dimensions(); iterator=ws.values
                headers=[str(x or '').strip() for x in next(iterator)]
                for i,row in enumerate(iterator):
                    if i>=20000: raise ValueError('Tối đa 20.000 dòng mỗi sheet')
                    d=dict(zip(headers,[str(x).strip() if x is not None else '' for x in row]));
                    if any(d.values()): yield d
            levels={}; lessons={}
            for r in rows('Levels'):
                if r['LevelID'] in levels: raise ValueError('LevelID trùng')
                levels[r['LevelID']]={'id':r['LevelID'],'name':r['LevelName'],'order':int(r.get('Order') or 0),'lessons':[]}
            for r in rows('Lessons'):
                l={'id':r['LessonID'], **{k:r.get(v,'') for k,v in [('title','Title'),('hantu','Hantu'),('pinyin','Pinyin'),('meaning','Meaning'),('formula','Formula'),('description','Description'),('notes','Notes')]},'examples':[],'exercises':[]}
                if l['id'] in lessons: raise ValueError('LessonID trùng')
                lessons[l['id']]=l; levels[r['LevelID']]['lessons'].append(l)
            for r in rows('Examples'):
                lessons[r['LessonID']]['examples'].append({'id':r['ExampleID'],'hantu':r['Hantu'],'pinyin':r['Pinyin'],'meaning':r['Meaning']})
            for r in rows('Exercises'):
                q={'id':r['QuestionID'],'type':r['Type'],'question':r['Question'],'answer':r['Answer'],'explanation':r.get('Explanation',''),'audioText':r.get('AudioText',''),'pinyin':r.get('Pinyin','')}
                for field,col in [('tokens','Tokens'),('acceptedAnswers','AcceptedAnswers')]:
                    if r.get(col): q[field]=[s.strip() for s in r[col].split('|') if s.strip()]
                opts=[r.get('Option'+x,'') for x in 'ABCD'];
                if any(opts): q['options']=[x for x in opts if x]
                lessons[r['LessonID']]['exercises'].append(q)
            return validate({'version':1,'levels':sorted(levels.values(),key=lambda l:l['order'])})
        finally: wb.close()

def review_answer(state,q,answer,ok,now=None):
    now=now or datetime.now(timezone.utc); records=state.setdefault('review',{}); old=records.get(q['id'])
    if ok and not old: return
    r=old or {'wrong':0,'streak':0}; r['question']=q; r['lastAnswer']=answer
    if ok:
        r['streak']=min(5,r['streak']+1); delay=timedelta(days=[1,3,7,14,30][r['streak']-1])
    else:
        r['wrong']+=1; r['streak']=0; delay=timedelta(minutes=10)
    r['due']=(now+delay).isoformat(); records[q['id']]=r
