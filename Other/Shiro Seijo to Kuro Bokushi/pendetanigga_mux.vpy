from vsmuxtools import Premux, Setup, SubFile, VideoFile, mux

setup = Setup("NCOP")

video = VideoFile(
    r"D:\Download\[premux] Shiro Seijo to Kuro Bokushi - 01 (BDRip 1920x1080 HEVC FLAC) [0FF4E2AB].mkv"
)
premux = Premux(video, subtitles=None, keep_attachments=False)

sub = SubFile(r"C:\Users\Administrator\Desktop\asd\pendeta nigga\OP.ass")

fonts = sub.collect_fonts()

mux(premux, sub.to_track("Indonesia"), *fonts)
