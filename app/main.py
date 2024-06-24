from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen

windowSize = 400
Window.size=(windowSize,windowSize*16/9)

Builder.load_file('screens.kv')

class PW(Screen):
    def enter(self, instance):
        #TODO: Private Key -> decrypt -> PWs
         
        print(instance.text)
        self.manager.current = "main"
        
class Main(Screen):
    pass

class Setting(Screen):
    pass

class Account(Screen):
    pass


class ChangePW(Screen):
    pass

class AccountManager(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(PW(name='pw')) # initial screen
        sm.add_widget(Main(name='main'))
        sm.add_widget(Setting(name="setting"))
        sm.add_widget(Account(name="account"))
        sm.add_widget(ChangePW(name="changepw"))
        return sm

if __name__ == '__main__':
    AccountManager().run()
