from descale_analysis import test_descale_error
from vskernels import Bicubic
from vstools import core, depth

src = core.lsmas.LWLibavSource(
    r"C:\Users\Administrator\Desktop\[SubsPlease] Suki na Ko ga Megane wo Wasureta - 02 (1080p) [DAB31E48].mkv"
)

kernelres0 = dict(width=1920, height=1080, fractional=719.8, kernel=Bicubic(0, 1 / 2))
test = test_descale_error(src, kernelres0)
test.set_output()
