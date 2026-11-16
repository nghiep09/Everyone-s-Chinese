"""Mandarin playback for the Android study screen."""
from kivy.clock import Clock
from jnius import PythonJavaClass, autoclass, java_method

TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
Locale = autoclass('java.util.Locale')


class MandarinSpeech(PythonJavaClass):
    __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']

    def __init__(self, report):
        super().__init__()
        self.report = report
        self.pending = None
        self.engine = None
        self.ready = False
        self.closed = False

    def play(self, text):
        self.pending = text
        if self.ready:
            self._speak()
        elif self.engine is None:
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            self.engine = TextToSpeech(activity.getApplicationContext(), self)

    @java_method('(I)V')
    def onInit(self, status):
        Clock.schedule_once(lambda dt: self._initialized(status), 0)

    def _initialized(self, status):
        if self.closed:
            return
        if status != TextToSpeech.SUCCESS:
            error = 'Hãy kiểm tra dịch vụ Chuyển văn bản thành giọng nói trong Cài đặt Android.'
        elif self.engine.setLanguage(Locale.SIMPLIFIED_CHINESE) < 0:
            error = 'Hãy tải giọng Tiếng Trung (Trung Quốc) trong cài đặt Chuyển văn bản thành giọng nói, rồi bấm loa lại.'
        else:
            self.ready = True
            if self.pending:
                self._speak()
            return
        show_error = bool(self.pending)
        self.close()
        if show_error:
            self.report(error)

    def _speak(self):
        text, self.pending = self.pending, None
        result = self.engine.speak(text, TextToSpeech.QUEUE_FLUSH, None, 'study-answer')
        if result == TextToSpeech.ERROR:
            self.report('Điện thoại chưa đọc được câu này. Hãy kiểm tra giọng tiếng Trung trong Cài đặt Android.')

    def stop(self):
        self.pending = None
        if self.ready:
            self.engine.stop()

    def close(self):
        self.closed = True
        self.stop()
        self.ready = False
        if self.engine is not None:
            self.engine.shutdown()
            self.engine = None
