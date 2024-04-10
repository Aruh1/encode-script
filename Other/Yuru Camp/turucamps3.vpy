from pathlib import Path

from kagefunc import adaptive_grain
from vsaa import Eedi3, Nnedi3, clamp_aa, transpose_aa, upscaled_sraa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import fine_dehalo
from vsdenoise import BM3DCPU, Profile
from vsmuxtools import (
    Setup,
    VideoFile,
    do_audio,
    mux,
    settings_builder_x265,
    src_file,
    x265,
)
from vspreview import is_preview
from vstools import core, finalize_clip, set_output

core.max_cache_size = 1024 * 30

sourcecr = src_file(
    r"C:\Users\samehadaku\Downloads\[SubsPlease] Yuru Camp S3 - 01 (1080p) [FDFCDDAA].mkv",
    force_lsmas=True,
)
srccr = sourcecr.init_cut()

denoise = BM3DCPU.denoise(srccr, 0.6, 3, profile=Profile.LOW_COMPLEXITY)

# aa = transpose_aa(denoise, Eedi3(opencl=False))
filt_aa_weak = transpose_aa(denoise, Nnedi3(opencl=False))
filt_aa_str = upscaled_sraa(
    denoise, ssfunc=Nnedi3(opencl=False), aafunc=Eedi3(opencl=False)
)
filt_aa = clamp_aa(denoise, filt_aa_weak, filt_aa_str)

filt_dehalo = fine_dehalo(filt_aa, darkstr=0.6)

mask_deband = deband_detail_mask(filt_dehalo)
f3k = F3kdb.deband(filt_dehalo, thr=45)
debanded = core.std.MaskedMerge(f3k, filt_dehalo, mask_deband)

grain = adaptive_grain(debanded)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(srccr, "TV")
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
            qp_clip=srccr,
        ).encode(final)
    )

    audio = do_audio(
        sourcecr,
        track=0,
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
    )
