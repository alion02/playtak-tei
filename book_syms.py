import argparse
import re
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Generate rotations and reflections for grid move sequences.")
    parser.add_argument("input_file", help="Path to the input file containing move sequences.")
    parser.add_argument("--size", type=int, default=6, help="Grid size (default: 6).")
    return parser.parse_args()

class GridTransformer:
    def __init__(self, size):
        self.size = size
        # Regex to find coordinates (e.g., a1, f6, z10)
        self.coord_pattern = re.compile(r'([a-z])(\d+)', re.IGNORECASE)
        # Regex to find directions (+, -, <, >)
        self.dir_pattern = re.compile(r'[+\-<> ]')

    def _col_to_int(self, char):
        return ord(char.lower()) - ord('a')

    def _int_to_col(self, val):
        return chr(val + ord('a'))

    def _rotate_coord_90(self, match):
        """
        Rotates a coordinate 90 degrees clockwise around the center of the grid.
        Formula: new_x = old_y, new_y = (Size - 1) - old_x
        """
        col_char, row_str = match.groups()
        
        x = self._col_to_int(col_char)
        y = int(row_str) - 1 # 0-indexed internally

        # Check boundaries. If coord is outside current board config, don't touch it.
        if not (0 <= x < self.size and 0 <= y < self.size):
            return match.group(0)

        new_x = y
        new_y = (self.size - 1) - x

        return f"{self._int_to_col(new_x)}{new_y + 1}"

    def _flip_coord_horizontal(self, match):
        """
        Reflects a coordinate horizontally (across vertical center axis).
        Formula: new_x = (Size - 1) - old_x, new_y = old_y
        """
        col_char, row_str = match.groups()
        
        x = self._col_to_int(col_char)
        y = int(row_str) - 1

        if not (0 <= x < self.size and 0 <= y < self.size):
            return match.group(0)

        new_x = (self.size - 1) - x
        new_y = y

        return f"{self._int_to_col(new_x)}{new_y + 1}"

    def _rotate_dir_90(self, match):
        """
        Maps directions 90 degrees clockwise.
        + (Up)    -> > (Right)
        > (Right) -> - (Down)
        - (Down)  -> < (Left)
        < (Left)  -> + (Up)
        """
        char = match.group(0)
        mapping = {'+': '>', '>': '-', '-': '<', '<': '+'}
        return mapping.get(char, char)

    def _flip_dir_horizontal(self, match):
        """
        Maps directions for a horizontal mirror.
        + (Up)    -> + (Up)
        - (Down)  -> - (Down)
        > (Right) -> < (Left)
        < (Left)  -> > (Right)
        """
        char = match.group(0)
        mapping = {'<': '>', '>': '<'}
        return mapping.get(char, char)

    def rotate_line_90(self, line):
        # Transform coordinates
        line = self.coord_pattern.sub(self._rotate_coord_90, line)
        # Transform directions
        line = self.dir_pattern.sub(self._rotate_dir_90, line)
        return line

    def flip_line_horizontal(self, line):
        # Transform coordinates
        line = self.coord_pattern.sub(self._flip_coord_horizontal, line)
        # Transform directions
        line = self.dir_pattern.sub(self._flip_dir_horizontal, line)
        return line

def process_file(filepath, size):
    transformer = GridTransformer(size)

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    for line in lines:
        original = line.strip()
        if not original:
            continue

        variations = []
        
        # 1. Identity (0 deg)
        current = original
        variations.append(current)

        # 2-4. Rotations (90, 180, 270)
        # We chain rotate_90 three times
        for _ in range(3):
            current = transformer.rotate_line_90(current)
            variations.append(current)

        # 5. Reflection (Horizontal Flip of Original)
        flipped = transformer.flip_line_horizontal(original)
        variations.append(flipped)

        # 6-8. Rotations of the Reflected version
        current = flipped
        for _ in range(3):
            current = transformer.rotate_line_90(current)
            variations.append(current)

        # Print all 8 variations
        for v in variations:
            print(v)

if __name__ == "__main__":
    args = parse_args()
    process_file(args.input_file, args.size)