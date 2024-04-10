from lvsfunc import get_match_centers_scaling
from vodesfunc import DescaleTarget, NNEDI_Doubler
from vskernels import Bilinear, Catrom, Hermite
from vsmuxtools import src_file
from vstools import core, replace_ranges, set_output

core.max_cache_size = 1024 * 30

source = core.lsmas.LWLibavSource(
    r"D:\Download\[Ioroid] Blue Archive the Animation - 01 [ABEMA WEB-DL 1080p AVC AAC].mkv"
)

source1 = src_file(
    r"D:\Download\[Ioroid] Blue Archive the Animation - 01 [ABEMA WEB-DL 1080p AVC AAC].mkv",
    force_lsmas=True,
)
src1 = source1.init_cut()

scale = get_match_centers_scaling(source, 1280, 720)

op = (30963, 33120)

descale = DescaleTarget(
    height=720,
    kernel=Bilinear,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
    border_handling=1,
)
rescale = descale.get_upscaled(src1)

tod = replace_ranges(src1, rescale, op)

descale1 = DescaleTarget(
    height=720,
    kernel=Catrom,
    upscaler=NNEDI_Doubler(opencl=False),
    downscaler=Hermite,
    border_handling=1,
)
rescale1 = descale1.get_upscaled(src1)

set_output(source)
set_output(scale)
set_output(rescale, "rescale Bilinear")
set_output(rescale1, "rescale Catrom")
