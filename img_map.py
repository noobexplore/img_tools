import random
import math
import os
from PIL import Image
from pathlib import Path
from img_processor import process_images as draw_lines_on_images
from img_processor import resize_images


def merge_images(base_image_path, overlay_image_path, output_image_path, tolerance=10):
    """
    将叠加图片融合到底图上，并以底图大小为准。
    白色背景将被处理为透明。
    """
    try:
        # 打开底图和叠加图
        base_image = Image.open(base_image_path).convert("RGBA")
        overlay_image = Image.open(overlay_image_path).convert("RGBA")

        # --- 新增代码：将叠加图的白色背景变为透明 ---
        overlay_data = overlay_image.getdata()
        new_data = []
        for item in overlay_data:
            # 如果像素是白色（考虑到一定的容差）
            if item[0] > (255 - tolerance) and item[1] > (255 - tolerance) and item[2] > (255 - tolerance):
                new_data.append((255, 255, 255, 0))  # 设置为透明
            else:
                new_data.append(item)
        overlay_image.putdata(new_data)
        # --- 代码结束 ---

        # 获取底图的尺寸
        base_width, base_height = base_image.size

        # 将处理过透明背景后的叠加图调整为底图的尺寸
        overlay_image_resized = overlay_image.resize((base_width, base_height), Image.LANCZOS)

        # 直接在底图上叠加（alpha_composite需要两个RGBA图像）
        merged_image = Image.alpha_composite(base_image, overlay_image_resized)

        # 保存融合后的图片
        merged_image.save(output_image_path)
        print(f"图片成功融合并保存到: {output_image_path}")

    except FileNotFoundError:
        print("错误: 确保图片路径正确。")
    except Exception as e:
        print(f"发生错误: {e}")


