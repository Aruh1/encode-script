from pathlib import Path

from kagefunc import adaptive_grain
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import smooth_dering
from vsdenoise import BM3DCPU, Profile
from vskernels import Bilinear, Hermite
from vsmuxtools import (
    FLAC,
    Resample,
    Setup,
    VideoFile,
    do_audio,
    mux,
    settings_builder_x265,
    src_file,
    x265,
)
from vspreview import is_preview
from vstools import Sar, core, finalize_clip, set_output

core.max_cache_size = 1024 * 30

source = src_file(r"00004.m2ts", force_lsmas=True)
src = source.init_cut()

descale = DescaleTarget(
    height=837.3,
    base_height=840,
    kernel=Bilinear,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
)
rescale = descale.get_upscaled(src)

denoise = BM3DCPU.denoise(rescale, 0.6, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))
sar = Sar(1, 1).apply(aa)
smooth = smooth_dering(sar)

mask_deband = deband_detail_mask(smooth)
f3k = F3kdb.deband(smooth)
debanded = core.std.MaskedMerge(f3k, smooth, mask_deband)

grain = adaptive_grain(debanded, 0.4)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "JPBD")
    set_output(rescale)
    set_output(final, "filter")
else:
    setup = Setup("01")
    settings = settings_builder_x265(
        preset="veryslow",
        crf=13,
        qcomp=0.75,
        bframes=12,
        rd=3,
        rect=False,
        ref=5,
        limit_refs=1,
        merange=57,
    )
    encoded = Path(setup.work_dir).joinpath("encoded.265").resolve()
    video_hevc = (
        VideoFile(encoded)
        if encoded.exists()
        else x265(
            settings,
            qp_clip=src,
        ).encode(final)
    )

    audio = do_audio(
        source,
        track=0,
        encoder=FLAC(preprocess=Resample(depth=None)),
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track("FLAC 2.0", "jpn", default=True, forced=False),
    )
