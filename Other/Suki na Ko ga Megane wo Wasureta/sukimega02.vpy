from vstools import core, set_output, vs
from vsutil import depth, get_y
from awsmfunc import bbmod
from vsdenoise import MVTools, SADMode, MotionMode, Prefilter, BM3DCPU, Profile, nl_means
from vspreview import is_preview
from vsdehalo import fine_dehalo, smooth_dering, dehalo_sigma
from vsdeband import masked_deband
from kagefunc import adaptive_grain
from vsaa import Nnedi3, fine_aa
from vsrgtools import bilateral

core.max_cache_size = 1024 * 2

tv = core.lsmas.LWLibavSource(
    r"C:\Users\Administrator\Desktop\[SubsPlease] Suki na Ko ga Megane wo Wasureta - 02 (1080p) [DAB31E48].mkv"
)
src = depth(tv, 16)

edgefix = bbmod(src, 1, 1, 1, 1, 30)


ref = MVTools.denoise(
    edgefix, thSAD=100, block_size=32, overlap=16,
    motion=MotionMode.HIGH_SAD,
    prefilter=Prefilter.DFTTEST,
    sad_mode=(
        SADMode.ADAPTIVE_SPATIAL_MIXED,
        SADMode.ADAPTIVE_SATD_MIXED,
    )
)
denoise = BM3DCPU.denoise(
    edgefix, sigma=0.8, tr=2, profile=Profile.LOW_COMPLEXITY, ref=ref, planes=0
)
denoise = nl_means(denoise, tr=2, strength=0.8, ref=ref, planes=[1, 2])

aa = fine_aa(denoise, taa=True)

# dering = smooth_dering(aa, mrad=4, msmooth=1, minp=1, mthr=0.16, darkthr=0, contra=0)

dh_sigma = dehalo_sigma(aa, blur_func=Prefilter.GAUSSBLUR2, pre_ss=2)
dh_bil = bilateral(edgefix, sigmaS=1.5, ref=dh_sigma, planes=0)
dh = core.akarin.Expr([src, dh_bil, dh_sigma], "x y z max min")

dh_masked = fine_dehalo.mask(aa, dh, thmi=80, thma=110, rx=2.0)

deband = masked_deband(dh_masked)

grain = adaptive_grain(deband, 0.8)

out = depth(grain, 10)

if is_preview():
    set_output(tv, "src")
    set_output(out, "filtering")
#     set_output(deband, "debanding")
#     set_output(aa, "aa")
else:
    set_output(out)