import flet as ft
import sql

with open("assets/security_icons.png", "rb") as img:
    a = sql.DynamoDB()
    b = a.encodeImg(img)
    with open("assets/security_icons.txt", "w") as t:
        t.write(b)