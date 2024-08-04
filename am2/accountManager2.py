import flet as ft
import sql
import AES
from decimal import Decimal
import sqlite3
import base64

# SQLite file path
localDB = 'assets/accounts.db'
secretMode = False


def changePage(pageNum: int, page: ft.Page, adminPW: str, db: sql.DynamoDB, data={}):
    # Need Update after this function
    page.controls.clear()
    page.floating_action_button = None

    match pageNum:
        case 0:
            return PW(page, adminPW, db)
        case 1:
            return PWsetUp(page, adminPW, db)
        case 2:
            return Main(page, adminPW, db)
        case 3:
            return AddAccount(page, adminPW, db)
        case 4:
            if len(data) == 0:
                return
            return Account(page, adminPW, db, data)
        case 5:
            return Setting(page, adminPW, db)
        case 6:
            return ChangePW(page, adminPW, db)
        case 7:
            return About(page, adminPW, db)


def loadAccountsFromLocal() -> list:
    """load my accounts from SQLite"""
    conn = sqlite3.connect(localDB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            title TEXT,
            account TEXT,
            pw TEXT,
            logo BLOB,
            note TEXT
        )
    ''')

    cursor.execute('SELECT id, title, account, pw, logo, note FROM accounts')
    rows = cursor.fetchall()
    accounts = []
    for row in rows:
        account = {
            'id': row[0],
            'title': row[1],
            'account': row[2],
            'pw': row[3],
            'logo': base64.b64encode(row[4]).decode('utf-8') if row[4] else "",
            'note': row[5]
        }
        accounts.append(account)

    conn.close()

    return accounts


def addAccountToLocal(acc: dict):
    global localDB
    """add an account to the local database. Should contain id, title, account, pw, logo, note"""
    conn = sqlite3.connect(localDB)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO accounts (id, title, account, PW, logo, note) VALUES (?, ?, ?, ?, ?, ?)
    ''', (acc['id'],
          acc['title'],
          acc['account'],
          acc['pw'],
          acc['logo'],
          acc['note']))

    conn.commit()
    conn.close()


def deleteAccountFromLocal(id: int):
    """Delete an account from the local database with id."""
    global localDB
    conn = sqlite3.connect(localDB)
    cursor = conn.cursor()

    # Delete account by ID
    cursor.execute('''
        DELETE FROM accounts WHERE id = ?
    ''', (id,))

    conn.commit()
    conn.close()


def editAccountFromLocal(acc: list):
    """Edit Account. Assume acc = [id, title, account, pw, logo, note]"""
    global localDB

    id, title, account, pw, logo, note = acc

    # Connect to the SQLite database
    conn = sqlite3.connect(localDB)
    cursor = conn.cursor()
    # Update account information
    cursor.execute('''
        UPDATE accounts
        SET title = ?, account = ?, PW = ?, logo = ?, note = ?
        WHERE id = ?
    ''', (title, account, pw, logo, note, id))

    conn.commit()
    conn.close()


def syncAccountToLocal(accs: list):
    """Sync Account from DynamoDB to SQLite"""
    conn = sqlite3.connect(localDB)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY,
            title TEXT,
            account TEXT,
            pw TEXT,
            logo BLOB,
            note TEXT
        )
    ''')

    # Insert items into SQLite table
    for acc in accs:
        cursor.execute('''
            INSERT OR REPLACE INTO accounts (id, title, account, PW, logo, note) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            int(acc['id']),
            acc['title'],
            acc['account'],
            acc['pw'],
            sql.DynamoDB.decodeImg(acc['logo']),
            acc['note']
        ))

    conn.commit()
    conn.close()


# Load Accounts from DynamoDB
accounts = loadAccountsFromLocal()

# Custom Flet Objects


class CenterCon(ft.Container):
    """Aligned center container"""

    def __init__(self, content, margin=0):
        super().__init__()
        self.content = content
        self.margin = margin
        self.alignment = ft.alignment.center


