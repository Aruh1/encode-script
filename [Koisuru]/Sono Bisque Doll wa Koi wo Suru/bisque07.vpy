from pathlib import Path

from kagefunc import adaptive_grain, squaremask
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import edge_cleaner, fine_dehalo
from vsdenoise import BM3DCPU, Profile
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
from vsrgtools import contrasharpening_dehalo
from vstools import Sar, core, finalize_clip, set_output
from vstools import replace_ranges as rfs

core.max_cache_size = 1024 * 30

source = src_file(r"00004.m2ts", trim=(None, 34046), force_lsmas=True)
src = source.init_cut()

cden = rfs(
    src,
    src.std.MaskedMerge(
        src[18179] * src.num_frames, squaremask(src, 1044, 1080, 876, 0)
    ),
    (18179, 18387),
)

denoise = BM3DCPU.denoise(cden, 0.75, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))

dehalo = fine_dehalo(aa, 2.2, 2.2, brightstr=1, darkstr=0)
dehalo_mask = fine_dehalo(aa, 2.2, 2.2, brightstr=1, darkstr=0, show_mask=True)
edgeclean = edge_cleaner(dehalo, 7, False)
edgeclean = core.std.MaskedMerge(dehalo, edgeclean, dehalo_mask)
contra = contrasharpening_dehalo(edgeclean, dehalo)
sar = Sar(1, 1).apply(contra)

mask_deband = deband_detail_mask(sar)
f3k = F3kdb.deband(sar)
debanded = core.std.MaskedMerge(f3k, sar, mask_deband)

grain = adaptive_grain(debanded, 0.4)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "JPBD")
    set_output(final, "filter")
else:
    setup = Setup("06")
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
        min_luma=64,
        max_luma=940,
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
