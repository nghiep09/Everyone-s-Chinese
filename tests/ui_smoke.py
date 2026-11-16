"""Optional desktop UI check. Run from repository root with Kivy installed."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.clock import Clock
from main import ChineseApp, GREEN, RED, color

temp = tempfile.TemporaryDirectory()


class SmokeApp(ChineseApp):
    @property
    def user_data_dir(self):
        return temp.name


app = SmokeApp()
errors = []
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(temp.name)
out.mkdir(parents=True, exist_ok=True)


def capture_vocab(dt):
    try:
        app.show_vocabulary()
        assert len(app.options) == 4
        app.root.export_to_png(str(out/'01_vocabulary.png'))
        expected = app.session.answer(app.session.current)
        wrong, value = next((b, v) for b, v in app.options if v != expected)
        app.pick(wrong, value)
        assert app.session.total == 1 and app.session.correct == 0
        assert list(wrong.background_color) == color(RED)
        good = next(b for b, v in app.options if v == expected)
        assert list(good.background_color) == color(GREEN)
        app.pick(good, expected)
        assert app.session.total == 1
        assert any('Hán Việt:' in w.text for w in app.feedback.children if hasattr(w, 'text'))
        Clock.schedule_once(capture_result, .5)
    except Exception as exc:
        errors.append(exc)
        app.stop()


def capture_result(dt):
    try:
        app.root.export_to_png(str(out/'02_result.png'))
        app.mode = 'sentence'
        app.entries, app.deck_title = app.sample_data()
        app.restart()
        app.toggle_part(0)
        app.toggle_part(0)
        assert app.selected == []
        app.clear_sentence()
        from learning import tokens
        for token in tokens(app.session.current.hanzi):
            index = next(i for i, value in enumerate(app.parts) if value == token and i not in app.selected)
            app.toggle_part(index)
        Clock.schedule_once(capture_sentence, .5)
    except Exception as exc:
        errors.append(exc)
        app.stop()


def capture_sentence(dt):
    try:
        app.root.export_to_png(str(out/'03_sentence.png'))
        app.check_sentence()
        assert app.session.correct == 1
        app.check_sentence()
        assert app.session.total == 1
        app.settings()
        Clock.schedule_once(finish, .5)
    except Exception as exc:
        errors.append(exc)
        app.stop()


def finish(dt):
    try:
        assert app.popup is not None
        app.dismiss()
    except Exception as exc:
        errors.append(exc)
    app.stop()


Clock.schedule_once(capture_vocab, 1)
app.run()
if errors:
    raise errors[0]
print('UI SMOKE PASS: wrong/right colors, lock scoring, Han Viet, sentence tokens, settings.')