class AccountBtn(ft.TextButton):
    def __init__(self, id, text, on_click, data, **kwargs):
        super().__init__(kwargs)
        self.id = id

        img_base64 = data['logo']
        if img_base64 == "":
            with open("assets/security_icons.txt", "r") as f:
                img_base64 = f.read()

        logoSize = 65
        self.logo = ft.Image(src_base64=img_base64,
                             width=logoSize,
                             height=logoSize)

        self.content = ft.Row(
            controls=[
                self.logo,
                ft.Text(text,
                        size=18)
            ])

        self.style = ft.ButtonStyle(
            color="BLACK",
            bgcolor="#45D094",
            overlay_color="#1E9690",
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self.width = 300
        self.height = 120
        self.data = data
        self.on_click = on_click
        self.on_click = lambda e: on_click(e, self.data)


class Confirm(ft.AlertDialog):
    def __init__(self, content: str, onYes, onNo, **kwargs):
        super().__init__(modal=True,
                         title=ft.Text("Please confirm"),
                         content=ft.Text(f"{content}"),
                         actions=[
                             ft.TextButton("Yes", on_click=onYes),
                             ft.TextButton("No", on_click=onNo),
                         ],
                         actions_alignment=ft.MainAxisAlignment.END)


class ColorButton(ft.TextButton):
    def __init__(self, text: str, on_click=None, height=45, width=100, data=None):
        self.text_widget = ft.Text(f"{text}", size=20)
        super().__init__(content=self.text_widget,
                         style=ft.ButtonStyle(
                             color="BLACK",
                             bgcolor="#45D094",
                             overlay_color="#1E9690"),
                         height=height,
                         width=width,
                         on_click=on_click,
                         data=data)

    def set_text(self, newText: str):
        self.text_widget.value = newText
        self.update()

# Pages


class PW:  # 0
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # encrypted before submit
        self.db = db

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
                spacing=15,
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
                        ft.ElevatedButton(content=ft.Text(value="Enter", size=20),
                                          color="BLACK",
                                          bgcolor="#45D094",
                                          style=ft.ButtonStyle(
                                              overlay_color="#1E9690",
                        ),
                            height=50,
                            width=150,
                            on_click=self.enter),
                    )
                ]
            )
        )

    def enter(self, e):
        pw = self.pw_field.value

        if AES.verifyPW(self.adminPW, pw):
            self.adminPW = AES.decryptPW(self.adminPW, pw)
            # Go to Main
            changePage(2, self.page, self.adminPW, self.db,)
            self.page.update()
        else:
            # open dialog
            dlg = ft.AlertDialog(title=ft.Text("Wrong Password",
                                               size=20,
                                               text_align="center"))
            self.pw_field.value = ""
            self.page.open(dlg)
            self.page.update()


class PWsetUp:  # 1
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # = "" before submit
        self.db = db

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
            pw = AES.encryptData(pw)
            self.adminPW = pw

            # update admin password
            self.db.update(0, title="admin", account="user", pw=pw)

            alertMsg = "Password Created"

        # open dialog
        dlg = ft.AlertDialog(title=ft.Text(
            alertMsg, size=20, text_align="center"))
        self.page.open(dlg)

        # Go to PW
        if valid:
            changePage(0, self.page, self.adminPW, self.db)
            self.page.update()