def merge_images_with_grid_jitter(input_folder, star_images_folder, output_folder, grid_size=(10, 10), density=0.8,
                                  scale_range=(0.2, 1.0), tolerance=10):
    """
    策略 'grid': 在地图上使用网格抖动算法叠加星星图片。
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    image_files = list(Path(input_folder).glob('*[!.db]'))
    star_image_files = list(Path(star_images_folder).glob('*[!.db]'))

    if not star_image_files:
        print("错误: 星星图片文件夹下没有找到图片。")
        return

    for image_file in image_files:
        star_image_path = random.choice(star_image_files)
        output_image_path = output_path / f"grid_jitter_{image_file.name}"

        try:
            base_image = Image.open(image_file).convert("RGBA")
            original_star_image = Image.open(star_image_path).convert("RGBA")
            base_width, base_height = base_image.size

            star_data = original_star_image.getdata()
            new_data = []
            for item in star_data:
                if item[0] > (255 - tolerance) and item[1] > (255 - tolerance) and item[2] > (255 - tolerance):
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            original_star_image.putdata(new_data)

            grid_cols, grid_rows = grid_size
            cell_width = base_width // grid_cols
            cell_height = base_height // grid_rows
            star_count = 0

            for i in range(grid_cols):
                for j in range(grid_rows):
                    if random.random() < density:
                        scale_factor = random.uniform(*scale_range)
                        scaled_star_width = int(original_star_image.width * scale_factor)
                        scaled_star_height = int(original_star_image.height * scale_factor)
                        if scaled_star_width < 1: scaled_star_width = 1
                        if scaled_star_height < 1: scaled_star_height = 1
                        scaled_star_image = original_star_image.resize((scaled_star_width, scaled_star_height), Image.LANCZOS)
                        max_offset_x = max(0, cell_width - scaled_star_width)
                        max_offset_y = max(0, cell_height - scaled_star_height)
                        offset_x = random.randint(0, max_offset_x)
                        offset_y = random.randint(0, max_offset_y)
                        x = (i * cell_width) + offset_x
                        y = (j * cell_height) + offset_y
                        base_image.paste(scaled_star_image, (x, y), scaled_star_image)
                        star_count += 1

            if image_file.suffix.lower() in ['.jpg', '.jpeg']:
                base_image = base_image.convert("RGB")
            base_image.save(output_image_path)
            print(f"成功使用网格抖动布局添加 {star_count} 个星星，并保存到: {output_image_path}")

        except FileNotFoundError:
            print(f"错误: 确保图片路径正确。请检查 '{image_file}' 和 '{star_image_path}' 是否存在。")
        except Exception as e:
            print(f"发生错误: {e}")


def _poisson_disc_sample(width, height, min_dist, k=30):
    cell_size = min_dist / math.sqrt(2)
    grid_width = math.ceil(width / cell_size)
    grid_height = math.ceil(height / cell_size)
    grid = [None] * (grid_width * grid_height)
    samples, active_list = [], []
    p0 = (random.uniform(0, width), random.uniform(0, height))
    samples.append(p0)
    active_list.append(p0)
    grid_x, grid_y = int(p0[0] / cell_size), int(p0[1] / cell_size)
    grid[grid_x + grid_y * grid_width] = p0
    while active_list:
        idx = random.randrange(len(active_list))
        p = active_list[idx]
        found = False
        for _ in range(k):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(min_dist, 2 * min_dist)
            px, py = p[0] + dist * math.cos(angle), p[1] + dist * math.sin(angle)
            if not (0 <= px < width and 0 <= py < height): continue
            gx, gy = int(px / cell_size), int(py / cell_size)
            too_close = False
            for i in range(max(0, gx - 2), min(grid_width, gx + 3)):
                for j in range(max(0, gy - 2), min(grid_height, gy + 3)):
                    neighbor = grid[i + j * grid_width]
                    if neighbor and math.sqrt((px - neighbor[0]) ** 2 + (py - neighbor[1]) ** 2) < min_dist:
                        too_close = True
                        break
                if too_close: break
            if not too_close:
                samples.append((px, py))
                active_list.append((px, py))
                grid[gx + gy * grid_width] = (px, py)
                found = True
                break
        if not found: active_list.pop(idx)
    return samples


def merge_images_with_poisson_disc(input_folder, star_images_folder, output_folder, min_distance=50,
                                   scale_range=(0.2, 1.0), tolerance=10):
    """
    策略 'disc': 在地图上使用泊松盘采样算法叠加星星图片。
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    image_files = list(Path(input_folder).glob('*[!.db]'))
    star_image_files = list(Path(star_images_folder).glob('*[!.db]'))

    if not star_image_files:
        print("错误: 星星图片文件夹下没有找到图片。")
        return

    for image_file in image_files:
        star_image_path = random.choice(star_image_files)
        output_image_path = output_path / f"poisson_disc_{image_file.name}"

        try:
            base_image = Image.open(image_file).convert("RGBA")
            original_star_image = Image.open(star_image_path).convert("RGBA")
            base_width, base_height = base_image.size

            star_data = original_star_image.getdata()
            new_data = []
            for item in star_data:
                if item[0] > (255 - tolerance) and item[1] > (255 - tolerance) and item[2] > (255 - tolerance):
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            original_star_image.putdata(new_data)

            points = _poisson_disc_sample(base_width, base_height, min_distance)

            for x, y in points:
                scale_factor = random.uniform(*scale_range)
                scaled_star_width = int(original_star_image.width * scale_factor)
                scaled_star_height = int(original_star_image.height * scale_factor)
                if scaled_star_width < 1: scaled_star_width = 1
                if scaled_star_height < 1: scaled_star_height = 1
                scaled_star_image = original_star_image.resize((scaled_star_width, scaled_star_height), Image.LANCZOS)
                paste_x, paste_y = int(x - scaled_star_width / 2), int(y - scaled_star_height / 2)
                if 0 <= paste_x < base_width and 0 <= paste_y < base_height:
                    base_image.paste(scaled_star_image, (paste_x, paste_y), scaled_star_image)

            if image_file.suffix.lower() in ['.jpg', '.jpeg']:
                base_image = base_image.convert("RGB")
            base_image.save(output_image_path)
            print(f"成功使用泊松盘采样布局添加 {len(points)} 个星星，并保存到: {output_image_path}")

        except FileNotFoundError:
            print(f"错误: 确保图片路径正确。请检查 '{image_file}' 和 '{star_image_path}' 是否存在。")
        except Exception as e:
            print(f"发生错误: {e}")


