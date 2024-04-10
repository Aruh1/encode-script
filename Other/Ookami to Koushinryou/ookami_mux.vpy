from vsmuxtools import Chapters, Premux, Setup, SubFile, VideoFile, mux

setup = Setup("01v2")

video = VideoFile(
    r"D:\[premux] Ookami to Koushinryou (2024) - 01 (WEBRip 1920x1080 HEVC AAC) [7790076B].mkv"
)
premux = Premux(video, subtitles=None, keep_attachments=False)

caramelsub = SubFile(
    r"[Caramel] Ookami to Koushinryou (2024) - 01 [9B0AD089]_Subtitles01.IND.ass"
)
delimasub = SubFile(
    r"[Delima] Ookami to Koushinryou (2024) - 01 [C9F0B0C3]_Subtitles01.IND.ass"
)

fontsCaramel = caramelsub.collect_fonts(
    use_system_fonts=False,
    additional_fonts=r"./[Caramel] Ookami to Koushinryou (2024) - 01 [9B0AD089]_Attachments",
)
fontsDelima = delimasub.collect_fonts(
    use_system_fonts=False,
    additional_fonts=r"./[Delima] Ookami to Koushinryou (2024) - 01 [C9F0B0C3]_Attachments",
)

chapters = Chapters(
    [
        (0, "Prolog"),
        (2710, "Lagu Pembuka"),
        (4867, "Bagian 1"),
        (14075, "Bagian 2"),
        (32008, "Lagu Penutup"),
        (34166, "Selanjutnya"),
    ],
)

mux(
    premux,
    caramelsub.to_track("Caramel", lang="id", default=True, forced=False),
    delimasub.to_track("Delima", lang="id", default=False, forced=False),
    *fontsCaramel,
    *fontsDelima,
    chapters,
)
