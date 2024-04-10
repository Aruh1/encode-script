from vstools import change_fps, core, set_output

source = core.lsmas.LWLibavSource(
    r"D:\Download\Gushing.Over.Magical.Girls.S01E10.Loco.x.Leber.1080p.HIDI.WEB-DL.AAC2.0.H.264-VARYG.mkv"
)
fps = change_fps(source, 24000 / 1001)

set_output(fps)
