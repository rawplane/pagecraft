#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import img2pdf
from PIL import Image
from tqdm import tqdm

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}

def validate_image_file(file_path: Path) -> bool:
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}", file=sys.stderr)
        return False
    if not file_path.is_file():
        print(f"Warning: Not a file: {file_path}", file=sys.stderr)
        return False
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Warning: Unsupported file type, skipping: {file_path}", file=sys.stderr)
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"Warning: Invalid or corrupted image, skipping: {file_path} ({e})", file=sys.stderr)
        return False

def get_image_files(input_paths: List[str], sort_by: str = 'name') -> List[Path]:
    image_files: List[Path] = []
    
    for input_path in input_paths:
        path = Path(input_path)
        
        if path.is_file():
            if validate_image_file(path):
                image_files.append(path)
        elif path.is_dir():
            for file in path.iterdir():
                if validate_image_file(file):
                    image_files.append(file)
        else:
            print(f"Warning: Path not found or inaccessible: {path}", file=sys.stderr)
    
    if sort_by == 'name':
        image_files.sort(key=lambda x: x.name.lower())
    elif sort_by == 'created':
        image_files.sort(key=lambda x: x.stat().st_ctime)
    elif sort_by == 'modified':
        image_files.sort(key=lambda x: x.stat().st_mtime)
    
    return image_files

def get_page_size(size: str, img: bytes) -> Tuple[float, float]:
    if size == 'a4':
        return img2pdf.get_layout_fun(img2pdf.pagesizes['A4'])
    elif size == 'letter':
        return img2pdf.get_layout_fun(img2pdf.pagesizes['letter'])
    else:
        return None

def create_pdf(image_files: List[Path], output_path: str, page_size: str) -> None:
    if not image_files:
        print("Error: No valid image files to convert", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(image_files)} image(s)...")
    
    img_data_list = []
    
    for img_path in tqdm(image_files, desc="Reading images", unit="img"):
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
            img_data_list.append(img_data)
        except PermissionError:
            print(f"Warning: Permission denied, skipping: {img_path}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Warning: Error reading file {img_path}: {e}", file=sys.stderr)
            continue
    
    if not img_data_list:
        print("Error: Failed to read any image files", file=sys.stderr)
        sys.exit(1)
    
    layout_fun = None
    if page_size in ('a4', 'letter'):
        layout_fun = img2pdf.get_layout_fun(img2pdf.pagesizes[page_size])
    
    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            if layout_fun:
                f.write(img2pdf.convert(img_data_list, layout_fun=layout_fun))
            else:
                f.write(img2pdf.convert(img_data_list))
        
        print(f"\nSuccess! PDF created: {output_path}")
        print(f"Total images processed: {len(img_data_list)}")
        
    except PermissionError:
        print(f"Error: Permission denied writing to {output_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Convert images to PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s image.jpg -o output.pdf
  %(prog)s img1.jpg img2.png img3.webp -o merged.pdf
  %(prog)s /path/to/images -o all_images.pdf
  %(prog)s image.jpg --size a4 -o document.pdf
  %(prog)s images/ --sort-by modified -o sorted.pdf
        '''
    )
    
    parser.add_argument(
        'input',
        nargs='+',
        help='Input image file(s) or directory containing images'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output PDF file path'
    )
    
    parser.add_argument(
        '--size',
        choices=['auto', 'a4', 'letter'],
        default='auto',
        help='Page size: auto (original), a4, or letter (default: auto)'
    )
    
    parser.add_argument(
        '--sort-by',
        choices=['name', 'created', 'modified'],
        default='name',
        help='Sort images by: name (alphanumeric), created (creation time), modified (default: name)'
    )
    
    args = parser.parse_args()
    
    image_files = get_image_files(args.input, args.sort_by)
    
    if not image_files:
        print("Error: No valid image files found", file=sys.stderr)
        sys.exit(1)
    
    create_pdf(image_files, args.output, args.size)

if __name__ == '__main__':
    main()
