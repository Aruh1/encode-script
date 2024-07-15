from pathlib import Path

from vodesfunc import VMDegrain, adaptive_grain, ntype4
from vsaa import fine_aa
from vsdeband import masked_deband
from vsmasktools import HardsubSign
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
from vstools import Keyframes, core, finalize_clip, replace_ranges, set_output

eps = "07"
dirsource = r"D:\tongren"

core.max_cache_size = 1024 * 40

rangets = [(1486, 1557), (1815, 1920), (3705, 3764)]
rangehard = [(11506, 11756), (12092, 12133), (14639, 14726), (18332, 18640)]

crjp = src_file(
    GlobSearch(
        f"*DEAD*DESTRUCTION*S01E{eps}*VARYG.mkv",
        dir=dirsource,
    ),
    force_bs=True,
)
src = crjp.init_cut()
crhard = src_file(
    GlobSearch(
        f"*Yameii*DEAD DEAD DEMONS DEDEDEDE DESTRUCTION - S01E{eps}*.mkv",
        dir=dirsource,
    ),
    force_bs=True,
)
ref = crhard.init_cut()

keyframes = Path("./").joinpath(f"{eps}.txt").resolve()
if keyframes.exists():
    None
else:
    Keyframes.from_clip(src).to_file(f"{eps}.txt")

rfsts = replace_ranges(src, ref, rangets)

dehardsub = HardsubSign(rangehard).apply_dehardsub(rfsts, ref)

denoise = VMDegrain(dehardsub, thSAD=100, prefilter=12)

aa = fine_aa(denoise, taa=True)

deband = masked_deband(aa)

grain = adaptive_grain(
    deband, strength=[1.9, 0.4], size=3.3, temporal_average=50, seed=217404, **ntype4
)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "CR")
    set_output(ref, "CReng")
    # set_output(rfsts, "rfsts")
    set_output(dehardsub, "dehardsub")
    set_output(final, "filter")
else:
    setup = Setup(
        eps,
        None,
        allow_binary_download=False,
        mkv_title_naming="$show$ - $ep$",
        out_dir="output",
        out_name="[premux] $show$ - $ep$ (WEBRip 1920x1080 HEVC AAC) [#crc32#]",
        show_name="DEAD DEAD DEMONS DEDEDEDE DESTRUCTION",
    )
    settings = settings_builder_x265(
        preset="placebo",
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
        crjp,
        track=0,
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
    )
