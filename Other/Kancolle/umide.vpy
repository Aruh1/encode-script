# from vodesfunc import adaptive_grain, ntype4, set_output
from kagefunc import adaptive_grain
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdenoise import BM3DCPU, Profile
from vstools import core, finalize_clip, initialize_clip, set_output

core.max_cache_size = 1024 * 2

source = core.lsmas.LWLibavSource(r"D:\00002.m2ts")
src = initialize_clip(source, 16)

# Native resolution is ~900p, but nevertheless it's not descaleable.

denoise = BM3DCPU.denoise(src, 1, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))

mask_deband = deband_detail_mask(aa)
f3k = F3kdb.deband(aa)
debanded = core.std.MaskedMerge(f3k, aa, mask_deband)

grained = adaptive_grain(debanded)

final = finalize_clip(grained, 10, False)

set_output(source)
set_output(final)
