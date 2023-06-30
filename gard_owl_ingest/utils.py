"""Utilities"""
import os
from pathlib import PosixPath
from typing import Union

import pandas as pd


def write_tsv_with_comments(df: pd.DataFrame, comments_file: Union[PosixPath, str], outpath: Union[PosixPath, str]):
    """pass"""
    # write metadata
    f = open(comments_file, "r")
    lines = f.readlines()
    f.close()
    output_lines = []
    for line in lines:
        output_lines.append("# " + line)
    metadata_str = ''.join(output_lines)
    if os.path.exists(outpath):
        os.remove(outpath)
    f = open(outpath, 'a')
    f.write(metadata_str)
    f.close()
    # write data
    df.to_csv(outpath, index=False, sep='\t', mode='a')