class Main:  # 2
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # decrypted
        self.db = db

        self.accounts = accounts
        self.accountsSubset = accounts

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
            width=w,
            height=h,
            content=self.AccountButtons
        )

        # Page
        self.page.add(
            ft.Column(
                controls=[
                    # Top Bar
                    ft.Container(
                        margin=ft.margin.only(top=topMargin),
                        content=ft.Row(
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
        """update controls of AccountButtons ft.Column"""
        global secretMode

        match secretMode:
            case False:
                self.AccountButtons.controls = [AccountBtn(id=account.get('id'),
                                                text=account.get('title')+'\n'+account.get('account')+'\n'+
                                                AES.decryptPW(account.get('pw'), self.adminPW),
                    on_click=self.clickAccount,
                    data=account)
                    for account in self.accountsSubset]
            case True:
                self.AccountButtons.controls = [AccountBtn(id=account.get('id'),
                                                text=account.get('title')+'\n'+account.get('account')+'\n'+
                                                "**********",
                    on_click=self.clickAccount,
                    data=account)
                    for account in self.accountsSubset]

    def clickSettings(self, e):
        changePage(5, self.page, self.adminPW, self.db)
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
            self.accountsSubset = [
                d for d in self.accounts if val.lower() in d.get('title').lower()]
        self.sortOrder(e)

    def sortOrder(self, e):
        if self.sortButton.data == "UP":
            self.accountsSubset = sorted(
                self.accountsSubset, key=lambda x: x['title'].lower())
        else:
            self.accountsSubset = sorted(
                self.accountsSubset, key=lambda x: x['title'].lower(), reverse=True)

        self.updateAccountButtons()
        self.page.update()

    def clickAccount(self, e, data):
        changePage(4, self.page, self.adminPW, self.db, data)
        self.page.update()

    def clickAdd(self, e):
        changePage(3, self.page, self.adminPW, self.db)
        self.page.update()


class AddAccount:  # 3
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # decrypted
        self.db = db
        self.uploaded = False
        self.backPressed = False

        self.dig = ft.AlertDialog(
            title=ft.Text("",
                          size=22),
        )

        self.filePicker = ft.FilePicker(on_result=self.uploadLogo)
        self.page.overlay.append(self.filePicker)
        self.fileUploadButton = ft.TextButton(
            content=ft.Text("Upload", size=20),
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

        self.titleField = ft.TextField(label="Title",
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
        self.confirmReset = Confirm(
            "Reset?", self.resetValues, self.closeReset)
        self.confirmAdd = Confirm("Add?", self.addValues, self.closeAdd)

        self.buttonContainer = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.icons.REPLAY_ROUNDED,
                        height=45,
                        width=100,
                        on_click=lambda e: page.open(self.confirmReset)
                    ),
                    ColorButton(
                        "Add", on_click=lambda e: page.open(self.confirmAdd))
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
                    self.titleField,
                    self.accountField,
                    self.pwField,
                    self.noteField,
                    self.buttonContainer
                ]
            )
        )

        # Back Button
        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_BACK_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickClose)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_TOP

    def clickClose(self, e):
        if not self.backPressed:
            self.backPressed = True
            changePage(2, self.page, self.adminPW, self.db)
            self.page.update()

    def closeReset(self, e):
        self.page.close(self.confirmReset)

    def closeAdd(self, e):
        self.page.close(self.confirmAdd)

    def resetValues(self, e):
        self.logo.src_base64 = self.default
        self.uploaded = False
        self.titleField.value = ""
        self.accountField.value = ""
        self.pwField.value = ""
        self.noteField.value = ""
        self.closeReset(e)
        self.page.update()

    def addValues(self, e):
        if self.uploaded:
            logoBase64 = self.logo.src_base64
        else:
            logoBase64 = ""

        title = self.titleField.value
        if title == "":
            self.closeAdd(e)
            msg = "You must have 'title'"
        else:
            pw = AES.encryptData(self.adminPW, self.pwField.value)

            newAccount = {}
            newAccount['id'] = self.db.maxID() + 1
            newAccount['title'] = title
            newAccount['account'] = self.accountField.value
            newAccount['pw'] = pw
            # newAccount['logo'] = logoBase64
            newAccount['logo'] = base64.b64decode(logoBase64)
            newAccount['note'] = self.noteField.value

            # add new account to local DB
            addAccountToLocal(newAccount)

            # add new account to DB
            self.db.put(title=title,
                        account=self.accountField.value,
                        pw=pw,
                        logo=logoBase64,
                        note=self.noteField.value
                        )

            msg = "Successfully added to the Database"

            self.closeAdd(e)
            # reload accounts
            global accounts
            accounts = loadAccountsFromLocal()
            changePage(2, self.page, self.adminPW, self.db)

        self.dig.title.value = msg
        self.page.open(self.dig)

        self.page.update()

    def uploadLogo(self, e: ft.FilePickerResultEvent):
        if e.files != None:
            with open(e.files[0].path, "rb") as file:
                img = sql.DynamoDB.encodeImg(file)
            self.logo.src_base64 = img
            self.uploaded = True
            self.page.update()


class Account(AddAccount):  # 4
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB, data):
        super().__init__(page, adminPW, db)
        self.data = data

        if data.get('logo') == "":
            with open("assets/security_icons.txt", "r") as f:
                self.img = f.read()
        else:
            self.img = data.get('logo')

        self.logo.src_base64 = self.img
        self.titleField.value = data.get('title')
        self.accountField.value = data.get('account')
        self.pwField.value = AES.decryptPW(data.get('pw'), self.adminPW)
        self.noteField.value = data.get('note')

        self.confirmDelete = Confirm(
            "Delete?", self.deleteValues, self.closeDelete)
        self.confirmSave = Confirm("Save?", self.saveValues, self.closeSave)

        self.buttonContainer.content = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ColorButton("Delete",
                            on_click=lambda e: page.open(self.confirmDelete)),
                ft.IconButton(
                    icon=ft.icons.REPLAY_ROUNDED,
                    height=45,
                    width=100,
                    on_click=lambda e: page.open(self.confirmReset)
                ),
                ColorButton("Save",
                            on_click=lambda e: page.open(self.confirmSave))
            ]
        )

    def resetValues(self, e):
        self.logo.src_base64 = self.img
        self.uploaded = False
        self.titleField.value = self.data.get('title')
        self.accountField.value = self.data.get('account')
        self.pwField.value = self.data.get('pw')
        self.noteField.value = self.data.get('note')
        self.closeReset(e)
        self.page.update()

    def deleteValues(self, e):
        # delete from local DB
        deleteAccountFromLocal(self.data.get('id'))

        # delete from DB
        self.db.delete(Decimal(str(self.data.get('id'))))
        self.closeDelete(e)

        # open dialog
        msg = "Successfully deleted from the Database"
        self.dig.title.value = msg
        self.page.open(self.dig)

        # reload accounts
        global accounts
        accounts = loadAccountsFromLocal()
        changePage(2, self.page, self.adminPW, self.db)
        self.page.update()

    def saveValues(self, e):
        if self.uploaded:
            logoBase64 = self.logo.src_base64
        else:
            logoBase64 = ""

        title = self.titleField.value
        if title == "":
            self.closeSave(e)
            msg = "You must have 'title'"
        else:
            encryptedPW = AES.encryptData(self.adminPW, self.pwField.value)

            # Edit local DB
            editedAccount = []  # item order = [id, title, account, pw, logo, note]
            editedAccount.append(self.data.get('id'))
            editedAccount.append(title)
            editedAccount.append(self.accountField.value)
            editedAccount.append(encryptedPW)
            editedAccount.append(logoBase64)
            editedAccount.append(self.noteField.value)

            editAccountFromLocal(editedAccount)

            # Edit DB
            self.db.update(self.data.get('id'),
                           title=title,
                           account=self.accountField.value,
                           pw=encryptedPW,
                           logo=logoBase64,
                           note=self.noteField.value)
            msg = "Successfully saved to the Database"

            self.closeSave(e)
            global accounts
            accounts = loadAccountsFromLocal()
            changePage(2, self.page, self.adminPW, self.db)

        # dialog
        self.dig.title.value = msg
        self.page.open(self.dig)

        self.page.update()

    def closeDelete(self, e):
        self.page.close(self.confirmDelete)

    def closeSave(self, e):
        self.page.close(self.confirmSave)


