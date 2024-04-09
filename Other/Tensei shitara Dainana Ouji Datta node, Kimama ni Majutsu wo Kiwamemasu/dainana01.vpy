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
    r"D:\Downloads\torrent\I.Was.Reincarnated.as.the.7th.Prince.so.I.Can.Take.My.Time.Perfecting.My.Magical.Ability.S01E01.I.Reincarnated.as.the.Seventh.Prince.1080p.CR.WEB-DL.AAC2.0.H.264-VARYG.mkv",
    force_lsmas=True,
)
src = source.init_cut()

testdescale = core.descale.Debilinear(src, 1600, 900)

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
    set_output(testdescale, "descale")
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
    )

    durandalsub = SubFile(
        r"./sub/[DurandalSubs] Dainanaoji - 01 [1080p][911D1DAF]_Subtitles01.IND.ass"
    )

    fonts = durandalsub.collect_fonts(
        use_system_fonts=False,
        additional_fonts=r"./sub/[DurandalSubs] Dainanaoji - 01 [1080p][911D1DAF]_Attachments",
    )

    chapters = Chapters(
        [
            (0, "Prolog"),
            (4149, "Lagu Pembuka"),
            (6306, "Bagian 1"),
            (17527, "Eyecatch"),
            (17647, "Bagian 2"),
            (31769, "Lagu Penutup"),
            (33927, "Cuplikan"),
        ],
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
        durandalsub.to_track("Durandal", lang="id", default=True, forced=False),
        *fonts,
        chapters,
    )
