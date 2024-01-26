from vsmuxtools import src_file, x265, settings_builder_x265, FFMpeg, src_file, mux
from vstools import core, set_output, finalize_clip, replace_ranges
from vspreview import is_preview
from vsdenoise import BM3DCPU, Profile
from kagefunc import retinex_edgemask
from vsrgtools import contrasharpening
from vsdeband import F3kdb
from kagefunc import adaptive_grain
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vskernels import Bilinear, Gaussian
from polofunc import nnedi3
from vsdehalo import fine_dehalo2

core.max_cache_size = 1024 * 2

op = ([2877, 5035])
ed = ([])

source = src_file(r"D:\00004.m2ts", force_lsmas=True)
src = source.init_cut()

descale = DescaleTarget(height=720, kernel=Bilinear, upscaler=NNEDI_Doubler(opencl=False), downscaler=Gaussian(linear=True))
rescale = descale.get_upscaled(src)

reprangesop = replace_ranges(src, rescale, op)

denoise= BM3DCPU.denoise(reprangesop, 1, 1, profile=Profile.LOW_COMPLEXITY)
dehalo = fine_dehalo2(denoise)
reprangesdehalo = replace_ranges(denoise, dehalo, op)

constasharpen = contrasharpening(reprangesdehalo, reprangesop)

mask_deband = retinex_edgemask(constasharpen, sigma=1)
deband = F3kdb.deband(constasharpen)
debanded = core.std.MaskedMerge(deband, constasharpen, mask_deband)

grain = adaptive_grain(debanded, 0.8)
output = finalize_clip(debanded, bits=10)

if __name__ == "__main__":
    settings = settings_builder_x265(preset='veryslow', crf=13, psy_rd=2.05, psy_rdoq=2.15, qcomp=0.73, aq_strength=0.85, rect=False)

    video_hevc = x265(settings, qp_clip=source, resumable=True).encode(output)
    
    audio = FFMpeg.Extractor(track=1).extract_audio(source.file)

    mux(
    video_hevc.to_track(default=True),
    audio.to_track(lang="ja", default=True)
    )
else:
    set_output(src, "source")
    set_output(rescale, "rescale")
    set_output(output, "Filtered")