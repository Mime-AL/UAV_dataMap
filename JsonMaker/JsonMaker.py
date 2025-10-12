import tkinter as tk
import ctypes
import json
import os
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import pillow_avif
from pyproj import CRS
from pyproj.enums import WktVersion
import sys
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import imageProcess
import lasProcess

def show_processing_dialog(parent, text="处理中，请稍候..."):
    dialog = tk.Toplevel(parent)
    dialog.title("提示")
    dialog.geometry("400x80")
    dialog.transient(parent)
    dialog.grab_set()
    tk.Label(dialog, text=text).pack(expand=True, fill="both", padx=20, pady=20)
    parent.update()
    return dialog

def EPSG_to_WKT(epsg_code: int) -> str:
    match = re.search(r'\((\d+)\)[^()]*$', epsg_code)
    if match:
        epsg_code = int(match.group(1))
    else:
        match = re.search(r'(\d+)$', epsg_code)
        if match:
            epsg_code = int(match.group(1))
        else:
            messagebox.showinfo("提示", "无效的EPSG编码")
            return ""
    try:
        crs = CRS.from_epsg(epsg_code)
        return crs.to_wkt(WktVersion.WKT2_2019)
    except Exception as e:
        messagebox.showinfo("提示", f"EPSG转换WKT失败: {e}")
        return ""

ctypes.windll.shcore.SetProcessDpiAwareness(1)
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
MainPage = tk.Tk()
try:#加载图标
    iconImage = Image.open("./data/icon.png")
    iconPhoto = ImageTk.PhotoImage(iconImage)
    MainPage.wm_iconphoto(True, iconPhoto)
except Exception as e:
    messagebox.showinfo("提示", f"图标加载失败: {e}")
MainPage.tk.call('tk', 'scaling', ScaleFactor/75)
MainPage.title("JSON生成工具")
MainPage.geometry("1300x850")
MainPage.resizable(False, False)

#是否直接从文件生成缩略图
DirectThumbnail = tk.BooleanVar()

data = {
    "Tag": "MapVisibleJson",
    "FileType": "",
    "BaseType": "",
    "WTK": "",
    "X": 0.0,
    "Y": 0.0,
    "Remark": "",
    "Thumbnail": ""
}

def GeoTiffBottonClick():
    #选择文件
    file_path = filedialog.askopenfilename(title="选择GeoTIFF文件", filetypes=[("GeoTIFF文件", "*.tif;*.tiff")])
    if not file_path:
        return
    processing_dialog = show_processing_dialog(MainPage, "GeoTIFF处理中，请稍候...")
    imginfo = imageProcess.GeoTIFF_to_Thumbnail_and_Info(file_path, r"./cache/thumb.avif", DirectThumbnail.get())
    if not imginfo["success"]:
        processing_dialog.destroy()
        messagebox.showinfo("提示", f"GeoTIFF处理失败: {imginfo['error']}")
        return
    try:
        Projectentry.delete(0, tk.END)
        if imginfo["epsg"]:
            Projectentry.insert(0, f"EPSG({imginfo['epsg']})")
        XEntry.delete(0, tk.END)
        XEntry.insert(0, str(imginfo["x"]))
        YEntry.delete(0, tk.END)
        YEntry.insert(0, str(imginfo["y"]))
    except Exception as e:
        processing_dialog.destroy()
        messagebox.showinfo("提示", f"GeoTIFF信息填写失败: {e}")
        return
    if DirectThumbnail.get():
        try:
            with Image.open(r"./cache/thumb.avif") as img:
                img.thumbnail((600, 600))
                img = ImageTk.PhotoImage(img)
                ImageCanvas.delete("all")
                ImageCanvas.create_image(300, 300, image=img)
                ImageCanvas.image = img
        except Exception as e:
            processing_dialog.destroy()
            messagebox.showinfo("提示", f"图像加载失败: {e}")
            return
    if imginfo["Channels"] > 3:
        FileTypeVar.current(1)
    else:
        FileTypeVar.current(0)
    processing_dialog.destroy()