class Setting:  # 5
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # decrypted
        self.db = db
        self.backPressed = False

        # width and height for buttons
        width = 200
        height = 80

        self.secretButton = ColorButton(
            text="Secret Mode: Off",
            width=width,
            height=height,
            on_click=self.clickSecret, data=False)

        self.page.add(
            ft.Container(
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[CenterCon(
                        ft.Text("Settings",
                                size=30),
                        margin=ft.margin.only(top=40)),
                        CenterCon(
                        ColorButton(
                            text="Sync",
                            width=width,
                            height=height,
                            on_click=self.clickSync)),
                        CenterCon(
                        self.secretButton
                    ),
                        CenterCon(
                        ColorButton(
                            text="Change PW",
                            width=width,
                            height=height,
                            on_click=self.clickChangePW)),
                        CenterCon(
                        ColorButton(
                            text="About",
                            width=width,
                            height=height,
                            on_click=self.clickAbout)),
                        CenterCon(
                        ColorButton(
                            text="GitHub Link",
                            width=width,
                            height=height,
                            on_click=self.clickGitHub)),
                    ]
                )
            )
        )

        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_BACK_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickClose)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_TOP
        self.page.update()

    def clickClose(self, e):
        if not self.backPressed:
            self.backPressed = True
            changePage(2, self.page, self.adminPW, self.db)
            self.page.update()

    def clickSync(self, e):
        loadedAccount = self.db.getAll()
        syncAccountToLocal(loadedAccount)
        global accounts
        accounts = loadAccountsFromLocal()

    def clickSecret(self, e):
        global secretMode

        toggle = secretMode
        match toggle:
            case False:
                # on
                self.secretButton.data = 1
                self.secretButton.set_text('Secret Mode: On')
                secretMode = True
            case True:
                # off
                self.secretButton.data = 0
                self.secretButton.set_text('Secret Mode: Off')
                secretMode = False

    def clickChangePW(self, e):
        changePage(6, self.page, self.adminPW, self.db)
        self.page.update()

    def clickAbout(self, e):
        changePage(7, self.page, self.adminPW, self.db)
        self.page.update()

    def clickGitHub(self, e):
        self.page.launch_url("https://github.com/CA-JunPark/AccountManger2")


