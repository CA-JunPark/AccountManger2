from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.metrics import dp

windowSize = 400
Window.size=(windowSize,windowSize*16/9)

Builder.load_file('screens.kv')

class PW(Screen):
    def pwEnter(self, instance):
        print(instance.text)
        self.manager.current = "main"
        
class InitialPW(Screen):
    pass

class Main(Screen):
    def on_enter(self,*args):
        accounts = self.ids.accounts
        for i in range(100):
            accounts.add_widget(Button(text=str(i), size_hint_y=None, height=dp(30)))
        
    def on_setting_press(self, instance):
        print("Setting")
        
    def on_spinner_press(self, instance):
        print(instance.text)
    
    def searchEnter(self, instance):
        print("search Enter: ", instance.text)
        
class Setting(Screen):
    pass

class Account(Screen):
    pass

class AddAccount(Screen):
    pass

class ChangePW(Screen):
    pass

class AccountManager(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(Main(name='main'))
        sm.add_widget(PW(name='pw')) # initial screen
        sm.add_widget(Setting(name="setting"))
        sm.add_widget(Account(name="account"))
        sm.add_widget(ChangePW(name="changepw"))
        return sm

if __name__ == '__main__':
    AccountManager().run()