def LasBottonClick():
    file_path = filedialog.askopenfilename(title="选择las文件", filetypes=[("las文件", "*.las;*.laz")])
    if not file_path:
        return
    processing_dialog = show_processing_dialog(MainPage, "las处理中，请稍候...")
    data = lasProcess.lasLocation(file_path)
    if not data["success"]:
        processing_dialog.destroy()
        messagebox.showinfo("提示", f"las处理失败: {data['error']}")
        return
    try:
        Projectentry.delete(0, tk.END)
        if data["epsg"] is not None:
            if data["epsg"].to_authority() is not None:
                Projectentry.insert(0, f"{data['epsg'].to_authority()[0]}({data['epsg'].to_authority()[1]})")
            else:
                Projectentry.insert(0, data["epsg"].to_wkt(WktVersion.WKT2_2019))
        XEntry.delete(0, tk.END)
        XEntry.insert(0, str(data["x"]))
        YEntry.delete(0, tk.END)
        YEntry.insert(0, str(data["y"]))
        FileTypeVar.current(2)
    except Exception as e:
        processing_dialog.destroy()
        messagebox.showinfo("提示", f"las信息填写失败: {e}")
        return
    if DirectThumbnail.get():
        try:
            lasProcess.las_to_thumbnail(file_path, r"./cache/thumb.png", size=(600, 600), sample_points=20000)
            with Image.open(r"./cache/thumb.png") as img:
                img.save(r"./cache/thumb.avif", format="AVIF")
            with Image.open(r"./cache/thumb.avif") as img:
                img.thumbnail((600, 600))
                img = ImageTk.PhotoImage(img)
                ImageCanvas.delete("all")
                ImageCanvas.create_image(300, 300, image=img)
                ImageCanvas.image = img
        except Exception as e:
            processing_dialog.destroy()
            messagebox.showinfo("提示", f"图像加载失败: {e}")
            return
    processing_dialog.destroy()

def SaveBottonClick():
    global data
    try:
        data["FileType"] = FileTypeVar.current()
        data["BaseType"] = BaseTypeVar.get()
        data["X"] = float(XEntry.get())
        data["Y"] = float(YEntry.get())
        data["WTK"] = EPSG_to_WKT(Projectentry.get())
        data["Remark"] = RemarkEntry.get()
    except ValueError as e:
        messagebox.showinfo("提示", f"输入数据格式错误: {e}")
        return
    data["Thumbnail"] = imageProcess.Image_to_Base64(r"./cache/thumb.avif")
    if data["Thumbnail"] == "":
        messagebox.showinfo("提示", "图像转换Base64失败")
        return
    json_path = filedialog.asksaveasfilename(title="保存Json文件", defaultextension=".json", filetypes=[("Json文件", "*.json")])
    if not json_path:
        return
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    try:
        messagebox.showinfo("提示", f"保存成功: {json_path}")
    except ValueError as e:
        messagebox.showinfo("提示", f"保存失败: {e}")

