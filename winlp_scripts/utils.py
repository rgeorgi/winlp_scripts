from string import ascii_lowercase
from xlrd.sheet import Cell, Sheet
import yaml
from typing import Tuple, List, Generator

def get_rows_with_headers(sheet: Sheet) -> Tuple[List[Cell],
                                                 Generator[List[Cell], None, None]]:
    """
    Since it ends up happening a lot, return
    """
    row_iterator = sheet.get_rows()
    headers = [cell.value for cell in next(row_iterator)]
    return headers, row_iterator


def col_letter(col_str):
    sum = 0
    for i, letter in enumerate(reversed(col_str.lower())):
        sum += (ascii_lowercase.index(letter)+1)*(26**i)
    return sum - 1

def overlap_bitstring(bs_a, bs_b):
    sum = 0
    for a, b in zip(bs_a, bs_b):
        if a and b:
            sum += 1
    return sum

def yn(cell: Cell) -> bool:
    """
    Return the "yes/no" as a boolean, rather than
    the string.
    """
    return cell.value == 'Yes'

def cols_to_bitstring(row, start_col: str, stop_col: str):
    start_index = col_letter(start_col)
    stop_index = col_letter(stop_col)
    print(start_col, start_index, stop_col, stop_index)
    return [int(cell.value == 'Yes') for cell in row[start_index:stop_index+1]]

def load_yml(yml_path):
    """
    Load a yaml file from the specified path.
    """
    with open(yml_path) as yml_f:
        return yaml.load(yml_f, Loader=yaml.FullLoader)