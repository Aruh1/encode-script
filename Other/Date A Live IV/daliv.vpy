from polofunc import nnedi3
from vstools import core, set_output, initialize_clip, finalize_clip
from vsdenoise import BM3DCPU, Profile
from vsrgtools import contrasharpening
from kagefunc import adaptive_grain, retinex_edgemask
from vsdeband import F3kdb
from vspreview  import is_preview

core.max_cache_size = 1024 * 2

src = core.lsmas.LWLibavSource(r"00004.m2ts")
src = initialize_clip(src, 16)

denoise = BM3DCPU.denoise(
    src, 1, 1, profile=Profile.LOW_COMPLEXITY
)

contrasharpen = contrasharpening(denoise, src)

aa = nnedi3(contrasharpen, opencl=False)
mask_deband = retinex_edgemask(aa, sigma=1)

f3k = F3kdb.deband(contrasharpen)

debanded = core.std.MaskedMerge(f3k, contrasharpen, mask_deband)

grain = adaptive_grain(debanded, 0.2)

final = finalize_clip(grain, 10)

set_output(final)

# if is_preview:
#     set_output(src, "src")
#     set_output(final, "filtering")
#     set_output(mask_deband)
# else:
#     set_output(final)