def select_shot_file():
    file_path = filedialog.askopenfilename(title="选择图像文件", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.tif;*.bmp;*.avif")])
    if file_path:
        ShotEntry.delete(0, tk.END)
        ShotEntry.insert(0, file_path)

def ThumbnailBottonClick():
    shot_path = ShotEntry.get()
    if not os.path.isfile(shot_path):
        messagebox.showinfo("提示", "图像文件路径无效")
        return
    try:
        imageProcess.ImageResize(input_path=shot_path, output_path=r"./cache/thumb.avif", size=(600, 600))
    except Exception as e:
        messagebox.showinfo("提示", f"图像缩放失败: {e}")
        return
    try:
        with Image.open(r"./cache/thumb.avif") as img:
            img.thumbnail((600, 600))
            img = ImageTk.PhotoImage(img)
            ImageCanvas.delete("all")
            ImageCanvas.create_image(300, 300, image=img)
            ImageCanvas.image = img
    except Exception as e:
        messagebox.showinfo("提示", f"图像加载失败: {e}")
        return
    messagebox.showinfo("提示", "缩略图生成成功")

#左右布局
InfoLable = tk.Label(MainPage, text="图像位置为生成缩略图所用的图像，仅支持3通道uint8格式的图像文件，如需处理其他格式请使用GeoTIFF快速填写或截图\r\n请生成缩略图后保存文件")
frameD = tk.LabelFrame(MainPage)
framelL = tk.LabelFrame(frameD)
framelR = tk.LabelFrame(frameD)
frameD.grid(row=0, column=0, padx=10, pady=10)
framelL.grid(row=0, column=0, padx=10, pady=10)
framelR.grid(row=0, column=1, padx=10, pady=10)
InfoLable.grid(row=1, column=0, padx=10, pady=10)



#左侧布局
#从文件快速生成
GeoTiffBotton = tk.Button(framelL, text="从GeoTIFF快速填写", command=GeoTiffBottonClick)
LasBotton = tk.Button(framelL, text="从LAS/LAZ快速填写", command=LasBottonClick)
DirectCheck = tk.Checkbutton(framelL, text="直接从文件生成缩略图", variable=DirectThumbnail)
#生成缩略图
ThumbnailBotton = tk.Button(framelL, text="生成缩略图", command=ThumbnailBottonClick)
#保存按钮
SaveBotton = tk.Button(framelL, text="保存", command=SaveBottonClick)
#信息填写
Projectlable = tk.Label(framelL, text="投影/EPSG:")
Projectentry = ttk.Combobox(framelL, values=["WSG84(4326)", "WSG84 UTM-50N(32650)", "CGCS2000(4490)", "CGCS2000 GK-20(4498)"
                                             , "CGCS2000 GK-19(4497)", "Xian80 GK-20(2334)", "Xian80 GK-19(2333)"], state="normal")
Projectentry.current(0)
XLable = tk.Label(framelL, text="中心X/经度:")
XEntry = tk.Entry(framelL)
YLable = tk.Label(framelL, text="中心Y/纬度:")
YEntry = tk.Entry(framelL)
FileTypeLable = tk.Label(framelL, text="文件类型:")
FileTypeVar = ttk.Combobox(framelL, values=["可见光", "多光谱", "点云", "其他"], state="readonly")
FileTypeVar.current(0)
BaseTypeLable = tk.Label(framelL, text="平台类型:")
BaseTypeVar = ttk.Combobox(framelL, values=["无人机", "卫星", "地面"], state="normal")
BaseTypeVar.current(0)
ShotLable = tk.Label(framelL, text="图像位置:")
ShotEntry = tk.Entry(framelL)
ShotBrowseBtn = tk.Button(framelL, text="浏览", command=select_shot_file)
RemarkLable = tk.Label(framelL, text="备注:")
RemarkEntry = tk.Entry(framelL)

#布局
GeoTiffBotton.grid(row=0, column=0, padx=10, pady=10)
LasBotton.grid(row=0, column=1, padx=10, pady=10)
DirectCheck.grid(row=1, column=1, padx=10, pady=10)
FileTypeLable.grid(row=2, column=0, padx=10, pady=10)
FileTypeVar.grid(row=2, column=1, padx=10, pady=10)
BaseTypeLable.grid(row=3, column=0, padx=10, pady=10)
BaseTypeVar.grid(row=3, column=1, padx=10, pady=10)
ShotLable.grid(row=4, column=0, padx=10, pady=10)
ShotEntry.grid(row=4, column=1, padx=10, pady=10)
ShotBrowseBtn.grid(row=4, column=2, padx=10, pady=10)
XLable.grid(row=5, column=0, padx=10, pady=10)
XEntry.grid(row=5, column=1, padx=10, pady=10)
YLable.grid(row=6, column=0, padx=10, pady=10)
YEntry.grid(row=6, column=1, padx=10, pady=10)
Projectlable.grid(row=7, column=0, padx=10, pady=10)
Projectentry.grid(row=7, column=1, padx=10, pady=10)
RemarkLable.grid(row=8, column=0, padx=10, pady=10)
RemarkEntry.grid(row=8, column=1, padx=10, pady=10)
SaveBotton.grid(row=9, column=0, padx=10, pady=10)
ThumbnailBotton.grid(row=9, column=1, padx=10, pady=10)


#右侧显示缩略图
ImageLable = tk.Label(framelR, text="缩略图:")
ImageCanvas = tk.Canvas(framelR, width=600, height=600, bg='white')
ImageLable.grid(row=0, column=0, padx=10, pady=10)
ImageCanvas.grid(row=1, column=0, padx=10, pady=10)


GeoTiffBotton.grid(row=0, column=0, padx=10, pady=10)
LasBotton.grid(row=0, column=1, padx=10, pady=10)

MainPage.mainloop()