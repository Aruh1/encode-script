"""vspipe bisque03.vpy -c y4m - | x265-x64-v3.5+131-aMod-gcc13.1.0-opt-znver4.exe --y4m - --fps 24000/1001 --preset veryslow --profile main10 --output-depth 10 --input-depth 10 --crf 13 --no-cutree --no-sao --no-sao-non-deblock --keyint 240 --bframes 12 --psy-rd 2 --psy-rdoq 2.0 --aq-mode 3 --aq-strength 0.75 --ref 5 --rd 3 --subme 5 --qcomp 0.75 --colorprim bt709 --transfer bt709 --colormatrix bt709 --cbqpoffs -2 --crqpoffs -2 --tu-intra-depth 2 --tu-inter-depth 2 --sar 1 --no-rect --no-amp --no-tskip --b-intra --weightb --rskip 0 --no-strong-intra-smoothing --no-open-gop --deblock=-2:-2 --rc-lookahead 60 --limit-refs 1 --min-luma 64 --max-luma 940 --range limited --output "bisque.hevc"""

from pathlib import Path

from kagefunc import adaptive_grain
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import edge_cleaner, fine_dehalo
from vsdenoise import BM3DCPU, Profile
from vsmuxtools import (
    FLAC,
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
from vstools import core, finalize_clip, set_output

core.max_cache_size = 1024 * 30

source = src_file(r"", trim=(0, 34047), force_lsmas=True)
src = source.init_cut()

denoise = BM3DCPU.denoise(src, 0.75, 3, profile=Profile.LOW_COMPLEXITY)

aa = transpose_aa(denoise, Eedi3(opencl=False))

mask_deband = deband_detail_mask(aa)
f3k = F3kdb.deband(aa)
debanded = core.std.MaskedMerge(f3k, aa, mask_deband)

dehalo = fine_dehalo(debanded, 2.2, 2.2, brightstr=1, darkstr=0)
dehalo_mask = fine_dehalo(debanded, 2.2, 2.2, brightstr=1, darkstr=0, show_mask=True)
edgeclean = edge_cleaner(dehalo, 7, False)
edgeclean = core.std.MaskedMerge(dehalo, edgeclean, dehalo_mask)
contra = contrasharpening_dehalo(edgeclean, dehalo)

grain = adaptive_grain(contra, 0.4)

final = finalize_clip(grain, 10, False)

if is_preview():
    set_output(src, "JPBD")
    set_output(final, "filter")
else:
    setup = Setup("03")
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

    # Audio
    audio = do_audio(source, track=0, encoder=FLAC(), quite=True)

    mux(
        video_hevc.to_track(lang="jpn", default=True, forced=False),
        audio.to_track("FLAc 2.0", "jpn", default=True, forced=False),
    )
