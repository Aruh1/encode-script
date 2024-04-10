"""vspipe hoshikuzu.vpy -c y4m - | x265-x64-v3.5+131-aMod-gcc13.1.0-opt-znver4.exe --y4m - --fps 24000/1001 --preset veryslow --profile main10 --output-depth 10 --input-depth 10 --crf 13 --no-cutree --no-sao --no-sao-non-deblock --keyint 240 --bframes 12 --psy-rd 2 --psy-rdoq 2.0 --aq-mode 3 --aq-strength 0.75 --ref 5 --rd 3 --subme 5 --qcomp 0.75 --colorprim bt709 --transfer bt709 --colormatrix bt709 --cbqpoffs -2 --crqpoffs -2 --tu-intra-depth 2 --tu-inter-depth 2 --sar 1 --no-rect --no-amp --no-tskip --b-intra --weightb --rskip 0 --no-strong-intra-smoothing --no-open-gop --deblock=-2:-2 --rc-lookahead 60 --limit-refs 1 --min-luma 64 --max-luma 940 --range limited --output "hoshikuzu.hevc"""

from kagefunc import adaptive_grain
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdenoise import BM3DCPU, Profile
from vstools import ChromaLocation, core, finalize_clip, initialize_clip, set_output

core.max_cache_size = 1024 * 7

source = core.lsmas.LWLibavSource(
    r"D:\Download\[SubsPlease] Hoshikuzu Telepath - 01 (1080p) [0C109EDF].mkv"
)
src = initialize_clip(source, 16)

# Native resolution is ~900p, but nevertheless it's not descaleable.

denoise = BM3DCPU.denoise(src, 1, 3, profile=Profile.LOW_COMPLEXITY)
denoised_luma = ChromaLocation.ensure_presence(
    denoise, ChromaLocation.from_video(src, strict=True)
)

aa = transpose_aa(denoised_luma, Eedi3(opencl=False))

mask_deband = deband_detail_mask(aa)
f3k = F3kdb.deband(aa)
debanded = core.std.MaskedMerge(f3k, aa, mask_deband)

grain = adaptive_grain(debanded, 0.4)

final = finalize_clip(grain, 10, False)

set_output(source)
set_output(final)
