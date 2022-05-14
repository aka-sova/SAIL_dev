import os, sys
sys.path.append("scripts")

from scripts.sail_b_utils import *
from scripts.utils import *




def main():
    
    fib_filepath = os.path.abspath("input/rib.txt")
    output_bitmap_fold = os.path.abspath("output/sail_b_bitmaps")

    os.makedirs(output_bitmap_fold, exist_ok=True)

    cfib_main = CFib()

    cfib_main.build_fib_from_file(fib_filepath, print_every = 5000) 
    cfib_main.print_statistics()
    cfib_main.create_bitmaps(output_bitmap_fold)


if __name__ == "__main__":
    main()