# UAV_dataMap
A tool to visually map and pinpoint the exact locations of drone aerial photos/point clouds. 直观地在地图上标记和可视化无人机航拍/点云的位置。

### 本工具需要使用天地图API Key，请自行申请或替换为OpenStreetMap

## 配置环境

1. 使用 ```conda env create -f environment.yml```安装环境
2. 切换环境 ```conda activate mapvisable```
3. 下载离线资源文件 ```python -m offline_folium```

## 使用
### 运行JsonMaker生成数据标记JSON

### 运行Mapvisable进行标记可视化