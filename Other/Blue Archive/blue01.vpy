from pathlib import Path
from typing import Any, Iterable

from kagefunc import adaptive_grain
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vsaa import Eedi3, transpose_aa
from vsdeband import F3kdb, deband_detail_mask
from vsdehalo import edge_cleaner, fine_dehalo
from vsdenoise import BM3DCPU, DFTTest, MVTools, Profile
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
from vsrgtools import MeanMode, contrasharpening_dehalo
from vstools import (
    CustomValueError,
    GenericVSFunction,
    KwargsT,
    PlanesT,
    Sar,
    core,
    fallback,
    finalize_clip,
    flatten_vnodes,
    get_video_format,
    normalize_seq,
    set_output,
    vs,
)


def frequency_merge(
    *_clips: vs.VideoNode | Iterable[vs.VideoNode],
    tr: int = 0,
    mode_high: MeanMode | vs.VideoNode = MeanMode.LEHMER,
    mode_low: MeanMode | vs.VideoNode = MeanMode.ARITHMETIC,
    mode_tr: MeanMode | None = None,
    lowpass: GenericVSFunction | list[GenericVSFunction] = DFTTest.denoise,
    mean_diff: bool = False,
    planes: PlanesT = None,
    mv_args: KwargsT | None = None,
    **kwargs: Any,
) -> vs.VideoNode:
    clips = flatten_vnodes(_clips)
    n_clips = len(clips)

    mv_args = mv_args or KwargsT()
    mode_tr = fallback(
        mode_tr, MeanMode.LEHMER if isinstance(mode_high, vs.VideoNode) else mode_high
    )

    if not lowpass:
        raise CustomValueError(
            "You must pass at least one lowpass filter!", frequency_merge
        )

    formats = {get_video_format(clip).id for clip in clips}

    if len(formats) > 1:
        raise CustomValueError("All clips must have the same format!", frequency_merge)

    blurred_clips = []
    for clip, filt in zip(clips, normalize_seq(lowpass, n_clips)):
        try:
            blurred_clips.append(
                clip if not filt else filt(clip, planes=planes, **kwargs)
            )
        except Exception:
            blurred_clips.append(clip if not filt else filt(clip, **kwargs))

    if isinstance(mode_low, vs.VideoNode):
        low_freqs = blurred_clips[clips.index(mode_low)]
    else:
        low_freqs = mode_low(blurred_clips)

    diffed_clips = []
    for clip, blur in zip(
        clips, normalize_seq(low_freqs if mean_diff else blurred_clips, n_clips)
    ):
        diffed_clips.append(None if clip == blur else clip.std.MakeDiff(blur))

    if isinstance(mode_high, vs.VideoNode):
        high_freqs = diffed_clips[clips.index(mode_high)]
    else:
        high_freqs = mode_high([clip for clip in diffed_clips if clip])

    if tr:
        mv = MVTools(clip, tr, **mv_args)
        mv.analyze()

        low_freqs = mv.degrain(ref=low_freqs)

        if mode_tr is MeanMode.ARITHMETIC:
            high_freqs = mv.degrain(ref=high_freqs)
        else:
            high_freqs = mv.compensate(mode_tr, ref=high_freqs)  # type: ignore

    return low_freqs.std.MergeDiff(high_freqs)


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

freq = frequency_merge([srcabm, srcamzn], mode_high=srcabm, mode_low=srcamzn)

descale = DescaleTarget(
    height=720,
    kernel=Bilinear,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
    border_handling=1,
)
rescale = descale.get_upscaled(freq)

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
    set_output(freq)
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
            qp_clip=srcamzn,
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
