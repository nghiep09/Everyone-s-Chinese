"""Học tiếng Trung: Android Kivy application, also runnable on desktop."""
from pathlib import Path
from threading import Thread
import json
import os

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.utils import platform, get_color_from_hex as color
from grammar_ui import GrammarUI
from learning import Entry, Session, compact, load_excel, read_deck, save_deck, sheet_names, shuffled_tokens

ROOT = Path(__file__).resolve().parent
FONT = str(ROOT / 'assets' / 'NotoSansSC-Regular.otf')
LabelBase.register('StudyFont', fn_regular=FONT)
NAVY, BLUE, TEXT = '#172B3A', '#2466B0', '#172B3A'
PALE, GREEN, RED = '#EAF0FA', '#DFF2E5', '#FCE4E2'


class StudyOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(font_name='StudyFont', font_size=sp(15), height=dp(52), **kwargs)


def label(text='', size=16, **kwargs):
    widget = Label(text=text, font_name='StudyFont', font_size=sp(size), color=color(TEXT),
                   size_hint_y=None, halign='left', valign='middle', **kwargs)
    widget.bind(width=lambda w, v: setattr(w, 'text_size', (max(1, v), None)))
    widget.bind(texture_size=lambda w, v: setattr(w, 'height', v[1] + dp(14)))
    return widget


class SoftButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.fill = Color(*self.background_color)
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
        self.bind(pos=self.repaint, size=self.repaint, background_color=self.repaint,
                  state=self.repaint)

    def repaint(self, *_):
        self.shape.pos, self.shape.size = self.pos, self.size
        rgba = list(self.background_color)
        if self.state == 'down':
            rgba[:3] = [c * .88 for c in rgba[:3]]
        self.fill.rgba = rgba


def button(text, callback, primary=False):
    widget = SoftButton(text=text, font_name='StudyFont', font_size=sp(15),
                        size_hint_y=None, height=dp(48), halign='center', valign='middle', background_normal='',
                        background_down='', background_color=color(BLUE if primary else PALE),
                        color=color('#FFFFFF' if primary else TEXT))
    # The custom canvas draws the rounded background; disable Button's rectangle.
    widget.background_normal = str(ROOT / 'assets' / 'transparent.png')
    widget.background_down = str(ROOT / 'assets' / 'transparent.png')
    widget.bind(width=lambda w, v: setattr(w, 'text_size', (max(1, v-dp(16)), None)))
    widget.bind(texture_size=lambda w, v: setattr(w, 'height', max(dp(48), v[1]+dp(20))))
    widget.bind(on_release=callback)
    return widget


def vertical():
    box = BoxLayout(orientation='vertical', spacing=dp(9), size_hint_y=None)
    box.bind(minimum_height=box.setter('height'))
    return box


def rounded(widget, shade='#FFFFFF', radius=18, shadow=False):
    with widget.canvas.before:
        if shadow:
            Color(0.16, 0.18, 0.15, .055)
            drop = RoundedRectangle(radius=[dp(radius)])
        Color(*color(shade))
        rect = RoundedRectangle(radius=[dp(radius)])
    def update(*_):
        rect.pos, rect.size = widget.pos, widget.size
        if shadow:
            drop.pos = (widget.x, widget.y-dp(3))
            drop.size = widget.size
    widget.bind(pos=update, size=update)
    update()
    return widget


def card(shade='#FFFFFF', padding=14):
    box = vertical()
    box.padding = dp(padding)
    return rounded(box, shade, shadow=shade == '#FFFFFF')


class ProgressTrack(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(7), **kwargs)
        self.fraction = 0
        with self.canvas:
            Color(*color('#E6E7E6'))
            self.track = RoundedRectangle(radius=[dp(4)])
            self.bar_color = Color(*color(BLUE))
            self.bar = RoundedRectangle(radius=[dp(4)])
        self.bind(pos=self.refresh, size=self.refresh)

    def refresh(self, *_):
        self.track.pos, self.track.size = self.pos, self.size
        self.bar_color.a = 1 if self.fraction else 0
        self.bar.pos = self.pos
        self.bar.size = (self.width * self.fraction, self.height)


