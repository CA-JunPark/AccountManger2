import flet as ft
import sql
from passlib.hash import pbkdf2_sha256

def changePage(pageNum: int, page:ft.Page):
    # Need Update after this function
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
        case 5:
            return Setting(page)
        case 6:
            return ChangePW(page)

class CenterCon(ft.Container):
    """Aligned center container"""
    def __init__(self,content,margin=0):
        super().__init__()
        self.content = content
        self.margin = margin
        self.alignment = ft.alignment.center

class AccountBtn(ft.TextButton):
    def __init__(self, id, text, on_click, data, **kwargs):
        super().__init__(kwargs)
        self.id = id
        self.text = text
        self.style = ft.ButtonStyle(
                        color="BLACK",
                        bgcolor="#45D094",
                        overlay_color="#1E9690",
                        shape=ft.RoundedRectangleBorder(radius=10),
                    )
        self.width = 230
        self.height = 100
        self.data = data
        self.on_click = on_click
        self.on_click = lambda e: on_click(e, self.data)

# Pages
class PW: # 0
    def __init__(self, page: ft.Page):
        self.db = sql.DynamoDB()
        self.page = page
        self.hashedPW = self.db.get(id=0)['pw']
        
        self.pw_field = ft.TextField(bgcolor="WHITE24",
                                autofocus=True,
                                password=True,
                                multiline=False,
                                text_align=ft.TextAlign.CENTER,
                                on_submit=self.enter)
        
        self.page.add(
            ft.Column(
                spacing = 15,
                controls=[
                    CenterCon(
                        ft.Image("assets/security_icons.png",
                                width=180),
                        margin=ft.margin.only(top=40)
                    ),
                    CenterCon(
                        ft.Text("Please enter your password",
                                size=20),
                    ),
                    self.pw_field,
                    CenterCon(
                        ft.ElevatedButton(content=ft.Text(value="Enter",size=20),
                                          color="BLACK",
                                          bgcolor="#45D094",
                                          style=ft.ButtonStyle(
                                              overlay_color="#1E9690",
                                          ),
                                          height=35,
                                          width=100,
                                          on_click=self.enter),
                    )
                ]   
            )
        )
    
    def enter(self,e):
        pw = self.pw_field.value
        
        if pbkdf2_sha256.verify(pw, self.hashedPW):
            # Go to Main
            changePage(2,self.page)
            self.page.update()
        else:
            # open dialog
            dlg = ft.AlertDialog(title=ft.Text("Wrong Password", 
                                               size=20, 
                                               text_align="center"))
            self.page.open(dlg)
            
class PWsetUp: # 1
    def __init__(self, page: ft.Page):
        self.db = sql.DynamoDB()
        self.page = page

        self.pw_field = ft.TextField(bgcolor="WHITE24",
                                        autofocus=True,
                                        password=True,
                                        multiline=False,
                                        text_align=ft.TextAlign.CENTER,
                                        on_submit=self.enter)
        
        self.pwConfirmField = ft.TextField(bgcolor="WHITE24",
                                           autofocus=True,
                                           password=True,
                                           multiline=False,
                                           text_align=ft.TextAlign.CENTER,
                                           on_submit=self.enter)

        self.page.add(
            ft.Column(
                spacing=15,
                controls=[
                    CenterCon(
                        ft.Image("assets/security_icons.png",
                                    width=180),
                        margin=ft.margin.only(top=40)
                    ),
                    CenterCon(
                        ft.Text("Set Up Your Password",
                                size=20),
                    ),
                    self.pw_field,
                    self.pwConfirmField,
                    CenterCon(
                        ft.ElevatedButton(content=ft.Text(value="Enter", size=20),
                                            color="BLACK",
                                            bgcolor="#45D094",
                                            style=ft.ButtonStyle(
                            overlay_color="#1E9690",
                        ),
                            height=35,
                            width=100,
                            on_click=self.enter),
                    )
                ]
            )
        )

    def enter(self, e):
        pw = self.pw_field.value
        pwConfirm = self.pwConfirmField.value
        print(pw)
        print(pwConfirm)
        
        valid = False
        
        if pw == "":
            alertMsg = "Cannot use empty String"
        elif pw != pwConfirm:
            alertMsg = "Passwords Does Not Match"
            
        elif pw == pwConfirm:
            valid = True
            
            # hash pw
            pw = pbkdf2_sha256.hash(pw)
            
            # update admin password
            self.db.update(0,pw=pw)
            
            alertMsg = "Password Created"
        
        # open dialog
        dlg = ft.AlertDialog(title=ft.Text(
            alertMsg, size=20, text_align="center"))
        self.page.open(dlg)
        
        # Go to PW
        if valid:
            changePage(0, self.page)
            self.page.update()
        
