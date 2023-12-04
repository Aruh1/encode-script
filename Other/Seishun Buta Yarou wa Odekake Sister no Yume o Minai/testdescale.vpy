from descale_analysis import test_descale_error
from vskernels import Bicubic
from vstools import core, depth

src = core.lsmas.LWLibavSource(
    r"E:\torrent\[BDMV][231129][ANZX-17001~4][青春ブタ野郎はおでかけシスターの夢を見ない]\BD_VIDEO\BDMV\STREAM\00000.m2ts"
)
bit = depth(src, 16)

kernelres0 = dict(width=1386, height=878, fractional=719.8, kernel=Bicubic(0, 1 / 2))
test = test_descale_error(src, kernelres0)
test.set_output()