import argparse


def run_pipeline(args):
    """
    执行完整的图像处理流水线。
    """
    # --- 路径定义 ---
    base_dir = Path(args.input_dir)
    raw_input_folder = base_dir
    star_assets_folder = Path("star_images")
    map_images_folder = Path("map_images")
    
    # 新增：调整尺寸后的图片目录
    resized_output_folder = base_dir / "processed_images" / "raw"
    
    line_output_folder = base_dir / "processed_images" / "line"
    final_map_folder = base_dir / "processed_images" / "map"
    merge_output_folder = base_dir / "processed_images" / "merge"
    visualize_output_folder = base_dir / "processed_images" / "visualize"

    # 确保所有输出目录都存在
    for folder in [resized_output_folder, line_output_folder, final_map_folder, merge_output_folder, visualize_output_folder]:
        folder.mkdir(parents=True, exist_ok=True)

    # --- 步骤 0: 调整图片尺寸 ---
    print("--- [步骤 0/3] 开始调整图片尺寸... ---")
    resize_images(
        input_dir=raw_input_folder,
        output_dir=resized_output_folder
    )
    print("--- 图片尺寸调整完成 ---\n")

    # --- 步骤 1: 绘制透明线 ---
    print("--- [步骤 1/3] 开始绘制透明线... ---")
    draw_lines_on_images(
        input_dir=resized_output_folder,  # 使用调整尺寸后的图片
        output_dir=line_output_folder,
        visualize_dir=visualize_output_folder,
        num_lines=100
    )
    print("--- 透明线绘制完成 ---\n")

    # --- 步骤 2: 根据策略叠加 ---
    strategy = args.strategy
    print(f"--- [步骤 2/3] 应用 '{strategy}' 策略进行叠加... ---")

    line_processed_files_folder = line_output_folder

    if strategy == 'grid':
        merge_images_with_grid_jitter(
            input_folder=line_processed_files_folder,
            star_images_folder=star_assets_folder,
            output_folder=final_map_folder,
            grid_size=args.grid_size,
            density=args.density,
            scale_range=args.scale_range
        )
    elif strategy == 'disc':
        merge_images_with_poisson_disc(
            input_folder=line_processed_files_folder,
            star_images_folder=star_assets_folder,
            output_folder=final_map_folder,
            min_distance=args.min_distance,
            scale_range=args.scale_range
        )
    elif strategy == 'merge':
        line_files = list(line_processed_files_folder.glob('*[!.db]'))
        map_files = list(map_images_folder.glob('*[!.db]'))

        if not map_files:
            print("错误: 地图图片文件夹下没有找到图片。")
            return

        for line_file in line_files:
            map_file = random.choice(map_files)
            output_image_path = merge_output_folder / f"merged_{line_file.name}"
            merge_images(line_file, map_file, output_image_path)
    else:
        print(f"错误：未知的策略 '{strategy}'。请选择 'grid', 'disc', 或 'merge'。")

    print(f"--- '{strategy}' 策略处理完成 ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图像处理流水线")
    parser.add_argument(
        'strategy', type=str, choices=['grid', 'disc', 'merge'], help="选择要执行的策略: 'grid', 'disc', 或 'merge'")
    parser.add_argument(
        'input_dir', type=str, help="输入文件夹的路径")

    # 'grid' 策略的参数
    grid_group = parser.add_argument_group('grid 策略参数')
    grid_group.add_argument('--grid_size', type=int, nargs=2, default=[5, 5], help="网格大小 (例如, 5 5)")
    grid_group.add_argument('--density', type=float, default=0.75, help="星星密度 (0.0 到 1.0)")

    # 'disc' 策略的参数
    disc_group = parser.add_argument_group('disc 策略参数')
    disc_group.add_argument('--min_distance', type=int, default=70, help="星星之间的最小距离")

    # 通用参数
    parser.add_argument('--scale_range', type=float, nargs=2, default=[0.2, 0.3], help="星星缩放范围 (例如, 0.2 0.3)")

    args = parser.parse_args()

    run_pipeline(args)
