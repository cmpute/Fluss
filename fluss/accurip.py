# AccurateRip support is based on CUETools

import asyncio
import subprocess
from pathlib import Path
from typing import Union

import parse
from addict import Dict as edict

from .config import global_config


async def verify_accurip(input_file: Union[str, Path]) -> str:
    args = [global_config.path.arcue, "-v", str(input_file)]
    process = await asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE)
    rt = await process.wait()
    if rt != 0:
        raise RuntimeError("ARCue returned non-zero!")
    return await process.stdout.read()

def parse_accurip(accurip_log: Union[str, bytes]) -> dict:
    '''
    Parse AccurateRip verification log in CUETools format
    :return: A dict containing parsed information
    '''
    if isinstance(accurip_log, bytes):
        accurip_log = accurip_log.decode()

    lines = accurip_log.splitlines()
    assert lines[0].startswith("[CUETools log;"), "Incorrect CUETools log"

    result = edict()
    result.fail = False
    for l in lines:
        ctdb_status = parse.parse("        [{:x}] ({1}) {2}", l)
        if ctdb_status:
            ctdbid, conf, status = ctdb_status
            result[ctdbid] = conf, status
            if "Differs" in status:
                result.fail = True

        if "NOT ACCURATE" in l:  # AccurateRip failed
            result.fail = True

        if "mismatch" in l:  # DISCID mismatch
            result.fail = True

    return result
