from vstools import core, finalize_clip, set_output, initialize_clip
from vspreview import is_preview
from vsdenoise import BM3DCPU, Profile
from kagefunc import retinex_edgemask
from vsrgtools import contrasharpening
from vsdeband import F3kdb
from kagefunc import adaptive_grain

core.max_cache_size = 1024 * 10

# note: tinggal ubah bagian ini aja
source = core.lsmas.LWLibavSource(r"D:\Download\[SubsPlease] Saijaku Tamer wa Gomi Hiroi no Tabi wo Hajimemashita - 01 (1080p) [3EEBBC73].mkv")
src = initialize_clip(source, 16)

denoise= BM3DCPU.denoise(src, 1, 1, profile=Profile.LOW_COMPLEXITY)
constasharpen = contrasharpening(denoise, src)

mask_deband = retinex_edgemask(constasharpen, sigma=1)
deband = F3kdb.deband(constasharpen)
debanded = core.std.MaskedMerge(deband, constasharpen, mask_deband)

grain = adaptive_grain(debanded, 0.8)
output = finalize_clip(grain, bits=10)

set_output(output)