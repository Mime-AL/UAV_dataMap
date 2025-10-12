import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import ctypes
from PIL import Image, ImageTk
import pillow_avif
import sqlite3
import json
import os
import hashlib
import pathlib
import pyproj
import base64
import io
from offline_folium import offline
import folium
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")    
    return os.path.join(base_path, relative_path)

def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        return None

def pathButton():
    global dataPath
    dataPath = filedialog.askdirectory()
    if dataPath == "":
        return
    else:
        entry1.delete(0, tk.END)
        entry1.insert(0, dataPath)

def saveButton():
    global dataPath
    global APIKey
    dataPath = entry1.get()
    APIKey = entry2.get()
    config = {
        "setings": {
            "datapath": dataPath,
            "APIKey": APIKey
        }
    }
    with open(configPath, "w") as f:
        json.dump(config, f)
    messagebox.showinfo("提示", "保存成功")

def StartLeafletMap():
    global APIKey
    map = folium.Map(location=[26.0, 119.0], zoom_start=5, tiles=None)
    #设置图例
    icon_map = {
        0: get_base64_encoded_image(resource_path(r"./data/tip-green.png")),
        1: get_base64_encoded_image(resource_path(r"./data/tip-blue.png")),
        2: get_base64_encoded_image(resource_path(r"./data/tip-red.png")),
        3: get_base64_encoded_image(resource_path(r"./data/tip-violet.png")),
    }
    default_icon = get_base64_encoded_image(resource_path(r"./data/tip-black.png"))
    #添加底图
    folium.TileLayer(
        tiles=f"https://{{s}}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={APIKey}",
        attr='天地图',
        name='天地图-矢量',
        subdomains=['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'],
        overlay=False,
        control=True
    ).add_to(map)
    folium.TileLayer(
        tiles=f"https://{{s}}.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={APIKey}",
        attr='天地图',
        name='天地图-影像',
        subdomains=['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'],
        overlay=False,
        control=True
    ).add_to(map)
    # 添加矢量注记叠加层
    folium.TileLayer(
        tiles=f"https://{{s}}.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&tk={APIKey}",
        attr='天地图注记',
        name='天地图-注记',
        subdomains=['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'],
        overlay=True,
        control=True,
        show=True
    ).add_to(map)
    folium.LayerControl().add_to(map)
    #从数据库中读取数据
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datamap WHERE AVAIABLE = 1;")
    results = cursor.fetchall()
    for row in results:
        path = row[1]
        img = row[2]
        type = row[3]
        base = row[4]
        remark = row[5]
        x = row[10]
        y = row[11]
        safe_path = path.replace('\\', '/')
        popup_text = f"文件路径: {safe_path}<br>平台类型: {base}<br>文件类型: {type}<br>备注: {remark}"
        if img and os.path.exists(img):
            encoded = base64.b64encode(open(img, 'rb').read()).decode()
            img_html = f'<img src="data:image/png;base64,{encoded}" width="200"><br>'
            popup_text = img_html + popup_text
        popup = folium.Popup(popup_text, max_width=300)
        icon_b64_str = icon_map.get(type, default_icon)
        if icon_b64_str:
            icon_url = f"data:image/png;base64,{icon_b64_str}"
            icon = folium.CustomIcon(icon_url, icon_size=(30, 30))
        else:
            # 如果图标文件找不到，使用folium默认图标作为后备
            icon = folium.Icon(color="blue")
        marker = folium.Marker(location=[y, x], popup=popup, icon=icon)
        marker.add_to(map)
    conn.close()
    #保存为HTML文件
    mapPath = "./user/map.html"
    map.save(mapPath)
    #使用默认浏览器打开HTML文件
    path = os.path.abspath(mapPath)
    os.startfile(path)
    startPage.destroy()

def mapButtonWithoutUpdate():
    global APIKey
    APIKey = entry2.get()
    StartLeafletMap()

