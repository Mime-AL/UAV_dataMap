import base64
from PIL import Image
import pillow_avif
from osgeo import gdal
import pyproj
from pyproj.enums import WktVersion
import os
import numpy as np


def Image_to_Base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        return ""
    
def ImageResize(input_path: str, output_path: str, size: tuple) -> bool:
    try:
        with Image.open(input_path) as img:
            img.thumbnail(size)
            img.save(output_path, "AVIF")
        return True
    except Exception as e:
        return False

def GeoTIFF_to_Thumbnail_and_Info(geotiff_path: str, thumbnail_path: str, DirectThumbnail: bool, thumbnail_size=(600, 600)):
    info = {
        "x": 0.0,
        "y": 0.0,
        "wtk": "",
        "epsg": "",
        "success": False,
        "error": "",
        "Channels": 0
    }
    #读取文件
    try:
        dataset = gdal.Open(geotiff_path)
    except Exception as e:
        info["error"] = f"无法打开文件: {geotiff_path}, 错误: {e}"
        return info
    
    #获取坐标系统
    try:
        projection_wkt = dataset.GetProjection()
        spatial_ref = pyproj.CRS.from_wkt(projection_wkt)
        info["wtk"] = spatial_ref.to_wkt(version=WktVersion.WKT2_2019)
        info["epsg"] = spatial_ref.to_epsg()
    except Exception as e:
        info["error"] = f"无法获取坐标系统: {e}"
        return info
    
    #获取图像中心位置
    try:
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        geotransform = dataset.GetGeoTransform()
        center_x = geotransform[0] + width * geotransform[1] / 2 + height * geotransform[2] / 2
        center_y = geotransform[3] + width * geotransform[4] / 2 + height * geotransform[5] / 2
        info["x"] = center_x
        info["y"] = center_y
    except Exception as e:
        info["error"] = f"无法获取图像中心位置: {e}"
        return info
    
    #生成缩略图
    if DirectThumbnail:
        try:
            bands_data = []
            for i in range(1, dataset.RasterCount + 1):
                band = dataset.GetRasterBand(i)
                bands_data.append(band.ReadAsArray())
            image_data = np.dstack(bands_data)
            # 只取前三个波段作为RGB
            info["Channels"] = image_data.shape[2]
            if image_data.shape[2] >= 3:
                rgb_data = image_data[:, :, :3]
            else:
                # 少于3通道时补齐
                rgb_data = np.repeat(image_data, 3, axis=2)[:, :, :3]
            image = Image.fromarray(rgb_data)
            image = image.resize(thumbnail_size, Image.BILINEAR)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(thumbnail_path, "AVIF")
        except Exception as e:
            info["error"] = f"无法生成缩略图: {e}"
            return info
    
    info["success"] = True
    return info
