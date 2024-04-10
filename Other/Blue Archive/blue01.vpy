from pathlib import Path

from kagefunc import adaptive_grain
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import edge_cleaner, fine_dehalo
from vsdenoise import BM3DCPU, Profile
from vskernels import Bilinear, Hermite
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
from vsrgtools import contrasharpening_dehalo
from vstools import (
    Sar,
    core,
    finalize_clip,
    set_output,
)

core.max_cache_size = 1024 * 30

sourceamzn = src_file(
    r"D:\Downloads\Blue Archive The Animation - S01E01 - 1080p WEB H.264 -NanDesuKa (AMZN).mkv",
    force_lsmas=True,
)
srcamzn = sourceamzn.init_cut()

sourceabm = src_file(
    r"D:\Downloads\[Ioroid] Blue Archive the Animation - 01 [ABEMA WEB-DL 1080p AVC AAC].mkv",
    force_lsmas=True,
)
srcabm = sourceabm.init_cut()

descale = DescaleTarget(
    height=720,
    kernel=Bilinear,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
    border_handling=1,
)
rescale = descale.get_upscaled(srcabm)

denoise = BM3DCPU.denoise(rescale, 0.6, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))
sar = Sar(1, 1).apply(aa)

dehalo = fine_dehalo(sar, 2.2, 2.2, brightstr=1, darkstr=0)
dehalo_mask = fine_dehalo(sar, 2.2, 2.2, brightstr=1, darkstr=0, show_mask=True)
edgeclean = edge_cleaner(dehalo, 7, False)
edgeclean = core.std.MaskedMerge(dehalo, edgeclean, dehalo_mask)
contra = contrasharpening_dehalo(edgeclean, dehalo)

mask_deband = deband_detail_mask(contra)
f3k = F3kdb.deband(contra)
debanded = core.std.MaskedMerge(f3k, contra, mask_deband)

grain = adaptive_grain(debanded, 0.4)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(srcamzn, "AMZN")
    set_output(srcabm, "Abema")
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
            qp_clip=srcabm,
        ).encode(final)
    )

    audio = do_audio(
        sourceamzn,
        track=0,
    )

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track(lang="jpn", default=True, forced=False),
    )
