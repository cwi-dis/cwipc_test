import argparse
import sys
from PIL import Image
import cwipc

def main():
    parser = argparse.ArgumentParser(description="Convert image to point cloud")
    parser.add_argument("--pointsize", action="store", default=0.01, type=float, help="Width/height of one pixel (in meters)")
    parser.add_argument("--bottom", action="store", default=0, type=float, help="Y coordinate of bottom of image (in meters)")
    parser.add_argument("input", type=str, action="store", help="Input image (.png, .jpg, etc)")
    parser.add_argument("output", type=str, action="store", help="Output point cloud (.ply or .cwipcdump)")
    args = parser.parse_args()
    convert(args.input, args.output, args.pointsize, args.bottom)

def convert(input : str, output : str, pointsize : float, bottom : float):
    print(f"Input={input}, Output={output}, pointsize={pointsize}, bottom={bottom}")
    with Image.open(input) as im:
        w = im.width
        h = im.height
        print(f"Image: {w}x{h} pixels")
        left_x = -(w/2.0)*pointsize
        right_x = (w/2.0)*pointsize
        bottom_y = bottom
        top_y = bottom + h*pointsize
        print(f"X-range: {left_x}..{right_x}")
        print(f"Y-range: {top_y}..{bottom_y}")
        print(f"Z-range: 0")
        points = []
        for y in range(0, h):
            for x in range(0, w):
                pt_x = left_x + (x*pointsize)
                pt_y = top_y - (y*pointsize)
                pt_z = 0.0
                pt_r, pt_g, pt_b = im.getpixel((x, y))
                pt_mask = 0
                points.append((pt_x, pt_y, pt_z, pt_r, pt_g, pt_b, pt_mask))
        pc = cwipc.cwipc_from_points(points, 0)
        if output.endswith(".ply"):
            cwipc.cwipc_write(output, pc)
        elif output.endswith(".cwipcdump"):
            cwipc.cwipc_write_debugdump(output, pc)
        else:
            print(f"{sys.argv[0]}: Unknown extension in {output}, .ply and .cwipcdump supported")
            



if __name__ == "__main__":
    main()