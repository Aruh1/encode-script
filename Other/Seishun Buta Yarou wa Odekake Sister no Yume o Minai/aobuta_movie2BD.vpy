import rekt
from awsmfunc import FrameInfo, bbmod
from kagefunc import adaptive_grain
from polofunc import masked_f3kdb, nnedi3
from vsdehalo import fine_dehalo
from vstools import core, set_output
from vsutil import depth, get_y

core.max_cache_size = 1024 * 2

bd = core.lsmas.LWLibavSource(
    r"E:\torrent\[BDMV][231129][ANZX-17001~4][青春ブタ野郎はおでかけシスターの夢を見ない]\BD_VIDEO\BDMV\STREAM\00000.m2ts"
)
src = depth(bd, 16)

ef = rekt.rektlvls(
    src,
    prot_val=[16, 235],
    rownum=[0, src.height - 1],
    rowval=[16, 16],
    colnum=[0, src.width - 1],
    colval=[16, 16],
)
bb_y = bbmod(ef, left=1, top=1, right=1, bottom=1, thresh=32, y=True, u=False, v=False)
bb_uv = bbmod(bb_y, left=2, top=2, right=2, bottom=2, y=False, u=True, v=True)

sloc = [0, 0, 0.4, 1, 0.45, 3, 0.5, 5, 1, 32]
denoise = core.dfttest.DFTTest(bb_uv, tbsize=1, slocation=sloc)
aa = nnedi3(denoise, opencl=False)

dehalo = fine_dehalo(denoise)
dehalo_mask = (
    core.tcanny.TCanny(get_y(dehalo), 1.5, 1.5, op=2, mode=1, scale=1.25)
    .std.Binarize(5000)
    .std.Maximum()
)
merge_mask = core.std.MaskedMerge(aa, dehalo, dehalo_mask)

deband = masked_f3kdb(merge_mask, rad=20, thr=[28, 24], grain=[24, 12])

grain = adaptive_grain(deband, 0.8)

out = depth(grain, 10)
# set_output(src, "JPBD")
set_output(out, "filtering")
