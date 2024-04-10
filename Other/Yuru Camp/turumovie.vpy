from vstools import core, set_output

bd = core.lsmas.LWLibavSource(
    r"E:\[BDMV][230426][AMU-ANM4111][映画『ゆるキャン△』][コレクターズ版]\TGXS-2802\BDMV\STREAM\00004.m2ts"
)

patk = core.lsmas.LWLibavSource(
    r"E:\[BDMV][230426][AMU-ANM4111][映画『ゆるキャン△』][コレクターズ版]\TGXS-2804\BDMV\STREAM\00004.m2ts"
)

set_output(bd, "1080")
set_output(patk, "4K")
