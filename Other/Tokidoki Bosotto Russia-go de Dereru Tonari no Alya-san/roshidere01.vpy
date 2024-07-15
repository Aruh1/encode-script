from pathlib import Path

from vodesfunc import VMDegrain, adaptive_grain
from vsaa import fine_aa
from vsdeband import masked_deband
from vskernels import Point
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
from vssource import IMWRI
from vstools import (
    Keyframes,
    Matrix,
    core,
    finalize_clip,
    get_y,
    replace_ranges,
    set_output,
)

eps = "01"
dirsource = r"D:\tongren"

core.max_cache_size = 1024 * 40

sourcesrc = GlobSearch(
    f"*Tokidoki Bosotto Russia-go de Dereru Tonari no Alya-san - {eps} (1080p)*.mkv",
    dir=dirsource,
)

sourceamzn = GlobSearch(
    f"Alya Sometimes Hides Her Feelings in Russian S01E{eps}*(AMZN).mkv", dir=dirsource
)

source = src_file(sourcesrc, force_bs=True)
src = source.init_cut()
amznsource = src_file(sourceamzn, force_bs=True)
srcamzn = amznsource.init_cut()

keyframes = Path("./").joinpath(f"{eps}.txt").resolve()
if keyframes.exists():
    None
else:
    Keyframes.from_clip(src).to_file(f"{eps}.txt")

freezeschool = core.std.FreezeFrames(
    src, first=[28123], last=[28233], replacement=[28122]
)

mlaku = replace_ranges(
    freezeschool,
    freezeschool.std.MaskedMerge(
        freezeschool[28234] * freezeschool.num_frames,
        get_y(freezeschool)
        .std.BlankClip()
        .sub.Subtitle("{\an7\pos(0,0)\p1}m 0 700 l 1920 700 1920 1080 0 1080")
        .std.BinarizeMask(),
    ),
    (28235, 28440),
)

Gambar = IMWRI.source("./assets/01/clean.png")
Gambar = Gambar * freezeschool.num_frames
Gambar = core.std.AssumeFPS(Gambar, fpsnum=24000, fpsden=1001)
Gambar = Point.resample(Gambar, format=src.format, matrix=Matrix.from_video(src))

clean = replace_ranges(
    mlaku,
    mlaku.std.MaskedMerge(
        Gambar,
        get_y(Gambar)
        .std.BlankClip()
        .sub.Subtitle("{\an7\pos(0,0)\p1}m 790 990 l 1920 990 1920 1080 790 1080")
        .std.BinarizeMask(),
    ),
    (28234, 28440),
)

tenmin = core.std.FreezeFrames(clean, first=[31167], last=[31205], replacement=[31166])

dns = VMDegrain(tenmin, thSAD=80, prefilter=4)

aa = fine_aa(dns, taa=True)

deband = masked_deband(aa)

grain = adaptive_grain(deband)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "CR")
    # set_output(srcamzn, "AMZN")
    set_output(freezeschool, "freeze")
    set_output(mlaku, "mlaku")
    set_output(clean, "clean")
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