class ChangePW:  # 6
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW  # decrypted
        self.db = db

        with open("assets/security_icons.txt", "r") as f:
            img = f.read()

        self.currentPW = ft.TextField(bgcolor="WHITE24",
                                      autofocus=True,
                                      password=True,
                                      multiline=False,
                                      text_align=ft.TextAlign.CENTER,
                                      label="Current PW"
                                      )

        self.newPW = ft.TextField(bgcolor="WHITE24",
                                  password=True,
                                  multiline=False,
                                  text_align=ft.TextAlign.CENTER,
                                  label="New PW"
                                  )

        self.confirmNewPW = ft.TextField(bgcolor="WHITE24",
                                         password=True,
                                         multiline=False,
                                         text_align=ft.TextAlign.CENTER,
                                         label="Confirm New PW",
                                         on_submit=self.enter
                                         )

        self.page.add(
            ft.Column(
                spacing=15,
                controls=[CenterCon(
                    ft.Image(src_base64=img,
                             width=180),
                    margin=ft.margin.only(top=40)),
                    self.currentPW,
                    self.newPW,
                    self.confirmNewPW,
                    CenterCon(
                    ft.ElevatedButton(content=ft.Text(value="Change", size=20),
                                      color="BLACK",
                                      bgcolor="#45D094",
                                      style=ft.ButtonStyle(
                        overlay_color="#1E9690",

                    ),
                        height=50,
                        width=150,
                        on_click=self.enter),
                )
                ]
            )
        )

        self.dlg = ft.AlertDialog(title=ft.Text("Wrong Current Password",
                                                size=20,
                                                text_align="center"))

        self.confirmChange = Confirm(
            "Change Password?", onYes=self.yesChangePW, onNo=self.noChangePW)

        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_BACK_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickClose)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_TOP
        self.page.update()

    def yesChangePW(self, e):
        try:
            encryptedNewAdminPW = AES.encryptData(self.newPW.value)
        except:
            print("Admin PW Encrypt Failed")

        # Update all passwords of accounts
        count = self.db.count()

        for id in range(1, count):
            # hash to string
            pwString = AES.decryptPW(self.db.get(id=id)['pw'], self.adminPW)
            # string to newHash
            newPW = AES.encryptData(self.newPW.value, pwString)
            # update
            self.db.update(id, pw=newPW)

        self.db.update(targetID=0, pw=encryptedNewAdminPW)
        self.adminPW = encryptedNewAdminPW

        self.dlg.title = ft.Text("Password Changed\nPlease Login Again",
                                 size=20,
                                 text_align="center")
        self.page.close(self.confirmChange)

        self.page.open(self.dlg)

        changePage(0, self.page, self.adminPW, self.db)
        self.page.update()

    def noChangePW(self, e):
        self.page.close(self.confirmChange)

    def clickClose(self, e):
        changePage(5, self.page, self.adminPW, self.db)
        self.page.update()

    def enter(self, e):
        # check currentPW
        current = self.currentPW.value
        pw = self.db.get(id=0)['pw']
        if not AES.verifyPW(pw, current):
            self.dlg.title = ft.Text("Wrong Current Password",
                                     size=20,
                                     text_align="center")
            self.page.open(self.dlg)
        else:
            # Check new passwords match
            new = self.newPW.value
            newC = self.confirmNewPW.value
            if new == "":
                self.dlg.title = ft.Text("Cannot Set Empty Password",
                                         size=20,
                                         text_align="center")
                self.page.open(self.dlg)
            if new != newC:
                self.dlg.title = ft.Text("New Passwords Does Not Match",
                                         size=20,
                                         text_align="center")
                self.page.open(self.dlg)
            else:
                # Update Admin PW
                self.page.open(self.confirmChange)


