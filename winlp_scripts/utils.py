import math
import re
from string import ascii_lowercase
from xlrd.sheet import Cell, Sheet
from typing import Tuple, List, Generator, Union


def get_rows_with_headers(sheet: Sheet) -> Tuple[List[Cell],
                                                 Generator[List[Cell], None, None]]:
    """
    Since it ends up happening a lot, return
    """
    row_iterator = sheet.get_rows()
    headers = [cell.value for cell in next(row_iterator)]
    return headers, row_iterator

def usd(s: Union[str, float]) -> float:
    """
    Unify the values entered for USD as float (0 when NaN)
    """
    if s is None:
        return 0
    elif isinstance(s, str):
        if not s.strip():
            return 0
        s = re.sub('[\$,]', '', s)
        return float(s)
    else:
        if math.isnan(s):
            s = 0
        return float(s)

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
    import yaml
    with open(yml_path) as yml_f:
        return yaml.load(yml_f, Loader=yaml.FullLoader)