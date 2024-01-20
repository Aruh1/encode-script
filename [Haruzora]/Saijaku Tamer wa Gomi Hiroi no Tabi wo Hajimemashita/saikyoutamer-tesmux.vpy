from vsmuxtools import src_file, x265, settings_builder_x265, FFMpeg, src_file, mux
from vstools import vs, core, finalize_clip
from vstools import core, set_output, finalize_clip
from vspreview import is_preview
from vsdenoise import BM3DCPU, Profile
from kagefunc import retinex_edgemask
from vsrgtools import contrasharpening
from vsdeband import F3kdb
from vssource import source
from kagefunc import adaptive_grain

core.max_cache_size = 1024 * 10

# note: tinggal ubah bagian ini aja
source = src_file(r"C:\Users\haru\Downloads\[SubsPlease] Saijaku Tamer wa Gomi Hiroi no Tabi wo Hajimemashita - 02 (1080p) [016E960C].mkv", force_lsmas=True)
src = source.init_cut()

denoise= BM3DCPU.denoise(src, 1, 1, profile=Profile.LOW_COMPLEXITY)
constasharpen = contrasharpening(denoise, src)

mask_deband = retinex_edgemask(constasharpen, sigma=1)
deband = F3kdb.deband(constasharpen)
debanded = core.std.MaskedMerge(deband, constasharpen, mask_deband)

grain = adaptive_grain(debanded, 0.8)
output = finalize_clip(grain, bits=10)

if __name__ == "__main__":
    settings = settings_builder_x265(preset='veryslow', crf=13, psy_rd=2.05, psy_rdoq=2.15, qcomp=0.73, aq_strength=0.85, rect=False)

    video_hevc = x265(settings, qp_clip=source, resumable=True).encode(output)
    
    audio = FFMpeg.Extractor(track=1).extract_audio(source.file)

    mux(
    video_hevc.to_track(name="pololer", default=True),
    audio.to_track("jpn", "jpn", True)
    )
else:
    set_output(src, "source")
    set_output(output, "Filtered")