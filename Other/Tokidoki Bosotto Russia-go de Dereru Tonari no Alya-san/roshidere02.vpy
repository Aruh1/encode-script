from pathlib import Path

from vodesfunc import VMDegrain, adaptive_grain, ntype4
from vsaa import fine_aa
from vsdeband import masked_deband
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
from vstools import Keyframes, core, finalize_clip, set_output

eps = "02"
dirsource = r"D:\tongren"

core.max_cache_size = 1024 * 40

sourcesrc = GlobSearch(
    f"*Tokidoki Bosotto Russia-go de Dereru Tonari no Alya-san - {eps} (1080p)*.mkv",
    dir=dirsource,
)

sourceamzn = GlobSearch(
    f"Alya Sometimes Hides Her Feelings in Russian S01E{eps}*(AMZN).mkv", dir=dirsource
)

source = src_file(sourcesrc, force_lsmas=True)
src = source.init_cut()
amznsource = src_file(sourceamzn, force_lsmas=True)
srcamzn = amznsource.init_cut()

keyframes = Path("./").joinpath(f"{eps}.txt").resolve()
if keyframes.exists():
    None
else:
    Keyframes.from_clip(src).to_file(f"{eps}.txt")

denoise = VMDegrain(src, thSAD=100, prefilter=12)

aa = fine_aa(denoise, taa=True)

deband = masked_deband(aa)

grain = adaptive_grain(
    deband, strength=[1.9, 0.4], size=3.3, temporal_average=50, seed=217404, **ntype4
)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "CR")
    set_output(srcamzn, "AMZN")
    set_output(final, "filter")
else:
    setup = Setup(
        eps,
        None,
        allow_binary_download=False,
        mkv_title_naming="$show$ - $ep$",
        out_dir="output",
        out_name="[premux] $show$ - $ep$ (WEBRip 1920x1080 HEVC E-AC-3) [#crc32#]",
        show_name="Tokidoki Bosotto Russia-go de Dereru Tonari no Alya-san",
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
        amznsource,
        track=0,
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
    )
