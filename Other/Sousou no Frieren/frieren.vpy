from vstools import core, set_output, finalize_clip, initialize_clip
from vspreview import is_preview
from vsdenoise import BM3DCPU, Profile
from kagefunc import retinex_edgemask
from vsdeband import F3kdb
from kagefunc import adaptive_grain
from polofunc import nnedi3

core.max_cache_size = 1024 * 16

src = core.lsmas.LWLibavSource(r"D:\00005.m2ts")
source = initialize_clip(src, 16)

denoise = BM3DCPU.denoise(
    source, 1, 1, profile=Profile.LOW_COMPLEXITY
)

aa = nnedi3(denoise, opencl=False)
debandmask = retinex_edgemask(aa)

deband = F3kdb.deband(denoise, 16, [144, 120, 120])
debanded = core.std.MaskedMerge(deband, denoise, debandmask)

grain = adaptive_grain(debanded, 0.8)
output = finalize_clip(grain, bits=10)

set_output(output)
