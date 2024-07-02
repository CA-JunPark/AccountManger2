import flet as ft
import sql
from passlib.hash import pbkdf2_sha256

def changePage(pageNum: int, page:ft.Page, db: sql.DynamoDB,data={}):
    # Need Update after this function
    page.controls.clear()
    page.floating_action_button = None
    
    match pageNum:
        case 0:
            return PW(page,db)
        case 1: 
            return PWsetUp(page, db)
        case 2:
            return Main(page, db)
        case 3:
            return AddAccount(page, db)
        case 4:
            if len(data) == 0:
                return
            return Account(page, db, data)
        case 5:
            return Setting(page, db)
        case 6:
            return ChangePW(page, db)

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
        self.content = ft.Text(text,
                               size=18)
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

class Confirm(ft.AlertDialog):
    def __init__(self,content:str,onYes,onNo,**kwargs):
        super().__init__(modal=True,
                         title=ft.Text("Please confirm"),
                         content=ft.Text(f"{content}"),
                         actions=[
                             ft.TextButton("Yes", on_click=onYes),
                             ft.TextButton("No", on_click=onNo),
                         ],
                         actions_alignment=ft.MainAxisAlignment.END)
        
class ColorButton(ft.TextButton):
    def __init__(self, text, on_click=None):
        super().__init__(content=ft.Text(f"{text}",
                                       size=20),
                       style=ft.ButtonStyle(
                            color="BLACK",
                            bgcolor="#45D094",
                            overlay_color="#1E9690"),
                       height=45,
                       width=100,
                       on_click=on_click)
