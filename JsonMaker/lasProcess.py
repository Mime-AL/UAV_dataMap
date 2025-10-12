import laspy
import numpy as np
from PIL import Image
from functools import partial
import matplotlib.pyplot as plt

# 获取las文件的坐标系和中心点，输入las文件路径，中心X，Y坐标，和坐标系
def lasLocation(lasPath):
    try:
        with laspy.open(lasPath) as las:
            header = las.header
            # 获取坐标系EPSG
            epsg = None
            if hasattr(header, "parse_crs"):
                crs = header.parse_crs()
                if crs and hasattr(crs, "to_epsg"):
                    epsg = crs.to_epsg()
            elif hasattr(header, "srs"):
                crs = header.srs
                if crs and hasattr(crs, "to_epsg"):
                    epsg = crs.to_epsg()
            
            min_x = header.mins[0]
            max_x = header.maxs[0]
            min_y = header.mins[1]
            max_y = header.maxs[1]
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2

            return {
                "success": True,
                "epsg": epsg,
                "x": center_x,
                "y": center_y
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def las_to_thumbnail(las_path, output_path, size=(600, 600), sample_points=20000):
    with laspy.open(las_path) as las:
        points = las.read()
        total_points = len(points.x)
        step = max(total_points // sample_points, 1)
        indices = np.arange(0, total_points, step)[:sample_points]
        x = points.x[indices]
        y = points.y[indices]
        # 判断是否有RGB信息
        if hasattr(points, "red") and hasattr(points, "green") and hasattr(points, "blue"):
            r = points.red[indices]
            g = points.green[indices]
            b = points.blue[indices]
            # 归一化到0-1
            rgb = np.stack([r, g, b], axis=1) / 65535.0 if r.max() > 255 else np.stack([r, g, b], axis=1) / 255.0
        else:
            rgb = "blue"
        plt.figure(figsize=(size[0]/100, size[1]/100), dpi=100)
        plt.scatter(x, y, c=rgb, s=0.1, marker='.')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
        plt.close()