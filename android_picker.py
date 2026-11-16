"""Android Storage Access Framework: no broad storage permission needed."""
from pathlib import Path
from threading import Thread
from kivy.clock import Clock


class DocumentPicker:
    REQUEST = 4812

    def __init__(self, directory, selected, error):
        self.directory = Path(directory)
        self.selected, self.error = selected, error
        self.busy = False
        from android import activity
        activity.bind(on_activity_result=self.on_result)

    def open(self):
        if self.busy:
            return
        self.busy = True
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def launch():
            try:
                Intent = autoclass('android.content.Intent')
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType('*/*')
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                activity.startActivityForResult(intent, self.REQUEST)
            except Exception as exc:
                message = str(exc)
                Clock.schedule_once(lambda dt, message=message: self.failed(message), 0)
        launch()

    def failed(self, message):
        self.busy = False
        self.error(message)

    def on_result(self, request, result, intent):
        if request != self.REQUEST:
            return
        if result != -1 or intent is None:
            Clock.schedule_once(lambda dt: setattr(self, 'busy', False), 0)
            return
        try:
            uri = str(intent.getData().toString())
            # Resolve app classes on the activity callback thread, BEFORE
            # starting a Python worker (which may use the system class loader).
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            copier = autoclass('vn.hoctiengtrung.DocumentCopy')
        except Exception as exc:
            message = str(exc)
            Clock.schedule_once(lambda dt, message=message: self.failed(message), 0)
            return

        def copy():
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
                path = str(self.directory / 'import.xlsx')
                copier.copy(activity, uri, path)
                Clock.schedule_once(lambda dt, path=path: self.completed(path), 0)
            except Exception as exc:
                message = str(exc)
                Clock.schedule_once(lambda dt, message=message: self.failed(message), 0)
        Thread(target=copy, daemon=True).start()

    def completed(self, path):
        self.busy = False
        self.selected(path)

    def close(self):
        from android import activity
        activity.unbind(on_activity_result=self.on_result)
