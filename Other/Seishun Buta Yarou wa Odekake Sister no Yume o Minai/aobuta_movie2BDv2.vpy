from awsmfunc import bbmod
from kagefunc import adaptive_grain
from polofunc import masked_f3kdb, nnedi3
from vsdehalo import dehalo_sigma, fine_dehalo, smooth_dering
from vsdenoise import Prefilter
from vsrgtools import bilateral
from vstools import core, set_output
from vsutil import depth

core.max_cache_size = 1024 * 2

bd = core.lsmas.LWLibavSource(
    r"E:\torrent\[BDMV][231129][ANZX-17001~4][青春ブタ野郎はおでかけシスターの夢を見ない]\BD_VIDEO\BDMV\STREAM\00000.m2ts"
)
src = depth(bd, 16)

edgefix = bbmod(src, 1, 1, 1, 1, 30)

sloc = [0, 0, 0.4, 1, 0.45, 3, 0.5, 5, 1, 32]
denoise = core.dfttest.DFTTest(edgefix, tbsize=1, slocation=sloc)
aa = nnedi3(denoise, opencl=False)

dering = smooth_dering(aa, mrad=3, msmooth=1, minp=1, mthr=0.20, darkthr=0, contra=0)
dering_mask = fine_dehalo(aa)

dh_sigma = dehalo_sigma(dering_mask, blur_func=Prefilter.GAUSSBLUR2, pre_ss=2)
dh_bil = bilateral(edgefix, sigmaS=1.5, ref=dh_sigma, planes=0)
dh = core.akarin.Expr([src, dh_bil, dh_sigma], "x y z max min")

dh_masked = fine_dehalo.mask(aa, dh, thmi=80, thma=110, rx=2.0)

# dering = smooth_dering(denoise)
# dehalo = fine_dehalo(dering)
# dehalo_mask = fine_dehalo(dehalo, show_mask=True)
# dehalo_mask = (
#     core.tcanny.TCanny(get_y(dehalo), 1.5, 1.5, op=2, mode=1, scale=1.0)
#     .std.Binarize(5000)
#     .std.Maximum()
# )
# merge_mask = core.std.MaskedMerge(denoise, aa, dh_masked)

deband = masked_f3kdb(dh_masked, rad=20, thr=[28, 24], grain=[24, 12])

grain = adaptive_grain(deband, 0.8)

out = depth(grain, 10)
set_output(bd, "JPBD")
set_output(out, "filtering")