class Main: # 2
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = sql.DynamoDB()
        # get all accounts from DB
        self.accounts = sorted(self.db.getAll(), key=lambda x: x['name'].lower())
        
        self.accountsSubset = self.accounts.copy()
        
        self.sortDropDown = ft.Dropdown(width=125,
                                        label="Sort Order",
                                        bgcolor="WHITE24",
                                        options=[
                                            ft.dropdown.Option(
                                                "Ascending"),
                                            ft.dropdown.Option(
                                                "Descending")
                                        ],
                                        value="Ascending",
                                        on_change=self.sortOrder
                                        )
        
        self.input = ft.TextField(bgcolor="WHITE24",
                                    autofocus=True,
                                    multiline=False,
                                    text_align=ft.TextAlign.LEFT,
                                    width=150,
                                    on_submit=self.search)
        
        self.AccountButtons = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
        )
        self.updateAccountButtons()
        
        self.ButtonContainer = ft.Container(
            alignment=ft.alignment.center,
            width = 400,
            height = 400*16/9 - 161,
            content=self.AccountButtons
            )
        
        # Page
        self.page.add(
            ft.Column(
                controls=[
                    # Top Bar  
                    ft.Container(
                        margin=ft.margin.only(top=40),
                        alignment=ft.alignment.top_center,
                        content=
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.IconButton(icon=ft.icons.SETTINGS_ROUNDED,
                                                        on_click=self.clickSettings),
                                    self.sortDropDown,
                                    self.input,
                                    ft.IconButton(icon=ft.icons.SEARCH_ROUNDED,
                                                  on_click=self.search)
                                ]
                            )
                    ),
                    # Account Buttons
                    self.ButtonContainer,
                ]
            )
        )
        
        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ADD_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickAdd)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.START_FLOAT
        
        self.page.update()
        
    def updateAccountButtons(self):
        self.AccountButtons.controls = [AccountBtn(id=account.get('id'),
                                                    text=f"{account.get('name')}\n{account.get('account')}\n{
                                                    account.get('pw')}",
                                                    on_click=self.clickAccount,
                                                    data=account)
                                                    for account in self.accountsSubset]
                                            
    def clickSettings(self, e):
        changePage(5, self.page)
        self.page.update()
        
    def search(self, e):
        val = self.input.value
        if val == "":
            return
        else:
            self.accountsSubset = [d for d in self.accounts if val.lower() in d.get('name').lower()]
        self.sortOrder(e)
        
    def sortOrder(self, e):
        if self.sortDropDown.value == "Ascending":
            self.accountsSubset = sorted(self.accountsSubset, key=lambda x: x['name'].lower())
        else:
            self.accountsSubset = sorted(
                self.accountsSubset, key=lambda x: x['name'].lower(), reverse=True)
        
        self.updateAccountButtons()
        self.page.update()
            
    def clickAccount(self, e, data):
        print("btn Click")
        print(data)
    
    def clickAdd(self, e):
        print("ADD")
        
class Account: # 3
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("Account")))

class AddAccount: # 4
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("AddAccount")))

class Setting: # 5
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("Setting")))

class ChangePW: # 6
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.add(ft.SafeArea(ft.Text("ChangePW")))

def main(page: ft.Page):
    page.title = "Account Manager 2"
    page.window.icon = "assets/security_icons.png"

    width = 400
    page.window.width = width
    page.window.height = width*16/9
    
    # get admin pw
    db = sql.DynamoDB()
    adminPW = db.get(id=0)['pw']
    
    # if no pw, set up
    if adminPW == "":
        app = PWsetUp(page)
    else:
        # app = PW(page)
        # app = Main(page)
        app = Account(page)
    
ft.app(main)
