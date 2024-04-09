from fractions import Fraction
from pathlib import Path

from kagefunc import adaptive_grain
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdenoise import BM3DCPU, Profile
from vskernels import Bilinear, Hermite
from vsmuxtools import (
    Chapters,
    Setup,
    SubFile,
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

source = src_file(
    r"C:\Users\samehadaku\Downloads\[SubsPlease] Dainanaoji - 02 (1080p) [DF639DB0].mkv",
    force_lsmas=True,
)
src = source.init_cut()

descale = DescaleTarget(
    height=900,
    kernel=Bilinear,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
)
rescale = descale.get_upscaled(src)

denoise = BM3DCPU.denoise(rescale, 0.6, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))
sar = Sar(1, 1).apply(aa)

mask_deband = deband_detail_mask(sar)
f3k = F3kdb.deband(sar)
debanded = core.std.MaskedMerge(f3k, sar, mask_deband)

grain = adaptive_grain(debanded, 0.4)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "TV")
    set_output(rescale)
    set_output(final, "filter")
else:
    setup = Setup("02")
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

    durandalsub = SubFile(
        r"./sub/[DurandalSubs] Dainanaoji - 02 [1080p][7D3DCAEA]_Subtitles01.IND.ass"
    )

    fonts = durandalsub.collect_fonts(
        use_system_fonts=False,
        additional_fonts=r"./sub/[DurandalSubs] Dainanaoji - 02 [1080p][7D3DCAEA]_Attachments",
    )

    chapters = Chapters(
        [
            (0, "Prolog"),
            (1272, "Lagu Pembuka"),
            (3429, "Bagian 1"),
            (13088, "Cuplikan 1"),
            (14124, "Eyecatch"),
            (14244, "Bagian 2"),
            (30186, "Lagu Penutup"),
            (32345, "Cuplikan 2"),
            (33927, "Selanjutnya"),
        ],
        Fraction(final.fps_num, final.fps_den),
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
        durandalsub.to_track("Durandal", lang="id", default=True, forced=False),
        *fonts,
        chapters,
    )
