"""Native Kivy screens for grammar and dashboard; existing vocabulary stays intact."""
from datetime import datetime, timezone
from threading import Thread
from pathlib import Path
import json, random, hashlib
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform, get_color_from_hex as color
from grammar import load, write_json, correct, review_answer

class GrammarUI:
    def init_grammar(self):
        from main import ROOT
        self.grammar_path=self.data_dir/'grammar.json'; self.progress_path=self.data_dir/'progress.json'
        try: self.grammar=load(self.grammar_path)
        except Exception: self.grammar=load(ROOT/'assets/grammar.json')
        try: self.study=json.loads(self.progress_path.read_text(encoding='utf-8'))
        except Exception: self.study={}
        self.study.setdefault('best',{}); self.study.setdefault('review',{}); self.study.setdefault('vocab',{})
        self.screen='home'; self.importing=False
        self.remote_path=self.data_dir/'grammar_remote.json'
        try: self.remote_url=json.loads(self.remote_path.read_text(encoding='utf-8')).get('url','')
        except Exception: self.remote_url=''
        if self.remote_url: Clock.schedule_once(lambda dt:self.sync_grammar(self.remote_url,False),1)
    def persist_study(self):
        try: write_json(self.progress_path,self.study)
        except OSError as e: self.message('Không lưu được tiến độ',str(e))
    def vocab_key(self,e):
        return hashlib.sha256((e.hanzi+'\0'+e.meaning).encode()).hexdigest()
    def record_vocab(self,e,ok):
        if ok:
            self.study['vocab'][self.vocab_key(e)]=True; self.persist_study()
    def lessons(self): return [l for level in self.grammar['levels'] for l in level['lessons']]
    def page(self,title,back,subtitle=''):
        from main import button, label, vertical, rounded
        self.shell.clear_widgets(); self.screen='grammar'; outer=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(15))
        rounded(outer,'#F3F6FC',0); self.shell.add_widget(outer)
        head=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(10)); b=button('‹',lambda *_:back()); b.size_hint_x=None;b.width=dp(48);head.add_widget(b);head.add_widget(label(title,22));outer.add_widget(head)
        scroll=ScrollView(do_scroll_x=False); body=vertical();body.spacing=dp(14);scroll.add_widget(body);outer.add_widget(scroll)
        if subtitle: body.add_widget(label(subtitle,13))
        return body
    def show_home(self,*_):
        from main import button,label,card,ProgressTrack
        body=self.page('Học tiếng Trung',self.show_home); self.screen='home'
        hero=card('#185AA6',18); title=label('你好！ Xin chào',25);title.color=color('#FFFFFF');hero.add_widget(title); sub=label('Mỗi ngày một chút, tiến bộ thật nhiều.',13);sub.color=color('#DCEBFF');hero.add_widget(sub);body.add_widget(hero)
        lessons=self.lessons(); best=self.study['best']; done=sum(best.get(l['id'],0)>=60 for l in lessons); vocab=sum(self.vocab_key(e) in self.study['vocab'] for e in self.entries); total=len(lessons)+len(self.entries); pct=round(100*(done+vocab)/total) if total else 0
        row=BoxLayout(size_hint_y=None,height=dp(98),spacing=dp(8))
        for val,caption in [(str(done),'Bài ngữ pháp'),(str(sum(best.get(l['id'],0) for l in lessons)+10*vocab),'Điểm số'),(f'{pct}%','Tiến độ')]:
            c=card(padding=8);c.size_hint_y=1; a=label(val,24);a.color=color('#185AA6');a.halign='center';c.add_widget(a);b=label(caption,11);b.halign='center';c.add_widget(b);row.add_widget(c)
        body.add_widget(row);body.add_widget(label('Hôm nay bạn muốn học gì?',19))
        for title,desc,action,shade in [('词  Từ vựng','Học từ mới · Ghép câu · Phát âm',self.show_vocabulary,'#E4F0FF'),('语  Ngữ pháp','Cấu trúc câu · 5 dạng luyện tập',self.show_levels,'#EEE8FF')]:
            c=card(shade);c.add_widget(button(title+'  ›',lambda _,f=action:f(),True));c.add_widget(label(desc,13));body.add_widget(c)
        c=card();c.add_widget(label('Tiến độ học tập',18))
        for title,n,t in [('Từ vựng',vocab,len(self.entries)),('Ngữ pháp',done,len(lessons))]:
            c.add_widget(label(f'{title} · {n}/{t}',14));bar=ProgressTrack();bar.fraction=n/t if t else 0;c.add_widget(bar);bar.refresh()
        body.add_widget(c);c=card('#FFF0D9');c.add_widget(label('Ôn tập thông minh',18));c.add_widget(label(f'{len(self.study["review"])} câu đã lưu · {len(self.due_questions())} đến hạn',13));c.add_widget(button('Mở danh sách ôn tập',lambda *_:self.show_review(),True));body.add_widget(c)
    def show_vocabulary(self,*_):
        self.shell.clear_widgets();self.shell.add_widget(self.vocab_root);self.screen='vocab'
    def show_levels(self,*_):
        from main import button,label,card
        body=self.page('Ngữ pháp',self.show_home,'Chọn cấp độ phù hợp với bạn.');
        for level in self.grammar['levels']:
            c=card();c.add_widget(label(level['name'],19));done=sum(self.study['best'].get(l['id'],0)>=60 for l in level['lessons']);c.add_widget(label(f'{done}/{len(level["lessons"])} bài hoàn thành',13));c.add_widget(button('Xem bài học  ›',lambda _,l=level:self.show_level(l),True));body.add_widget(c)
        body.add_widget(button('Nhập Excel / JSON',lambda *_:self.import_grammar()))
        body.add_widget(button('Tải JSON từ GitHub',lambda *_:self.remote_grammar()))
    def show_level(self,level):
        from main import button,label,card
        body=self.page(level['name'],self.show_levels)
        for l in level['lessons']:
            c=card();c.add_widget(label(l['title'],19));c.add_widget(label(l['hantu']+' · '+l['pinyin'],16));c.add_widget(label('Điểm cao nhất: '+str(self.study['best'].get(l['id'],0)),13));c.add_widget(button('Học bài  ›',lambda _,lesson=l:self.show_lesson(lesson,level),True));body.add_widget(c)
        if not level['lessons']: body.add_widget(label('Chưa có bài học. Hãy nhập thêm dữ liệu.'))
    def speaker(self,text):
        from main import button, ROOT
        from kivy.uix.image import Image
        b=button('',lambda *_:self.speak_grammar(text),True)
        b.size_hint_x=None; b.width=dp(56)
        icon=Image(source=str(ROOT/'assets/speaker.png'),size_hint=(None,None),size=(dp(30),dp(30)))
        b.add_widget(icon); b.bind(center=lambda w,v:setattr(icon,'center',v));icon.center=b.center
        return b
    def speak_grammar(self,text):
        if platform=='android': self.play_answer(text)
        else: self.message('Phát âm','Chức năng dùng bộ giọng tiếng Trung của Android. Hãy thử trên điện thoại.')
    def show_lesson(self,l,level):
        from main import button,label,card
        body=self.page(l['title'],lambda:self.show_level(level),level['name']);c=card();c.add_widget(label(l['hantu'],40));c.add_widget(label(l['pinyin'],20));c.add_widget(label(l['meaning'],16));c.add_widget(self.speaker(l['hantu']));body.add_widget(c)
        c=card();c.add_widget(label('Cách sử dụng',19));c.add_widget(label(l['description']));body.add_widget(c)
        c=card('#E4F0FF');c.add_widget(label('CÔNG THỨC',13));c.add_widget(label(l['formula'],20));body.add_widget(c)
        if l.get('notes'): body.add_widget(label('Lưu ý: '+l['notes'],14))
        for e in l.get('examples',[]):
            c=card();c.add_widget(label(e['hantu'],25));c.add_widget(label(e['pinyin'],15));c.add_widget(label(e['meaning'],15));c.add_widget(self.speaker(e['hantu']));body.add_widget(c)
        body.add_widget(button('Bắt đầu luyện tập  →',lambda *_:self.start_quiz(l['exercises'],l,lambda:self.show_lesson(l,level)),True))
    def start_quiz(self,questions,lesson,back):
        self.quiz=list(questions);self.quiz_lesson=lesson;self.quiz_back=back;self.quiz_index=0;self.quiz_score=0;self.quiz_wrong=[];self.render_quiz()
    def render_quiz(self):
        from main import button,label,card,vertical,ProgressTrack
        q=self.quiz[self.quiz_index];body=self.page('Luyện tập',self.quiz_back,f'Câu {self.quiz_index+1}/{len(self.quiz)}'); self.quiz_locked=False;self.quiz_answer='';self.quiz_selected=[]
        bar=ProgressTrack();bar.fraction=self.quiz_index/len(self.quiz);body.add_widget(bar);bar.refresh()
        c=card();body.add_widget(c); names={'multiple_choice':'Trắc nghiệm','fill_blank':'Điền từ','reorder':'Sắp xếp câu','zh_to_vi':'Dịch Trung → Việt','vi_to_zh':'Dịch Việt → Trung'};c.add_widget(label(names[q['type']],13));c.add_widget(label(q['question'],25));
        if q['type']=='zh_to_vi':c.add_widget(self.speaker(q['question']))
        self.quiz_input=None;self.quiz_buttons=[]
        if q['type']=='multiple_choice':
            opts=q['options'][:];random.shuffle(opts)
            for opt in opts:
                b=button(opt,lambda w,o=opt:self.choose_option(o));self.quiz_buttons.append((b,opt));c.add_widget(b)
        elif q['type']=='reorder':
            self.quiz_tokens=q['tokens'][:];random.shuffle(self.quiz_tokens);self.quiz_selected_box=vertical();self.quiz_bank=GridLayout(cols=3,spacing=dp(6),size_hint_y=None);self.quiz_bank.bind(minimum_height=self.quiz_bank.setter('height'));c.add_widget(label('Đáp án của bạn',13));c.add_widget(self.quiz_selected_box);c.add_widget(self.quiz_bank);self.render_quiz_tokens()
        else:
            self.quiz_input=TextInput(font_name='StudyFont',font_size=sp(20),size_hint_y=None,height=dp(95),hint_text='Nhập đáp án',multiline=True);c.add_widget(self.quiz_input)
        self.quiz_check=button('Kiểm tra đáp án',lambda *_:self.submit_quiz(),True);c.add_widget(self.quiz_check);self.quiz_feedback=vertical();body.add_widget(self.quiz_feedback)
    def choose_option(self,opt):
        if self.quiz_locked:return
        self.quiz_answer=opt
        for b,v in self.quiz_buttons:b.background_color=color('#BBD8FF' if v==opt else '#EAF0FA')
    def render_quiz_tokens(self):
        from main import button,label
        self.quiz_selected_box.clear_widgets();self.quiz_bank.clear_widgets();self.quiz_selected_box.add_widget(label(''.join(self.quiz_tokens[i] for i in self.quiz_selected) or 'Chưa chọn từ',22))
        for i,t in enumerate(self.quiz_tokens):
            b=button(t,lambda _,n=i:self.toggle_quiz_token(n));b.disabled=i in self.quiz_selected;self.quiz_bank.add_widget(b)
        self.quiz_selected_box.add_widget(button('Xóa lựa chọn',lambda *_:self.reset_quiz_tokens()))
    def toggle_quiz_token(self,i):
        if not self.quiz_locked and i not in self.quiz_selected:self.quiz_selected.append(i);self.render_quiz_tokens()
    def reset_quiz_tokens(self):
        if not self.quiz_locked:self.quiz_selected=[];self.render_quiz_tokens()
    def submit_quiz(self):
        from main import button,label,card
        if self.quiz_locked:return
        q=self.quiz[self.quiz_index];a=self.quiz_input.text if self.quiz_input else (''.join(self.quiz_tokens[i] for i in self.quiz_selected) if q['type']=='reorder' else self.quiz_answer)
        if not a.strip() or (q['type']=='reorder' and len(self.quiz_selected)!=len(self.quiz_tokens)):self.message('Chưa hoàn thành','Hãy nhập hoặc chọn đủ đáp án.');return
        self.quiz_locked=True;self.quiz_check.disabled=True
        if self.quiz_input:self.quiz_input.disabled=True
        ok=correct(q,a);self.quiz_score+=int(ok)
        if not ok:self.quiz_wrong.append(q)
        review_answer(self.study,q,a,ok);self.persist_study();c=card('#DFF3E7' if ok else '#FCE4E2');c.add_widget(label('Chính xác!' if ok else 'Chưa đúng · Đã lưu để ôn',20));c.add_widget(label('Đáp án: '+q['answer'],19));
        if q.get('explanation'):c.add_widget(label(q['explanation'],14))
        if q.get('pinyin'):c.add_widget(label(q['pinyin'],14))
        audio=q.get('audioText') or (q['answer'] if q['type'] in ('vi_to_zh','reorder','fill_blank') else q['question'] if q['type']=='zh_to_vi' else '')
        if audio:c.add_widget(self.speaker(audio))
        c.add_widget(button('Tiếp theo  →',lambda *_:self.advance_quiz(),True));self.quiz_feedback.add_widget(c)
    def advance_quiz(self):
        if not self.quiz_locked:return
        self.quiz_index+=1
        if self.quiz_index<len(self.quiz):self.render_quiz();return
        self.show_results()
    def show_results(self):
        from main import button,label,card
        score=round(100*self.quiz_score/len(self.quiz));l=self.quiz_lesson
        if l:self.study['best'][l['id']]=max(score,self.study['best'].get(l['id'],0));self.persist_study()
        body=self.page('Kết quả',self.quiz_back);c=card();c.add_widget(label(f'{score}/100',42));c.add_widget(label(f'Đúng {self.quiz_score}/{len(self.quiz)} · Sai {len(self.quiz_wrong)}'));body.add_widget(c)
        for q in self.quiz_wrong:body.add_widget(label(q['question']+' → '+q['answer'],15))
        body.add_widget(button('Luyện lại',lambda *_:self.start_quiz(self.quiz,l,self.quiz_back),True));body.add_widget(button('Quay về',lambda *_:self.quiz_back()))
    def due_questions(self):
        now=datetime.now(timezone.utc);return [r['question'] for r in sorted(self.study['review'].values(),key=lambda r:(-r['wrong'],r['due'])) if datetime.fromisoformat(r['due'])<=now]
    def show_review(self,*_):
        from main import button,label,card
        body=self.page('Ôn tập thông minh',self.show_home);records=self.study['review'];due=self.due_questions();body.add_widget(label(f'{len(due)} câu đến hạn · {len(records)} câu đã lưu',16))
        if due:body.add_widget(button('Ôn các câu đến hạn',lambda *_:self.start_quiz(due,None,self.show_review),True))
        if records:body.add_widget(button('Ôn tất cả ngay',lambda *_:self.start_quiz([r['question'] for r in records.values()],None,self.show_review)))
        for r in sorted(records.values(),key=lambda r:-r['wrong']):
            c=card();c.add_widget(label(r['question']['question'],20));c.add_widget(label(f'Sai {r["wrong"]} lần · Đúng liên tiếp {r["streak"]}'));c.add_widget(label('Ôn tiếp: '+datetime.fromisoformat(r['due']).astimezone().strftime('%d/%m %H:%M'),13));body.add_widget(c)
    def import_grammar(self):
        from main import button
        if self.importing:return
        if platform=='android':
            from android_picker import DocumentPicker
            if self.picker is None:self.picker=DocumentPicker(self.data_dir,self.choose_sheet,lambda msg:self.message('Lỗi chọn tệp',msg))
            self.picker.selected=self.load_grammar_file;self.picker.open();return
        c=BoxLayout(orientation='vertical');chooser=FileChooserListView(path=str(Path.home()),filters=['*.xlsx','*.json']);c.add_widget(chooser)
        def selected(*_):
            if chooser.selection:self.dismiss();self.load_grammar_file(chooser.selection[0])
        c.add_widget(button('Nhập',selected,True));c.add_widget(button('Hủy',lambda *_:self.dismiss()));self.show_popup('Chọn dữ liệu ngữ pháp',c)
    def load_grammar_file(self,path):self.grammar_task(lambda:load(path))
    def grammar_task(self,task,interactive=True):
        if self.importing:return
        self.importing=True
        def work():
            try:
                data=task();write_json(self.grammar_path,data);Clock.schedule_once(lambda dt:self.grammar_done(data,interactive),0)
            except Exception as e:
                msg=str(e);Clock.schedule_once(lambda dt:self.grammar_failed(msg,interactive),0)
        Thread(target=work,daemon=True).start()
    def grammar_done(self,data,interactive=True):
        self.importing=False;self.grammar=data
        if interactive:self.show_levels();self.message('Đã cập nhật','Dữ liệu mới đã được lưu. Tiến độ theo ID được giữ nguyên.')
        elif self.screen=='home' and not self.popup:self.show_home()
    def grammar_failed(self,msg,interactive=True):
        self.importing=False
        if interactive:self.message('Không cập nhật được',msg+'\nDữ liệu cũ vẫn được giữ.')
    def remote_grammar(self):
        from main import button,label
        c=BoxLayout(orientation='vertical',spacing=dp(10));c.add_widget(label('Dán URL JSON công khai trên raw.githubusercontent.com.'));field=TextInput(text=self.remote_url,font_name='StudyFont',size_hint_y=None,height=dp(90),multiline=True);c.add_widget(field)
        def fetch(*_):
            from urllib.parse import urlparse
            url=field.text.strip();p=urlparse(url)
            if p.scheme!='https' or p.netloc!='raw.githubusercontent.com':self.message('URL không hợp lệ','Cần URL HTTPS raw.githubusercontent.com.');return
            self.dismiss()
            self.remote_url=url
            write_json(self.remote_path,{'url':url})
            self.sync_grammar(url,True)
        def disable(*_):
            self.remote_url='';write_json(self.remote_path,{'url':''});self.dismiss()
        c.add_widget(button('Lưu URL và tải dữ liệu',fetch,True));c.add_widget(button('Tắt đồng bộ tự động',disable));c.add_widget(button('Hủy',lambda *_:self.dismiss()));self.show_popup('GitHub',c)
    def sync_grammar(self,url,interactive):
        def task():
            from urllib.request import urlopen
            from grammar import validate
            with urlopen(url,timeout=20) as r: raw=r.read(20*1024*1024+1)
            if len(raw)>20*1024*1024:raise ValueError('JSON quá lớn')
            return validate(json.loads(raw.decode('utf-8-sig')))
        self.grammar_task(task,interactive)
