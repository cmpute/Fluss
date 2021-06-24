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
            conf_num, conf_denum = conf.split("/")
            conf = int(conf_num) / max(1, int(conf_denum))
            result[ctdbid] = conf, status
            if "differs" in status: # differ in matching
                result.fail = True
            if "no match" in status and conf < 0.4: # completely no match
                result.fail = True

        if "not accurate" in l.lower():  # AccurateRip failed
            result.fail = True

        if "mismatch" in l.lower():  # DISCID mismatch
            result.fail = True

    return result