def mapButtonWithUpdate():
    global APIKey
    APIKey = entry2.get()
    #设置数据库中的数据为不可用
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("UPDATE datamap SET AVAIABLE = 0;")
    conn.commit()
    #遍历数据路径文件夹
    global dataPath
    if dataPath == "":
        messagebox.showinfo("提示", "数据路径不能为空")
        return
    if not os.path.exists(dataPath):
        messagebox.showinfo("提示", "数据路径不存在")
        return
    Path = pathlib.Path(dataPath)
    fileList = list(Path.rglob('*'))
    progressWin = tk.Toplevel(startPage)
    progressWin.title("数据处理进度")
    progressWin.geometry("420x80")
    progressWin.resizable(False, False)
    progress = ttk.Progressbar(progressWin, orient=tk.HORIZONTAL, length=400, mode='determinate')
    progress.pack(padx=10, pady=20)
    progress['maximum'] = len(fileList)
    for filePath in fileList:
        #检查文件是否是json
        if filePath.suffix != ".json":
            progress['value'] += 1
            progressWin.update_idletasks()
            continue
        # 处理json文件
        with open(filePath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                progress['value'] += 1
                progressWin.update_idletasks()
                continue
            try:
                data = json.loads(content)
            except Exception as e:
                progress['value'] += 1
                progressWin.update_idletasks()
                continue
            try:
                #检查是否含有Tag字段，内容为MapVisibleJson
                if "Tag" not in data or data["Tag"] != "MapVisibleJson":
                    progress['value'] += 1
                    progressWin.update_idletasks()
                    continue
                #计算文件的SHA256，SHAKE256和Blake2b值
                sha256 = hashlib.sha256()
                shake256 = hashlib.shake_256()
                blake2b = hashlib.blake2b()
                with open(filePath, "rb") as f2:
                    while True:
                        data2 = f2.read(65536)
                        if not data2:
                            break
                        sha256.update(data2)
                        shake256.update(data2)
                        blake2b.update(data2)
                hash1 = sha256.hexdigest()
                hash2 = shake256.hexdigest(32)
                hash3 = blake2b.hexdigest()
                #检查数据库中是否存在相同的HASH值
                cursor.execute("SELECT * FROM datamap WHERE HASH1 = ? OR HASH2 = ? OR HASH3 = ?", (hash1, hash2, hash3))
                result = cursor.fetchone()
                if result:
                    #如果存在相同的HASH值，则将数据库中的数据标记为可用，并更新文件路径
                    cursor.execute("UPDATE datamap SET AVAIABLE = 1, PATH = ? WHERE HASH1 = ? OR HASH2 = ? OR HASH3 = ?", (str(filePath.parent), hash1, hash2, hash3))
                else:
                    #如果不存在相同的HASH值，则将数据插入数据库
                    #使用JSON的WTK,X,Y字段对数据进行重投影到WSG84经纬度
                    try:
                        wtk = data["WTK"]
                        x = data["X"]
                        y = data["Y"]
                        proj = pyproj.Proj(wtk)
                        lon, lat = proj(x, y, inverse=True)
                    except Exception as e:
                        messagebox.showinfo("提示", f"坐标转换失败: {e}")
                        continue
                    #Thumbnail中存在图片数据，保存为PNG格式
                    imgPath = None
                    if "Thumbnail" in data and data["Thumbnail"] != "":
                        try:
                            imgData = data["Thumbnail"]
                            imgData = imgData.split(",")[-1]
                            imgData = bytes(imgData, encoding="utf-8")
                            imgData = base64.b64decode(imgData)
                            img = Image.open(io.BytesIO(imgData))
                            img = img.convert("RGB")
                            imgPath = os.path.join(thumbPath, f"{hash1}.png")
                            img.save(imgPath, format="PNG")
                        except Exception as e:
                            imgPath = None
                    #读取FileType、BaseType和Remark字段
                    try:
                        fileType = int(data["FileType"])
                    except:
                        fileType = 0
                        messagebox.showinfo("提示", f"文件类型错误")
                        continue
                    try:
                        baseType = data["BaseType"]
                    except:
                        baseType = ""
                        messagebox.showinfo("提示", f"平台类型错误")
                        continue
                    try:
                        remark = data["Remark"]
                    except:
                        remark = ""
                    #插入数据
                    cursor.execute("INSERT INTO datamap (PATH, IMG, TYPE, BASE, REMARK, HASH1, HASH2, HASH3, AVAIABLE, X, Y) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)", (str(filePath.parent), imgPath, fileType, baseType, remark, hash1, hash2, hash3, lon, lat))
                conn.commit()
            except Exception as e:
                messagebox.showinfo("提示", f"处理文件{filePath}失败: {e}")
                continue
        progress['value'] += 1
        progressWin.update_idletasks()
    conn.close()
    progressWin.update_idletasks()
    messagebox.showinfo("提示", "数据更新完成")
    StartLeafletMap()


if __name__ == "__main__":
    #配置TK
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    startPage = tk.Tk()
    try:#加载图标
        iconImage = Image.open(resource_path("./data/map-f.png"))
        iconPhoto = ImageTk.PhotoImage(iconImage)
        startPage.wm_iconphoto(True, iconPhoto)
    except Exception as e:
        messagebox.showinfo("提示", f"图标加载失败: {e}")
    startPage.tk.call('tk', 'scaling', ScaleFactor/75)
    startPage.title("可视化工具参数")
    startPage.geometry("600x300")
    startPage.resizable(False, False)

    #创建用户文件夹
    userPath = resource_path("./user")
    if not os.path.exists(userPath):
        try:
            os.mkdir(userPath)
        except Exception as e:
            messagebox.showinfo("提示", f"创建用户文件夹失败: {e}")
            startPage.destroy()
            exit()
        messagebox.showinfo("提示", "创建用户文件夹成功")

    #创建缩略图文件夹
    thumbPath = resource_path("./thumb")
    if not os.path.exists(thumbPath):
        try:
            os.mkdir(thumbPath)
        except Exception as e:
            messagebox.showinfo("提示", f"创建缩略图文件夹失败: {e}")
            startPage.destroy()
            exit()
        messagebox.showinfo("提示", "创建缩略图文件夹成功")

    #检查数据库
    dbPath = resource_path("./user/map.db")
    if not os.path.exists(dbPath):
        messagebox.showinfo("提示", "数据库文件不存在,创建新的数据库文件")
        try:
            conn = sqlite3.connect(dbPath)
            conn.execute('''CREATE TABLE datamap
                    (id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    PATH    TEXT            NOT NULL,
                    IMG    TEXT,
                    TYPE   INT             NOT NULL,
                    BASE   TEXT            NOT NULL,
                    REMARK TEXT,
                    HASH1  TEXT            NOT NULL,
                    HASH2  TEXT            NOT NULL,
                    HASH3  TEXT            NOT NULL,
                    AVAIABLE BOOLEAN        NOT NULL,
                    X      FLOAT(8)        NOT NULL,
                    Y      FLOAT(8)        NOT NULL);''')
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showinfo("提示", f"创建数据库文件失败: {e}")
            startPage.destroy()
            exit()
    else:
        conn = sqlite3.connect(dbPath)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='datamap';")
        exitTable = cursor.fetchone() is not None
        if not exitTable:
            messagebox.showinfo("提示", "数据库文件存在,但表不存在,创建新的表")
            conn.execute('''CREATE TABLE datamap
                    (id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    PATH    TEXT            NOT NULL,
                    IMG    TEXT,
                    TYPE   INT             NOT NULL,
                    BASE   TEXT            NOT NULL,
                    REMARK TEXT,
                    HASH1  TEXT            NOT NULL,
                    HASH2  TEXT            NOT NULL,
                    HASH3  TEXT            NOT NULL,
                    AVAIABLE BOOLEAN        NOT NULL,
                    X      FLOAT(8)        NOT NULL,
                    Y      FLOAT(8)        NOT NULL);''')
            conn.commit()
        conn.close()

    #加载配置文件
    configPath = resource_path("./user/config.json")
    if not os.path.exists(configPath):
        messagebox.showinfo("提示", "配置文件不存在,创建新的配置文件")
        try:
            with open(configPath, "w") as f:
                json.dump({
                    "setings": {
                        "datapath": "",
                        "APIKey": ""
                    }
                }, f)
            dataPath = ""
            APIKey = ""
        except Exception as e:
            messagebox.showinfo("提示", f"创建配置文件失败: {e}")
            startPage.destroy()
            exit()
    else:
        with open(configPath, "r") as f:
            try:
                config = json.load(f)
                dataPath = config["setings"]["datapath"]
                APIKey = config["setings"]["APIKey"]
            except Exception as e:
                messagebox.showinfo("提示", f"配置文件加载失败: {e}")
                with open(configPath, "w") as f:
                    json.dump({
                    "setings": {
                        "datapath": "",
                        "APIKey": ""
                        }
                    }, f)
                dataPath = ""
                APIKey = ""

    framel1 = tk.LabelFrame(startPage)
    framel2 = tk.LabelFrame(startPage)
    framel3 = tk.LabelFrame(startPage, bd = 0)
    lable1 = tk.Label(framel1, text="数据路径", width = 7, height = 2)
    lable2 = tk.Label(framel2, text="API Key", width = 7, height = 2)
    lable3 = tk.Label(framel3, text="", width = 7, height = 2)
    entry1 = tk.Entry(framel1, textvariable=dataPath,width =34)
    entry2 = tk.Entry(framel2, textvariable=APIKey,width = 39)
    button1 = tk.Button(framel1, text="选择", command=pathButton)
    button2 = tk.Button(framel3, text="保存", command=saveButton, width = 7)
    button3 = tk.Button(framel3, text="不更新数据启动", command=mapButtonWithoutUpdate, width = 14)
    button4 = tk.Button(framel3, text="更新数据启动", command=mapButtonWithUpdate, width = 14)
    lable4 = tk.Label(startPage, text="API Key使用天地图API")

    entry1.insert(0, dataPath)
    entry2.insert(0, APIKey)

    framel1.grid(row=0, column=0, padx=10, pady=10)
    framel2.grid(row=1, column=0, padx=10, pady=10)
    lable4.grid(row=2, column=0)
    framel3.grid(row=3, column=0, padx=10, pady=10)
    lable1.grid(row=0, column=0)
    lable2.grid(row=0, column=0)
    entry1.grid(row=0, column=1)
    entry2.grid(row=0, column=1)
    button1.grid(row=0, column=2)
    button2.grid(row=0, column=0)
    lable3.grid(row=0, column=1)
    button3.grid(row=0, column=2)
    button4.grid(row=0, column=3)

    startPage.mainloop()