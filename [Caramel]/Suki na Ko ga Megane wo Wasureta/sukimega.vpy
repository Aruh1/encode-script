"""vspipe sukimega.vpy -c y4m - | x265-x64-v3.5+131-aMod-gcc13.1.0-opt-znver4.exe --y4m - --fps 24000/1001 --preset veryslow --profile main10 --output-depth 10 --input-depth 10 --crf 13 --no-cutree --no-sao --no-sao-non-deblock --keyint 240 --bframes 12 --psy-rd 2 --psy-rdoq 2.0 --aq-mode 3 --aq-strength 0.75 --ref 5 --rd 3 --subme 5 --qcomp 0.75 --colorprim bt709 --transfer bt709 --colormatrix bt709 --cbqpoffs -2 --crqpoffs -2 --tu-intra-depth 2 --tu-inter-depth 2 --sar 1 --no-rect --no-amp --no-tskip --b-intra --weightb --rskip 0 --no-strong-intra-smoothing --no-open-gop --deblock=-2:-2 --rc-lookahead 60 --limit-refs 1 --min-luma 64 --max-luma 940 --range limited --output "sukimega.hevc"""

from awsmfunc import bbmod
from kagefunc import adaptive_grain
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import dehalomicron
from vsdenoise import BM3DCPU, Prefilter, Profile
from vstools import core, finalize_clip, initialize_clip, set_output

core.max_cache_size = 1024 * 30

source = core.lsmas.LWLibavSource(r"C:\Users\samehadaku\Downloads\00006.m2ts")
src = initialize_clip(source, 16)

edgefix = bbmod(src, 1, 1, 1, 1, 30)

denoise = BM3DCPU.denoise(edgefix, 1, 1, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))

dehaloed = dehalomicron(
    aa,
    brz=0.075,
    sigma=1.55,
    sigma0=1.15,
    dampen=(0.65, True),
    blur_func=Prefilter.GAUSSBLUR2,
)

mask_deband = deband_detail_mask(dehaloed)
f3k = F3kdb.deband(dehaloed)
debanded = core.std.MaskedMerge(f3k, dehaloed, mask_deband)

grain = adaptive_grain(debanded, 0.5)

out = finalize_clip(grain, 10)

set_output(out)
