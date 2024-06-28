import flet as ft
import time


def changePage(pageNum: int, page):
    page.controls.clear()
    match pageNum:
        case 0:
            return PW(page)
        case 1: 
            return PWsetUp(page)
        case 2:
            return Main(page)
        case 3:
            return Account(page)
        case 4:
            return AddAccount(page)
        
class PW: # 0
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("PW")))

class PWsetUp: # 1
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("PWsetUp")))
        
class Main: # 2
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("Main")))
        
class Account: # 3
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("Account")))

class AddAccount: # 4
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("AddAccount")))

        
def main(page: ft.Page):
    page.title = "Account Manager 2"
    page.window.icon = 
    width = 400
    page.window.width = width
    page.window.height = width*16/9
    
    app = PW(page)
    # app = changePage(1,page)
    # page.update()
    


ft.app(main)
