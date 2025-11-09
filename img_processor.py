import os
import cv2
import numpy as np
import random
from pathlib import Path


def draw_invisible_lines(image, num_lines=None, max_alpha_shift=3):
    """
    在图片上绘制“不可见”的透明线（只修改 alpha 通道的微小值，不改变 RGB）

    Args:
        image: 输入 BGR 或 BGRA 图片（numpy array）
        num_lines: 线条数量（None -> 随机 1~10）
        max_alpha_shift: 每条线在 alpha 通道上降低的最大值（1~3 几乎不可见）

    Returns:
        RGBA 图像（BGRA 格式的 numpy array）
    """
    if num_lines is None:
        num_lines = random.randint(1, 10)

    h, w = image.shape[:2]

    # 确保图像是 BGRA 格式并且 dtype 是 uint8
    if image.shape[2] == 3:
        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    else:
        rgba = image.copy()

    # 提取 alpha 通道
    alpha = rgba[:, :, 3]

    # 创建 mask 来记录 alpha 通道变化
    mask = np.zeros((h, w), dtype=np.uint8)

    for _ in range(num_lines):
        x1, y1 = random.randint(0, w - 1), random.randint(0, h - 1)
        x2, y2 = random.randint(0, w - 1), random.randint(0, h - 1)
        thickness = random.randint(1, 3)
        delta = random.randint(1, max_alpha_shift)

        # 在 mask 上绘制线条（用 delta 表示 alpha 降低的值）
        cv2.line(mask, (x1, y1), (x2, y2), int(delta), thickness)

    # 从 alpha 中减去 mask（防止 underflow）
    new_alpha = cv2.subtract(alpha, mask)
    rgba[:, :, 3] = new_alpha

    return rgba


def visualize_invisible_lines(image_rgba, overlay_on_original=True):
    """
    生成线条可视化图（仅显示线条位置）
    Args:
        image_rgba: 含透明通道的 RGBA 图像
        overlay_on_original: 是否将线条叠加到原图上
    Returns:
        可视化图像（numpy array）
    """
    alpha = image_rgba[:, :, 3]
    mask = 255 - alpha  # 线条区域差异
    mask_vis = (mask > 0).astype(np.uint8) * 255

    if overlay_on_original:
        base = image_rgba[:, :, :3].copy()
        red_overlay = np.zeros_like(base)
        red_overlay[:, :, 2] = mask_vis
        vis = cv2.addWeighted(base, 0.7, red_overlay, 0.8, 0)
    else:
        vis = cv2.cvtColor(mask_vis, cv2.COLOR_GRAY2BGR)

    return vis


def resize_images(input_dir, output_dir, size=(800, 800)):
    """
    批量调整图片尺寸并保存。
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')

    image_files = []
    for ext in supported_formats:
        image_files.extend(Path(input_dir).glob(f'*{ext}'))
        image_files.extend(Path(input_dir).glob(f'*{ext.upper()}'))

    if not image_files:
        print(f"在目录 {input_dir} 中没有找到支持的图片文件")
        return

    print(f"找到 {len(image_files)} 张图片，开始调整尺寸...")
    resized_count = 0
    for image_path in image_files:
        try:
            # 修复中文路径读取问题
            img = cv2.imdecode(np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"无法读取图片: {image_path}")
                continue

            # 调整尺寸
            resized_img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)

            # 保存图片
            output_path = Path(output_dir) / image_path.name
            # 修复中文路径写入问题
            cv2.imencode(output_path.suffix, resized_img)[1].tofile(str(output_path))

            print(f"✅ {image_path.name} -> {output_path.name} (尺寸: {size[0]}x{size[1]})")
            resized_count += 1
        except Exception as e:
            print(f"❌ 调整图片 {image_path} 尺寸时出错: {e}")

    print(f"\n尺寸调整完成，共 {resized_count} 张图片。结果保存在: {output_dir}")


def process_images(input_dir="raw_data", output_dir="processed_images/line", visualize_dir="processed_images/visualize", num_lines=None):
    """
    批量处理图片：添加隐形透明线 + 可视化线条
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(visualize_dir).mkdir(parents=True, exist_ok=True)
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')

    image_files = []
    for ext in supported_formats:
        image_files.extend(Path(input_dir).glob(f'*{ext}'))
        image_files.extend(Path(input_dir).glob(f'*{ext.upper()}'))

    if not image_files:
        print(f"在目录 {input_dir} 中没有找到支持的图片文件")
        return

    print(f"找到 {len(image_files)} 张图片，开始处理...")

    processed_count = 0

    for image_path in image_files:
        try:
            # 修复中文路径读取问题
            img = cv2.imdecode(np.fromfile(str(image_path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"无法读取图片: {image_path}")
                continue

            # 添加隐形透明线
            processed_image = draw_invisible_lines(img, num_lines)

            # 输出文件名
            base_name = image_path.stem
            output_png = Path(output_dir) / f"processed_{base_name}.png"
            output_vis = Path(visualize_dir) / f"visualize_processed_{base_name}.png"

            # 修复中文路径写入问题
            cv2.imencode(".png", processed_image)[1].tofile(str(output_png))

            # 生成线条可视化图（红线叠加）
            vis_image = visualize_invisible_lines(processed_image, overlay_on_original=True)
            cv2.imencode(".png", vis_image)[1].tofile(str(output_vis))


            print(f"✅ {image_path.name} -> {output_png.name}, 可视化: {output_vis.name}")
            processed_count += 1

        except Exception as e:
            print(f"❌ 处理图片 {image_path} 时出错: {e}")

    print(f"\n处理完成，共 {processed_count} 张图片。结果保存在: {output_dir} 和 {visualize_dir}")


if __name__ == "__main__":
    # 示例工作流
    raw_input = "raw_data"
    resized_output = "processed_images/raw"
    line_output = "processed_images/line"
    visualize_output = "processed_images/visualize"

    # 1. 调整尺寸
    resize_images(
        input_dir=raw_input,
        output_dir=resized_output
    )

    # 2. 在调整尺寸后的图片上绘制线条
    process_images(
        input_dir=resized_output,
        output_dir=line_output,
        visualize_dir=visualize_output,
        num_lines=None
    )
