# UAV_dataMap
A tool to visually map and pinpoint the exact locations of drone aerial photos/point clouds. 直观地在地图上标记和可视化无人机航拍/点云的位置。

![工作状态](https://github.com/Mime-AL/UAV_dataMap/blob/main/imgs/img2.jpg?raw=true)

### 本工具需要使用天地图API Key，请自行申请或替换为OpenStreetMap

## 配置环境

1. 使用 ```conda env create -f environment.yml```安装环境
2. 切换环境 ```conda activate mapvisable```
3. 下载离线资源文件 ```python -m offline_folium```

## 使用
### 运行JsonMaker生成数据标记JSON

1. 从文件添加，请选择对应的文件类型，从GeoTiff，LAS/LAZ快速填写。勾选直接从文件生成缩略图会处理文件，产生缩略图，否则只获取坐标信息和文件类型。

2. 图像位置用于生成缩略图，如果不从文件生成缩略图，就需要在此处选择图像，请使用受支持的格式（JPG，PNG，8Bit通道TIFF，AVIF），选择文件后点击生成缩略图，从自定义图片生成缩略图。

3. 填写需要填写的其他信息，点击保存。将JSON文件保存到影像/点云同目录即可。

4. 软件保存的缩略图为右侧预览结果，请务必保证左侧有正确显示的缩略图！

![设置页面](https://github.com/Mime-AL/UAV_dataMap/blob/main/imgs/img3.png?raw=true)

### 运行Mapvisable进行标记可视化
1. 填写API Kay并设置文件夹位置，点击保存，根据需求选择是否更新数据。

2. 更新数据时软件会遍历整个文件夹寻找JsonMaker生成的JSON文件，并添加到数据库。

3. 软件会生成一个web地图，使用默认浏览器打开地图，并退出自身。

![设置页面](https://github.com/Mime-AL/UAV_dataMap/blob/main/imgs/img1.png?raw=true)