class ChineseApp(GrammarUI, App):
    title = 'Học tiếng Trung'

    def build(self):
        Window.clearcolor = color('#F3F6FC')
        if platform != 'android':
            Window.size = (412, 850)
        self.mode, self.reverse = 'vocab', False
        self.entries = []
        self.deck_title = ''
        self.session = None
        self.popup = None
        self.picker = None
        self.speech = None
        self.busy = False
        self.last_header = True
        self.data_dir = Path(self.user_data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.deck_path = self.data_dir / 'deck.json'
        self.settings_path = self.data_dir / 'settings.json'
        try:
            settings = json.loads(self.settings_path.read_text(encoding='utf-8'))
            self.mode = settings.get('mode', 'vocab')
            if self.mode not in ('vocab', 'sentence'):
                self.mode = 'vocab'
            self.reverse = bool(settings.get('reverse', False))
            self.last_header = bool(settings.get('header', True))
        except (OSError, ValueError):
            pass
        try:
            self.entries, self.deck_title = read_deck(self.deck_path)
        except (OSError, ValueError, TypeError, KeyError):
            self.entries, self.deck_title = self.sample_data()
        outer = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(12), dp(10)])
        rounded(outer, '#F3F6FC', radius=0)
        header = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(10))
        emblem = button('⌂', lambda *_: self.show_home(), True)
        emblem.size_hint_x = None
        emblem.width = dp(48)
        emblem.font_size = sp(28)
        header.add_widget(emblem)
        titles = vertical()
        titles.spacing = 0
        titles.add_widget(label('Học tiếng Trung', 22))
        sub = label('Mỗi ngày một chút, tiến bộ thật nhiều', 10)
        sub.color = color('#69777E')
        titles.add_widget(sub)
        header.add_widget(titles)
        outer.add_widget(header)
        self.scroll = ScrollView(do_scroll_x=False)
        page = vertical()
        page.spacing = dp(14)
        self.scroll.add_widget(page)
        outer.add_widget(self.scroll)
        file_card = card()
        file_row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        file_info = vertical()
        file_info.spacing = 0
        self.deck_label = label('', 15)
        self.deck_meta = label('', 11)
        self.deck_meta.color = color('#69777E')
        file_info.add_widget(self.deck_label)
        file_info.add_widget(self.deck_meta)
        file_row.add_widget(file_info)
        change = button('Đổi tệp', lambda *_: self.open_file())
        change.size_hint_x = None
        change.width = dp(88)
        file_row.add_widget(change)
        file_card.add_widget(file_row)
        page.add_widget(file_card)
        tabs = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6), padding=dp(3))
        rounded(tabs, '#FFFFFF')
        self.vocab_tab = button('Từ vựng', lambda *_: self.switch_mode('vocab'))
        self.sentence_tab = button('Ghép từ', lambda *_: self.switch_mode('sentence'))
        tabs.add_widget(self.vocab_tab)
        tabs.add_widget(self.sentence_tab)
        page.add_widget(tabs)
        progress = card()
        top = BoxLayout(size_hint_y=None, height=dp(35))
        top.add_widget(label('Tiến độ luyện tập', 17))
        self.progress_label = label('', 15)
        self.progress_label.size_hint_x = .5
        self.progress_label.halign = 'right'
        self.progress_label.color = color(BLUE)
        top.add_widget(self.progress_label)
        progress.add_widget(top)
        self.progress_track = ProgressTrack()
        progress.add_widget(self.progress_track)
        self.score_label = label('', 13)
        self.score_label.color = color('#227762')
        progress.add_widget(self.score_label)
        page.add_widget(progress)
        self.content = card(padding=16)
        page.add_widget(self.content)
        self.next_button = button('Bỏ qua', lambda *_: self.next_question(), True)
        outer.add_widget(self.next_button)
        nav = BoxLayout(size_hint_y=None, height=dp(51), spacing=dp(6))
        nav.add_widget(button('Trang chủ', lambda *_: self.show_home()))
        nav.add_widget(button('Bộ từ', lambda *_: self.show_deck()))
        nav.add_widget(button('Cài đặt', lambda *_: self.settings()))
        outer.add_widget(nav)
        Window.bind(on_keyboard=self.on_key)
        self.init_grammar()
        self.restart()
        self.vocab_root = outer
        self.shell = BoxLayout(orientation='vertical')
        self.show_home()
        return self.shell

    def sample_data(self):
        path = ROOT / 'assets' / ('sentences.json' if self.mode == 'sentence' else 'vocab.json')
        return read_deck(path)

    def persist_settings(self):
        try:
            temp = self.settings_path.with_suffix('.tmp')
            temp.write_text(json.dumps({'mode': self.mode, 'reverse': self.reverse,
                                       'header': self.last_header}), encoding='utf-8')
            os.replace(temp, self.settings_path)
        except OSError as exc:
            self.message('Chưa lưu được cài đặt', str(exc))

    def restart(self):
        self.session = Session(self.entries, self.mode, self.reverse)
        self.next_question()

    def switch_mode(self, mode):
        if self.busy or mode == self.mode:
            return
        self.mode = mode
        self.persist_settings()
        self.restart()

    def show_deck(self):
        content = BoxLayout(orientation='vertical', spacing=dp(8))
        content.add_widget(label(f'{self.deck_title} · {len(self.entries)} mục', 16))
        scroll = ScrollView(do_scroll_x=False)
        rows = vertical()
        for e in self.entries[:200]:
            item = card(PALE, 10)
            item.add_widget(label(compact(e.hanzi) + '  ·  ' + e.meaning, 16))
            item.add_widget(label(f'{e.pinyin}  |  Hán Việt: {e.hanviet or "—"}', 12))
            rows.add_widget(item)
        if len(self.entries) > 200:
            rows.add_widget(label('Hiển thị 200 mục đầu. Toàn bộ dữ liệu vẫn dùng để học.', 12))
        scroll.add_widget(rows)
        content.add_widget(scroll)
        content.add_widget(button('Đổi tệp Excel', lambda *_: (self.dismiss(), self.open_file()), True))
        content.add_widget(button('Đóng', lambda *_: self.dismiss()))
        self.show_popup('Bộ từ của bạn', content)

    def score(self):
        s = self.session
        self.deck_label.text = self.deck_title
        self.deck_meta.text = f'{len(self.entries)} mục · Học offline'
        self.score_label.text = f'Đúng {s.correct}     ·     Sai {s.total-s.correct}     ·     Bỏ qua {s.skipped}'
        count = len(s.eligible)
        completed = s.total + s.skipped
        progress = (completed % count or (count if completed else 0)) if count else 0
        self.progress_label.text = f'{progress} / {count}'
        self.progress_track.fraction = progress / count if count else 0
        self.progress_track.refresh()
        for tab, mode in ((self.vocab_tab, 'vocab'), (self.sentence_tab, 'sentence')):
            active = mode == self.mode
            tab.background_color = color(BLUE if active else '#F3F6FC')
            tab.color = color('#FFFFFF' if active else TEXT)

    def next_question(self):
        if self.busy:
            return
        if self.speech:
            self.speech.stop()
        self.content.clear_widgets()
        self.next_button.text = 'Bỏ qua'
        entry = self.session.next()
        self.score()
        self.scroll.scroll_y = 1
        if entry is None:
            self.content.add_widget(label('Chưa đủ dữ liệu', 24))
            self.content.add_widget(label('Từ vựng cần 4 đáp án khác nhau. Ghép câu cần ít nhất 2 mảnh khác nhau. Hãy đổi sheet hoặc dùng bài mẫu trong Cài đặt.'))
            return
        direction = 'VIỆT → TRUNG' if self.mode == 'sentence' or self.reverse else 'TRUNG → VIỆT'
        badge = label(direction, 12)
        badge.color = color('#AF7426')
        self.content.add_widget(badge)
        self.content.add_widget(label(self.session.prompt(entry), 30))
        if self.mode == 'vocab':
            self.content.add_widget(label('Chạm vào một đáp án.', 14))
            self.options = []
            for value in self.session.options():
                b = button(value, lambda w, v=value: self.pick(w, v))
                self.options.append((b, value))
                self.content.add_widget(b)
        else:
            self.content.add_widget(label('Chạm các chữ theo đúng thứ tự.', 14))
            self.parts = shuffled_tokens(entry.hanzi)
            self.selected = []
            self.content.add_widget(label('ĐÁP ÁN CỦA BẠN', 12))
            self.selected_grid = GridLayout(cols=3, spacing=dp(8), padding=dp(10), size_hint_y=None)
            rounded(self.selected_grid, PALE, radius=14)
            self.selected_grid.bind(minimum_height=self.selected_grid.setter('height'))
            self.content.add_widget(self.selected_grid)
            self.content.add_widget(label('CÁC MẢNH CÓ SẴN', 12))
            self.bank_grid = GridLayout(cols=3, spacing=dp(6), size_hint_y=None)
            self.bank_grid.bind(minimum_height=self.bank_grid.setter('height'))
            self.content.add_widget(self.bank_grid)
            self.content.add_widget(button('Xóa lựa chọn', lambda *_: self.clear_sentence()))
            self.content.add_widget(button('Kiểm tra', lambda *_: self.check_sentence(), True))
            self.render_parts()
        self.feedback = vertical()
        self.content.add_widget(self.feedback)
        self.content.add_widget(button('Hướng dẫn', lambda *_: self.help()))

    def pick(self, widget, value):
        result = self.session.submit(value)
        if result is None:
            return
        for b, option in self.options:
            if option == self.session.answer(self.session.current):
                b.background_color = color(GREEN)
                b.text = 'ĐÚNG · ' + option
                b.color = color('#146C49')
            elif b == widget:
                b.background_color = color(RED)
                b.text = 'SAI · ' + option
                b.color = color('#A83232')
        self.finish(result)

    def render_parts(self):
        self.selected_grid.clear_widgets()
        self.bank_grid.clear_widgets()
        for i in self.selected:
            tile = button(self.parts[i], lambda w, n=i: self.toggle_part(n))
            tile.font_size = sp(26)
            tile.background_color = color('#FFFFFF')
            self.selected_grid.add_widget(tile)
        for i, part in enumerate(self.parts):
            if i not in self.selected:
                tile = button(part, lambda w, n=i: self.toggle_part(n))
                tile.font_size = sp(24)
                self.bank_grid.add_widget(tile)

    def toggle_part(self, index):
        if self.session.answered:
            return
        if index in self.selected:
            self.selected.remove(index)
        else:
            self.selected.append(index)
        self.render_parts()

    def clear_sentence(self):
        if not self.session.answered:
            self.selected = []
            self.render_parts()

    def check_sentence(self):
        if self.session.answered:
            return
        if len(self.selected) != len(self.parts):
            self.message('Chưa ghép xong', 'Hãy chọn hết các mảnh trước khi kiểm tra.')
            return
        result = self.session.submit(''.join(self.parts[i] for i in self.selected))
        self.finish(result)

    def finish(self, correct):
        e = self.session.current
        self.record_vocab(e, correct)
        self.feedback.clear_widgets()
        self.feedback.padding = dp(14)
        rounded(self.feedback, GREEN if correct else RED, radius=14)
        heading = label('Chính xác!' if correct else 'Chưa đúng. Câu trả lời đúng:', 20)
        heading.color = color('#11733C' if correct else '#B52828')
        self.feedback.add_widget(heading)
        self.feedback.add_widget(label(compact(e.hanzi), 28))
        if platform == 'android':
            speaker = button('', lambda *_: self.play_answer(compact(e.hanzi)), True)
            speaker.size_hint_x = None
            speaker.width = dp(56)
            speaker.pos_hint = {'center_x': .5}
            icon = Image(source=str(ROOT / 'assets' / 'speaker.png'),
                         size_hint=(None, None), size=(dp(32), dp(32)))
            speaker.add_widget(icon)
            speaker.bind(center=lambda widget, center: setattr(icon, 'center', center))
            icon.center = speaker.center
            self.feedback.add_widget(speaker)
        self.feedback.add_widget(label(f'Nghĩa: {e.meaning}'))
        self.feedback.add_widget(label(f'Pinyin: {e.pinyin or "Chưa có dữ liệu"}'))
        self.feedback.add_widget(label(f'Hán Việt: {e.hanviet or "Chưa có dữ liệu ở cột D"}'))
        self.next_button.text = 'Câu tiếp theo  →'
        self.score()
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), .15)

    def show_popup(self, title, content):
        if self.popup:
            self.popup.dismiss()
        self.popup = Popup(title=title, title_font='StudyFont', title_size=sp(18),
                           content=content, size_hint=(.94, .88),
                           background='', background_color=color('#F3F6FC'),
                           separator_color=color(BLUE), title_color=color(TEXT))
        self.popup.open()

    def dismiss(self):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def message(self, title, text):
        content = BoxLayout(orientation='vertical', spacing=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(label(text))
        content.add_widget(scroll)
        content.add_widget(button('Đóng', lambda *_: self.dismiss(), True))
        self.show_popup(title, content)

    def settings(self):
        if self.busy:
            return
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        content.add_widget(label('Chế độ học', 15))
        mode = Spinner(text='Từ vựng' if self.mode == 'vocab' else 'Ghép câu',
                       values=('Từ vựng', 'Ghép câu'), font_name='StudyFont',
                       option_cls=StudyOption, size_hint_y=None, height=dp(54))
        content.add_widget(mode)
        content.add_widget(label('Hướng hỏi (áp dụng cho từ vựng)', 14))
        direction = Spinner(text='Việt → Trung' if self.reverse else 'Trung → Việt',
                            values=('Trung → Việt', 'Việt → Trung'), font_name='StudyFont',
                            option_cls=StudyOption, size_hint_y=None, height=dp(54))
        content.add_widget(direction)
        content.add_widget(label('Áp dụng sẽ bắt đầu một lượt học mới. Dữ liệu Excel đã nhập vẫn được giữ.', 14))

        def apply(use_sample=False):
            self.mode = 'vocab' if mode.text == 'Từ vựng' else 'sentence'
            self.reverse = direction.text == 'Việt → Trung'
            if use_sample:
                entries, title = self.sample_data()
                try:
                    save_deck(self.deck_path, entries, title)
                except OSError as exc:
                    self.message('Không lưu được', str(exc))
                    return
                self.entries, self.deck_title = entries, title
            self.dismiss()
            self.persist_settings()
            self.restart()
        content.add_widget(button('Áp dụng / Bắt đầu lại', lambda *_: apply(), True))
        content.add_widget(button('Dùng bài mẫu của chế độ này', lambda *_: apply(True)))
        content.add_widget(button('Đóng', lambda *_: self.dismiss()))
        self.show_popup('Cài đặt học', content)

    def run_background(self, task, success):
        if self.busy:
            return
        self.busy = True
        self.deck_label.text = 'Đang đọc dữ liệu…'

        def work():
            try:
                result = task()
                Clock.schedule_once(lambda dt: done(result), 0)
            except Exception as exc:
                message = str(exc)
                Clock.schedule_once(lambda dt: fail(message), 0)

        def done(result):
            self.busy = False
            self.score()
            success(result)

        def fail(message):
            self.busy = False
            self.score()
            self.message('Không đọc được Excel', message + '\nBộ học trước vẫn được giữ.')
        Thread(target=work, daemon=True).start()

    def open_file(self):
        if self.busy:
            return
        if platform == 'android':
            try:
                if self.picker is None:
                    from android_picker import DocumentPicker
                    self.picker = DocumentPicker(self.data_dir, self.choose_sheet,
                        lambda text: self.message('Không mở được tài liệu', text))
                self.picker.selected = self.choose_sheet
                self.picker.open()
            except Exception as exc:
                self.message('Không mở được trình chọn tệp', str(exc))
        else:
            content = BoxLayout(orientation='vertical', spacing=dp(8))
            chooser = FileChooserListView(path=str(Path.home()), filters=['*.xlsx', '*.xlsm'])
            content.add_widget(chooser)
            def selected(*_):
                if chooser.selection:
                    path = chooser.selection[0]
                    self.dismiss()
                    self.choose_sheet(path)
            content.add_widget(button('Chọn', selected, True))
            content.add_widget(button('Hủy', lambda *_: self.dismiss()))
            self.show_popup('Chọn Excel', content)

    def choose_sheet(self, path):
        self.run_background(lambda: sheet_names(path), lambda names: self.sheet_dialog(path, names))

    def sheet_dialog(self, path, names):
        content = BoxLayout(orientation='vertical', spacing=dp(12))
        content.add_widget(label('Chọn sheet dữ liệu'))
        sheet = Spinner(text=names[0], values=names, font_name='StudyFont', option_cls=StudyOption,
                        size_hint_y=None, height=dp(54))
        content.add_widget(sheet)
        row = BoxLayout(size_hint_y=None, height=dp(56))
        header = CheckBox(active=self.last_header, size_hint_x=None, width=dp(48), color=color(BLUE))
        row.add_widget(header)
        row.add_widget(label('Dòng 1 là tiêu đề', 15))
        content.add_widget(row)
        content.add_widget(label('A: Chữ Hán\nB: Pinyin\nC: Nghĩa tiếng Việt\nD: Hán Việt (không bắt buộc)\n\nNhập file mới sẽ thay bộ học đang dùng và đặt điểm về 0.', 15))

        def load(*_):
            name, has_header = sheet.text, header.active
            self.dismiss()
            def task():
                entries, skipped = load_excel(path, name, has_header)
                save_deck(self.deck_path, entries, name)
                return entries, skipped
            def success(result):
                self.entries, skipped = result
                self.deck_title = name
                self.last_header = has_header
                self.persist_settings()
                self.restart()
                if skipped:
                    self.message('Đã nhập dữ liệu', f'Đã nhập {len(self.entries)} mục. Bỏ qua {len(skipped)} dòng thiếu A/C hoặc quá dài: ' + ', '.join(map(str, skipped[:15])))
            self.run_background(task, success)
        content.add_widget(button('Bắt đầu học', load, True))
        content.add_widget(button('Hủy', lambda *_: self.dismiss()))
        self.show_popup('Nhập dữ liệu', content)

    def help(self):
        self.message('Cách sử dụng', '1. Chọn Excel (.xlsx/.xlsm), chọn sheet và xác định dòng tiêu đề.\n\n'
            '2. Cài đặt: chọn Từ vựng hoặc Ghép câu. Từ vựng có hai hướng hỏi.\n\n'
            '3. Sau khi trả lời sẽ hiện chữ Hán, nghĩa, pinyin và Hán Việt. Hán Việt lấy từ cột D, không tự dịch.\n\n'
            '4. Ghép câu: nên viết cột A có dấu cách, ví dụ 我 喜欢 中文 。 Nếu không có dấu cách, tách từng ký tự. Chấm theo câu mẫu, có tính dấu câu.\n\n'
            '5. Câu không lặp trong một vòng. Điểm tính câu đã trả lời; Bỏ qua tính riêng.\n\n'
            'Dữ liệu đã nhập được giữ trên máy. Điểm được đặt lại khi mở lại ứng dụng, đổi chế độ hoặc nhập file. Muốn cập nhật Excel, chọn nhập lại file.\n\n'
            'Dữ liệu và font có sẵn nên học được offline. File trên Google Drive cần tải về trước. Giới hạn 20 MB / 20.000 dòng mỗi sheet.')

    def on_key(self, window, keycode, *args):
        if keycode == 27:
            if self.popup:
                self.dismiss()
            elif self.screen != 'home':
                self.show_home()
            else:
                content = BoxLayout(orientation='vertical', spacing=dp(12))
                content.add_widget(label('Thoát ứng dụng? Bộ học đã nhập vẫn được lưu. Điểm của lượt này sẽ đặt lại khi mở lại.'))
                content.add_widget(button('Tiếp tục học', lambda *_: self.dismiss(), True))
                content.add_widget(button('Thoát', lambda *_: self.stop()))
                self.show_popup('Thoát', content)
            return True
        return False

    def play_answer(self, text):
        from android_speech import MandarinSpeech
        if self.speech is None or self.speech.closed:
            self.speech = MandarinSpeech(lambda msg: self.message('Phát âm', msg))
        self.speech.play(text)

    def on_pause(self):
        if self.speech:
            self.speech.stop()
        return True

    def on_stop(self):
        if self.speech:
            self.speech.close()
        if self.picker:
            self.picker.close()


if __name__ == '__main__':
    import sys
    sys.modules['main'] = sys.modules[__name__]
    ChineseApp().run()