# Pages
class PW: # 0
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.db = db
        self.page = page
        self.hashedPW = self.db.get(id=0)['pw']
        
        self.pw_field = ft.TextField(bgcolor="WHITE24",
                                autofocus=True,
                                password=True,
                                multiline=False,
                                text_align=ft.TextAlign.CENTER,
                                on_submit=self.enter)
        with open("assets/security_icons.txt", "r") as f:
            img = f.read()
            
        self.page.add(
            ft.Column(
                spacing = 15,
                controls=[
                    CenterCon(
                        ft.Image(src_base64=img,
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
            changePage(2,self.page, self.db)
            self.page.update()
        else:
            # open dialog
            dlg = ft.AlertDialog(title=ft.Text("Wrong Password", 
                                               size=20, 
                                               text_align="center"))
            self.page.open(dlg)
            
class PWsetUp: # 1
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.db = db
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
            changePage(0, self.page, self.db)
            self.page.update()
        
class Main: # 2
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.page = page
        self.db = db
        
        # get all accounts from DB
        self.accounts = sorted(self.db.getAll(), key=lambda x: x['name'].lower())
        
        self.accountsSubset = self.accounts.copy()
        
        self.sortButton = ft.IconButton(icon=ft.icons.ARROW_UPWARD_ROUNDED,
                                        on_click=self.clickSort, data="UP")
        
        self.input = ft.TextField(label="Search",
                                    bgcolor="WHITE24",
                                    multiline=False,
                                    text_align=ft.TextAlign.LEFT,
                                    width=170,
                                    on_submit=self.search)
            
        self.AccountButtons = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
        )
        self.updateAccountButtons()
        
        if self.page.platform == ft.PagePlatform.WINDOWS:
            w = 400
            h = w * 16/9 - 170
            topMargin = 0
        elif self.page.platform == ft.PagePlatform.ANDROID:
            w = 350
            h = w * 16/9 - 75
            topMargin = 40
        
        self.ButtonContainer = ft.Container(
            alignment=ft.alignment.center,
            width = w,
            height = h,
            content=self.AccountButtons
            )
        
        # Page
        self.page.add(
            ft.Column(
                controls=[
                    # Top Bar  
                    ft.Container(
                        margin=ft.margin.only(top=topMargin),
                        content=
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10,
                                controls=[
                                    ft.IconButton(icon=ft.icons.SETTINGS_ROUNDED,
                                                        on_click=self.clickSettings),
                                    self.sortButton,
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
        changePage(5, self.page, self.db)
        self.page.update()
    
    def clickSort(self, e):
        if self.sortButton.data == "UP":
            self.sortButton.icon = ft.icons.ARROW_DOWNWARD_ROUNDED
            self.sortButton.data = "DOWN"
        else:
            self.sortButton.icon = ft.icons.ARROW_UPWARD_ROUNDED
            self.sortButton.data = "UP"
        
        self.sortOrder(e)
        
    def search(self, e):
        val = self.input.value
        if val == "":
            self.accountsSubset = self.accounts
        else:
            self.accountsSubset = [d for d in self.accounts if val.lower() in d.get('name').lower()]
        self.sortOrder(e)
        
    def sortOrder(self, e):
        if self.sortButton.data == "UP":
            self.accountsSubset = sorted(self.accountsSubset, key=lambda x: x['name'].lower())
        else:
            self.accountsSubset = sorted(
                self.accountsSubset, key=lambda x: x['name'].lower(), reverse=True)
        
        self.updateAccountButtons()
        self.page.update()
            
    def clickAccount(self, e, data):
        changePage(4, self.page, self.db, data)
        self.page.update()
    
    def clickAdd(self, e):
        changePage(3, self.page, self.db)
        self.page.update()

class AddAccount:  # 3
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.page = page
        self.db = db
        self.uploaded = False

        self.filePicker = ft.FilePicker(on_result=self.uploadLogo)
        self.page.overlay.append(self.filePicker)
        self.fileUploadButton = ft.TextButton(content=ft.Text("Upload",
                                                              size=20),
                                                    style=ft.ButtonStyle(
                                                    color="BLACK",
                                                    bgcolor="#45D094",
                                                    overlay_color="#1E9690",
                                                ),
                                                    height=45,
                                                    width=100,
                                                    on_click=lambda _:  self.filePicker.pick_files(allow_multiple=False))

        # Account Data
        with open("assets/security_icons.txt", "r") as f:
            self.default = f.read()

        self.logo = ft.Image(src_base64=self.default,
                             width=150,
                             height=150)
        
        self.nameField = ft.TextField(label="Name",
                                      bgcolor=ft.colors.WHITE24)
        self.accountField = ft.TextField(label="Account",
                                         bgcolor=ft.colors.WHITE24)
        self.pwField = ft.TextField(label="Password",
                                    bgcolor=ft.colors.WHITE24)
        self.noteField = ft.TextField(label="Note",
                                      bgcolor=ft.colors.WHITE24,
                                      multiline=True,
                                      max_lines=8)

        # Confirms
        self.confirmReset = Confirm("Reset?", self.resetValues, self.closeReset)
        self.confirmAdd = Confirm("Add?", self.addValues, self.closeAdd)
        
        self.buttonContainer = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.IconButton(
                        icon=ft.icons.REPLAY_ROUNDED,
                        height=45,
                        width=100,
                        on_click=lambda e: page.open(self.confirmReset)
                    ),
                    ColorButton("Add", on_click=lambda e: page.open(self.confirmAdd))
                ]
            )    
        )
        
        # Page
        self.page.add(
            ft.Column(
                alignment=ft.alignment.center,
                spacing=10,
                controls=[
                    CenterCon(
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                self.logo,
                                self.fileUploadButton
                            ]  
                        ),
                        margin=ft.margin.only(top=40)
                    ),
                    self.nameField,
                    self.accountField,
                    self.pwField,
                    self.noteField,
                    self.buttonContainer
                ]
            )
        )

        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_BACK_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickClose)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_TOP

    def clickClose(self, e):
        changePage(2, self.page, self.db)
        self.page.update()
    
    def closeReset(self, e):
        self.page.close(self.confirmReset)
    
    def closeAdd(self, e):
        self.page.close(self.confirmAdd)
    
    def resetValues(self, e):
        self.logo.src_base64 = self.default
        self.nameField.value = ""
        self.accountField.value = ""
        self.pwField.value = ""
        self.noteField.value = ""
        self.closeReset(e)
        self.page.update()
    
    def addValues(self, e):
        dig = ft.AlertDialog(
            title=ft.Text("Successfully added to the Database",
                          size=22),
        )
        if self.uploaded:
            logoBase64 = self.logo.src_base64
        else:
            logoBase64 = ""
        
        name = self.nameField.value
        if name == "":
            self.closeAdd(e)
            msg = "You must have 'Name'"
        else:
            self.db.put(name=name,
                        account=self.accountField.value,
                        pw=self.pwField.value,
                        logo=logoBase64,
                        note=self.noteField.value
                        )
            msg = "Successfully added to the Database"

            self.closeAdd(e)
            changePage(2, self.page, self.db)
       
        dig.title.value = msg
        
        self.page.open(dig)
        self.page.update()
        
    def uploadLogo(self, e: ft.FilePickerResultEvent):
        if e.files != None:
            with open(e.files[0].path, "rb") as file:
                img = self.db.encodeImg(file)
            self.logo.src_base64 = img
            self.uploaded = True
            self.page.update()
            
class Account(AddAccount): # 4
    def __init__(self, page: ft.Page, db: sql.DynamoDB, data):
        super().__init__(page, db)
        self.data = data
        
        if data.get('logo') == "":
            with open("assets/security_icons.txt", "r") as f:
                self.img = f.read()
        else:
            self.img = data.get('logo')
            
        self.logo.src_base64 = self.img
        self.nameField.value = data.get('name')
        self.accountField.value = data.get('account')
        self.pwField.value = data.get('pw')
        self.noteField.value = data.get('note')
        
        self.buttonContainer.content=ft.Row(
            controls=[
                
            ]
        )
        
class Setting: # 5
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.page = page
        self.db = db
        self.page.add(ft.SafeArea(ft.Text("Setting")))

class ChangePW: # 6
    def __init__(self, page: ft.Page, db: sql.DynamoDB):
        self.page = page
        self.db = db
        self.page.add(ft.SafeArea(ft.Text("ChangePW")))

def main(page: ft.Page):
    page.title = "Account Manager 2"
    page.window.icon = "assets/security_icons.png"
    page.adaptive = True

    width = 400
    page.window.width = width
    page.window.height = width*16/9
    
    # get admin pw
    db = sql.DynamoDB()
    adminPW = db.get(id=0)['pw']
    
    # if no pw, set up
    if adminPW == "":
        app = PWsetUp(page,db)
    else:
        # app = PW(page,db)
        app = Main(page, db)
    
ft.app(main)
