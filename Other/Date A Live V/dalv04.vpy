from pathlib import Path

from kagefunc import adaptive_grain
from vsaa import Eedi3, fine_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdenoise import BM3DCPU, Profile
from vsmuxtools import (
    GlobSearch,
    Setup,
    VideoFile,
    do_audio,
    mux,
    settings_builder_x265,
    src_file,
    x265,
)
from vspreview import is_preview
from vstools import (
    Sar,
    core,
    finalize_clip,
    set_output,
)

eps = "04"
dirsource = r"D:\Downloads"
core.max_cache_size = 1024 * 40

sourcesrc = GlobSearch(f"*Date* - {eps}*.mkv", dir=dirsource)

source = src_file(
    sourcesrc,
    force_lsmas=True,
)
src = source.init_cut()

# Native resolution is 864p, but nevertheless it's not descaleable.

denoise = BM3DCPU.denoise(src, 0.8, 3, profile=Profile.LOW_COMPLEXITY)

aa = fine_aa(denoise, taa=False, singlerater=Eedi3())
sar = Sar(1, 1).apply(aa)

mask_deband = deband_detail_mask(sar)
f3k = F3kdb.deband(sar)
debanded = core.std.MaskedMerge(f3k, sar, mask_deband)

grain = adaptive_grain(debanded, 0.2)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "CR")
    set_output(aa)
    set_output(final, "filter")
else:
    setup = Setup(
        eps,
        None,
        allow_binary_download=False,
        mkv_title_naming="$show$ - $ep$",
        out_dir="output",
        out_name="[premux] $show$ - $ep$ (WEBRip 1920x1080 HEVC AAC) [#crc32#]",
        show_name="Date A Live V",
    )
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
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
    )
