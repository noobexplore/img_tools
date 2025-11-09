图片处理工具

star_images：为星星素材池，随机选择

map_images：为叠加池，叠加的是整张图片

输出的目录：

processed_images/line为划线的临时图

processed_images/map为最终星星打点的图片

processed_images/merge为叠加图片最终效果图

processed_images/visualize为划线的效果对比图

命令行如下：
disc策略推荐

python img_map.py disc D:\BaiduNetdiskDownload\1 --min_distance 100 --scale_range 0.2 0.3

D:/开头的为文件夹路径，min_distance为星星之间的距离，scale_range为每个星星的缩放比例


grid策略

python img_map.py grid D:\BaiduNetdiskDownload\1 --grid_size 5 5 --density 0.75 

星星密度 (0.0 到 1.0)

merge策略

python img_map.py merge