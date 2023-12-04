from awsmfunc import bbmod
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

edgefix = bbmod(src, 1, 1, 1, 1, 30)

sloc = [0, 0, 0.4, 1, 0.45, 3, 0.5, 5, 1, 32]
denoise = core.dfttest.DFTTest(edgefix, tbsize=1, slocation=sloc)
aa = nnedi3(denoise, opencl=False)

dehalo = fine_dehalo(denoise)
dehalo_mask = (
    core.tcanny.TCanny(get_y(dehalo), 1.5, 1.5, op=2, mode=1, scale=1.25)
    .std.Binarize(5000)
    .std.Maximum()
)
merge_mask = core.std.MaskedMerge(dehalo, aa, dehalo_mask)

deband = masked_f3kdb(merge_mask, rad=20, thr=[28, 24], grain=[24, 12])

grain = adaptive_grain(deband, 0.8)

out = depth(grain, 10)
# set_output(src, "JPBD")
set_output(out, "filtering")
