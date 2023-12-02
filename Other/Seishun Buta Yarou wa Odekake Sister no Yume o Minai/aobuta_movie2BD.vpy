from havsfunc import SMDegrain
from kagefunc import adaptive_grain
from polofunc import masked_f3kdb
from vsdehalo import dehalo_sigma, fine_dehalo
from vsdenoise import Prefilter
from vstools import core, depth, get_y, set_output, vs
from typing import Any, Callable, Dict

core.max_cache_size = 1024 * 2

### CUSTOM FUNCTIONS
def taa(clip: vs.VideoNode, aafun: Callable[[vs.VideoNode], vs.VideoNode]) -> vs.VideoNode:
    """
    Perform transpose AA.
    :param clip:   Input clip.
    :param aafun:  Antialiasing function
    :return:       Antialiased clip
    """
    if clip.format is None:
        raise ValueError("taa: 'Variable-format clips not supported'")

    y = get_y(clip)

    aa = aafun(y.std.Transpose())
    aa = aa.resize.Spline36(height=clip.width, src_top=0.5).std.Transpose()
    aa = aafun(aa)
    aa = aa.resize.Spline36(height=clip.height, src_top=0.5)

    return aa if clip.format.color_family == vs.GRAY \
        else core.std.ShufflePlanes([aa, clip], planes=[0, 1, 2], colorfamily=vs.YUV)

def nnedi3(clip: vs.VideoNode, opencl: bool = False, **override: Any) -> vs.VideoNode:
    """
    Standard nnedi3 antialiasing.
    :param clip:     Input clip
    :param opencl:   Use OpenCL (Default: False)
    :param override: nnedi3 parameter overrides
    :return:         Antialiased clip
    """
    nnedi3_args: Dict[str, Any] = dict(field=0, dh=True, nsize=3, nns=3, qual=1)
    nnedi3_args.update(override)

    def _nnedi3(clip: vs.VideoNode) -> vs.VideoNode:
        return clip.nnedi3cl.NNEDI3CL(**nnedi3_args) if opencl \
            else clip.nnedi3.nnedi3(**nnedi3_args)

    return taa(clip, _nnedi3)


###GETTING SOURCES
src = core.lsmas.LWLibavSource(
    r"E:\torrent\[BDMV][231129][ANZX-17001~4][青春ブタ野郎はおでかけシスターの夢を見ない]\BD_VIDEO\BDMV\STREAM\00000.m2ts"
)
bit = depth(src, 16)

###AA
aa = nnedi3(bit, opencl=False)

preden = SMDegrain(get_y(bit), tr=2, thSAD=120, RefineMotion=True, prefilter=2)
mask = preden.std.Prewitt().std.Binarize(65 << 8)
aamask = mask.std.Inflate()
aamasked = core.std.MaskedMerge(get_y(bit), aa, aamask)

grainmask1 = mask.std.Deflate().std.Deflate()
grainmask2 = core.std.Expr([aamask.std.Inflate(), grainmask1], "x y -").std.BoxBlur()

aagrain = core.grain.Add(aamasked, seed=1, var=0.70, uvar=0.0, constant=True)
aagrained = core.std.MaskedMerge(aamasked, aagrain, grainmask2)


###DEHALO
doubledh = (
    aagrained.znedi3.nnedi3(field=0, dh=True, nsize=4, nns=3)
    .std.Transpose()
    .znedi3.nnedi3(field=0, dh=True, nsize=4, nns=3)
    .std.Transpose()
)
dehalomask = fine_dehalo(doubledh, show_mask=True).resize.Bicubic(1920, 1080)
dehalomask2 = dehalomask.std.BoxBlur()

dehalo = dehalo_sigma(
    doubledh, brightstr=1, blur_func=Prefilter.GAUSSBLUR2(sigma=1.65)
).resize.Point(1920, 1080)
dehalo = core.std.MaskedMerge(aagrained, dehalo, dehalomask2)

dehalograin = core.grain.Add(dehalo, seed=1, var=1.00, uvar=0.0, constant=True)
dehalograined = core.std.MaskedMerge(aagrained, dehalograin, dehalo)

###CHROMA
merge = core.std.ShufflePlanes([dehalograined, bit], [0, 1, 2], vs.YUV)
# cden = core.knlm.KNLMeansCL(merge, d = 4, a = 4, s = 3, h = 0.25, channels = 'uv')
sloc = [0, 0, 0.4, 1, 0.45, 3, 0.5, 5, 1, 32]
denoise = core.dfttest.DFTTest(merge, tbsize=1, slocation=sloc)
dehalo_mask = (
    core.tcanny.TCanny(get_y(denoise), 1.5, 1.5, op=2, mode=1, scale=1.25)
    .std.Binarize(5000)
    .std.Maximum()
)
merge_mask = core.std.MaskedMerge(merge, denoise, dehalo_mask)
deband = masked_f3kdb(merge_mask, rad=20, thr=[28, 24], grain=[24, 12])
grain = adaptive_grain(deband, 0.8)


###OUTPUT
out = depth(grain, 10)
merge = depth(merge, 10)
set_output(src, "JPBD")
set_output(out, "filtering")
set_output(merge, "merge")
