"""
Main application of the OpenCMR
"""
from kivy.app import App
from kivy.uix.button import Button


class OpenCMRApp(App):

    def build(self):
        return Button(text="Hello Button")


if __name__ == "__main__":
    OpenCMRApp().run()
