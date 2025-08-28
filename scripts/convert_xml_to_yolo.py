import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

def convert_xml_to_yolo(xml_file, class_mapping=None):
    """
    将XML标注文件转换为YOLO格式
    
    Args:
        xml_file: XML文件路径
        class_mapping: 类别名称到索引的映射，默认为{'pig': 0}
    
    Returns:
        YOLO格式的标注列表，每行为 [class_id, x_center, y_center, width, height]
    """
    if class_mapping is None:
        class_mapping = {'pig': 0}
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # 获取图像尺寸
    size = root.find('size')
    width = float(size.find('width').text)
    height = float(size.find('height').text)
    
    yolo_annotations = []
    
    # 遍历所有目标
    for obj in root.findall('object'):
        class_name = obj.find('name').text
        if class_name not in class_mapping:
            print(f"警告: 类别 '{class_name}' 不在映射中，跳过")
            continue
        
        class_id = class_mapping[class_name]
        
        # 获取边界框坐标
        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        ymin = float(bbox.find('ymin').text)
        xmax = float(bbox.find('xmax').text)
        ymax = float(bbox.find('ymax').text)
        
        # 转换为YOLO格式 (x_center, y_center, width, height)，归一化到0-1
        x_center = ((xmin + xmax) / 2) / width
        y_center = ((ymin + ymax) / 2) / height
        box_width = (xmax - xmin) / width
        box_height = (ymax - ymin) / height
        
        yolo_annotations.append([class_id, x_center, y_center, box_width, box_height])
    
    return yolo_annotations

def process_directory(xml_dir, output_dir, class_mapping=None):
    """处理整个目录的XML文件并输出YOLO格式的txt文件"""
    xml_dir = Path(xml_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    for xml_file in xml_dir.glob('*.xml'):
        yolo_annotations = convert_xml_to_yolo(xml_file, class_mapping)
        
        # 创建输出文件
        output_file = output_dir / f"{xml_file.stem}.txt"
        with open(output_file, 'w') as f:
            for ann in yolo_annotations:
                f.write(f"{ann[0]} {ann[1]:.6f} {ann[2]:.6f} {ann[3]:.6f} {ann[4]:.6f}\n")
        
        print(f"已转换 {xml_file.name} -> {output_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将XML标注转换为YOLO格式')
    parser.add_argument('--xml_dir', required=True, help='XML标注文件目录')
    parser.add_argument('--output_dir', required=True, help='输出YOLO格式标注的目录')
    parser.add_argument('--class_name', default='pig', help='目标类别名称')
    
    args = parser.parse_args()
    
    class_mapping = {args.class_name: 0}
    process_directory(args.xml_dir, args.output_dir, class_mapping)