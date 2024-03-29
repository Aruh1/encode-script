"""vspipe sukimega.vpy -c y4m - | x265-x64-v3.5+131-aMod-gcc13.1.0-opt-znver4.exe --y4m - --fps 24000/1001 --preset veryslow --profile main10 --output-depth 10 --input-depth 10 --crf 13 --no-cutree --no-sao --no-sao-non-deblock --keyint 240 --bframes 12 --psy-rd 2 --psy-rdoq 2.0 --aq-mode 3 --aq-strength 1.00 --ref 5 --rd 3 --subme 5 --qcomp 0.73 --colorprim bt709 --transfer bt709 --colormatrix bt709 --cbqpoffs -2 --crqpoffs -2 --tu-intra-depth 2 --tu-inter-depth 2 --sar 1 --no-rect --no-amp --no-tskip --b-intra --weightb --rskip 0 --no-strong-intra-smoothing --no-open-gop --deblock=-2:-2 --rc-lookahead 60 --limit-refs 1 --min-luma 64 --max-luma 940 --range limited --output "sukimega.hevc"""

from vstools import core, set_output, initialize_clip, finalize_clip
from awsmfunc import bbmod
from vsdenoise import BM3DCPU, Profile
from vspreview import is_preview
from vsdeband import F3kdb
from kagefunc import adaptive_grain, retinex_edgemask
from polofunc import nnedi3
from vsdehalo import smooth_dering

core.max_cache_size = 1024 * 2

tv = core.lsmas.LWLibavSource(
    r"00007.m2ts"
)
src = initialize_clip(tv, 16)

edgefix = bbmod(src, 1, 1, 1, 1, 30)

# descale = DescaleTarget(height=810, kernel=Bilinear,upscaler=NNEDI_Doubler(opencl=False)).generate_clips(src)
# rescaled = descale.get_upscaled(src)

denoise = BM3DCPU.denoise(
    edgefix, 1, 1, profile=Profile.LOW_COMPLEXITY
)

aa = nnedi3(denoise, opencl=False)
dering = smooth_dering(aa, mrad=3, msmooth=1, minp=1, mthr=0.20, darkthr=0, contra=0)

mask_deband = retinex_edgemask(dering, sigma=1)
f3k = F3kdb.deband(dering)
debanded = core.std.MaskedMerge(f3k, denoise, mask_deband)

grain = adaptive_grain(debanded, 0.8)

out = finalize_clip(grain, 10)

set_output(out)

# if is_preview():
#     set_output(tv, "src")
#     set_output(out, "filtering")
# else:
#     set_output(out)