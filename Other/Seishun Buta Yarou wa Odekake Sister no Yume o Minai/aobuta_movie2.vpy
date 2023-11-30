from havsfunc import SMDegrain
from kagefunc import adaptive_grain, inverse_scale
from polofunc import masked_f3kdb, nnedi3_rpow2
from vsdehalo import dehalo_sigma, fine_dehalo
from vsdenoise import Prefilter
from vstools import core, depth, get_y, set_output, vs

core.max_cache_size = 1024 * 2

###GETTING SOURCES
src = core.lsmas.LWLibavSource(r"C:\Users\Administrator\Desktop\[Ioroid] Seishun Buta Yarou wa Odekake Sister no Yume o Minai [AMZN WEB-DL 1080p AVC E-AC3].mkv")
bit = depth(src, 16)

###AA
scaled = inverse_scale(bit, height=878, mask_detail=True)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.GRAY16)

preden = SMDegrain(get_y(bit), tr = 2, thSAD = 120, RefineMotion = True, prefilter = 2)
mask = preden.std.Prewitt().std.Binarize(65 << 8)
aamask = mask.std.Inflate()
aamasked = core.std.MaskedMerge(get_y(bit), scaled, aamask)

grainmask1 = mask.std.Deflate().std.Deflate()
grainmask2 = core.std.Expr([aamask.std.Inflate(), grainmask1], "x y -").std.BoxBlur()

aagrain = core.grain.Add(aamasked, seed = 1, var = 0.70, uvar = 0.0, constant = True)
aagrained = core.std.MaskedMerge(aamasked, aagrain, grainmask2)


###DEHALO
doubledh = aagrained.znedi3.nnedi3(field=0, dh=True, nsize=4, nns=3).std.Transpose().znedi3.nnedi3(field=0, dh=True, nsize=4, nns=3).std.Transpose()
dehalomask = fine_dehalo(doubledh, show_mask=True).resize.Bicubic(1920, 1080)
dehalomask2 = dehalomask.std.BoxBlur()

dehalo = dehalo_sigma(doubledh, brightstr = 1, blur_func=Prefilter.GAUSSBLUR2(sigma = 1.65)).resize.Point(1920, 1080)
dehalo = core.std.MaskedMerge(aagrained, dehalo, dehalomask2)

dehalograin = core.grain.Add(dehalo, seed = 1, var = 1.50, uvar = 0.0, constant = True)
dehalograined = core.std.MaskedMerge(aagrained, dehalograin, dehalo)

###CHROMA
merge = core.std.ShufflePlanes([dehalograined, bit], [0,1,2], vs.YUV)
# cden = core.knlm.KNLMeansCL(merge, d = 4, a = 4, s = 3, h = 0.25, channels = 'uv')
sloc = [0, 0, 0.4, 1, 0.45, 3, 0.5, 5, 1, 32]
denoise = core.dfttest.DFTTest(merge, tbsize=1, slocation=sloc)
dehalo = fine_dehalo(denoise)
dehalo_mask = core.tcanny.TCanny(get_y(dehalo), 1.5, 1.5, op=2, mode=1, scale=1.25).std.Binarize(5000).std.Maximum()
merge_mask = core.std.MaskedMerge(denoise, dehalo, dehalo_mask)
cwarp = core.warp.AWarpSharp2(merge_mask, thresh=72, blur=3, type=1, depth=4, planes=[1, 2])
deband = masked_f3kdb(cwarp, rad=20, thr=[28, 24], grain=[24, 12])
grain = adaptive_grain(deband, 0.8)


###OUTPUT
out = depth(grain, 10)
set_output(src, "src")
set_output(out, "filtering")