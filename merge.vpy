import math

from vsdenoise import frequency_merge
from vsmasktools import FreyChen
from vstools import core, finalize_clip, get_y, initialize_clip, set_output, vs


def ChangeFPS(clip: vs.VideoNode, fpsnum: int, fpsden: int = 1) -> vs.VideoNode:
    if not isinstance(clip, vs.VideoNode):
        raise vs.Error("ChangeFPS: this is not a clip")

    factor = (fpsnum / fpsden) * (clip.fps_den / clip.fps_num)

    def frame_adjuster(n: int) -> vs.VideoNode:
        real_n = math.floor(n / factor)
        one_frame_clip = clip[real_n] * (len(clip) + 100)
        return one_frame_clip

    attribute_clip = clip.std.BlankClip(
        length=math.floor(len(clip) * factor), fpsnum=fpsnum, fpsden=fpsden
    )
    return attribute_clip.std.FrameEval(eval=frame_adjuster)


sourceamzn = core.lsmas.LWLibavSource(
    r"D:\Download\[Ioroid] Yoru no Kurage wa Oyogenai - 01 [AMZN WEB-DL 1080p AVC E-AC3].mkv"
)
depthamzn = initialize_clip(sourceamzn, 16)

sourceadn = core.lsmas.LWLibavSource(
    r"D:\Download\Jellyfish Cant Swim in the Night S01E01 VOSTFR 1080p WEB x264 AAC -Tsundere-Raws (ADN).mkv"
)
# fps = ChangeFPS(sourceamzn, sourcecr.fps_num, sourcecr.fps_den)
depthadn = initialize_clip(sourceadn, 16)

freq = frequency_merge([depthadn, depthamzn], mode_high=depthadn, mode_low=depthamzn)

mask = (
    FreyChen().edgemask(get_y(depthamzn)).std.Binarize(25 << 7).std.Convolution([1] * 9)
)
merge = core.std.MaskedMerge(depthamzn, depthamzn, mask)

final = finalize_clip(merge, 10)
final1 = finalize_clip(freq, 10)

set_output(sourceamzn)
set_output(sourceadn)
set_output(final, "merge with mask")
set_output(final1, "freq")