class About:  # 7
    def __init__(self, page: ft.Page, adminPW: str, db: sql.DynamoDB):
        self.page = page
        self.adminPW = adminPW
        self.db = db
        self.page.add(ft.SafeArea(ft.Text(
            """App name: Account Manager 2 
Version: 1.0.0
Developed by: Jun Park
Email: cskoko5786@gmail.com

Third Party Libraries:
    Flet
    Boto3
    PassLib

Images:
    security icons
        < a href="https://www.flaticon.com/free-icons/security" title="security icons" > Security icons created by Freepik - Flaticon < /a >
    settings
        < link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" / >
    search
        < link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" / >
    JP
        'This logo was generated using OpenAI's DALL-E. © 2024 OpenAI. All rights reserved.'""")))

        self.page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_BACK_ROUNDED,
                                                                   bgcolor="#1E9690",
                                                                   focus_color="#45D094",
                                                                   on_click=self.clickClose)
        self.page.floating_action_button_location = ft.FloatingActionButtonLocation.END_TOP
        self.page.update()

    def clickClose(self, e):
        changePage(5, self.page, self.adminPW, self.db)
        self.page.update()


def main(page: ft.Page):
    page.title = "Account Manager 2"
    page.adaptive = True

    width = 400
    height = width*16/9

    page.window.icon = "assets/security_icons.png"
    page.window.width = width
    page.window.height = height
    page.window.min_width = width
    page.window.min_height = height
    page.window.max_width = width
    page.window.mmx_height = height

    # get admin pw
    db = sql.DynamoDB()
    adminPW = db.get(id=0)['pw']

    # if no pw, set up
    if adminPW == "":
        app = PWsetUp(page, adminPW, db)
    else:
        app = PW(page, adminPW, db)
