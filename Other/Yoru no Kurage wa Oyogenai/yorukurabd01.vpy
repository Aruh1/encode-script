from vspreview import is_preview
from vstools import core
from yorukura_common import (
    create_mux_settings,
    filterchain,
    get_source,
    mux_video,
    preview_clips,
)

# Pengaturan dasar
eps = "01"  # Nomor episode
jpbd = r"00002.m2ts"  # Sumber video Blu-ray
amzn = f"Jellyfish.Cant.Swim.in.the.Night.S01E{eps}*VARYG.mkv"  # Sumber video Amazon (jika ada)

# Memperbesar ukuran cache untuk VapourSynth
core.max_cache_size = 1024 * 40

# Mendapatkan sumber file
source_jpbd, source_amzn, source_jpbdinit, source_amzninit = get_source(
    jpbd, amzn, trimbd=(24, 34190), trimamzn=(22, 34020)
)

# Melakukan proses filtering menggunakan filterchain
# Menangani situasi di mana source_amzn mungkin None
filterchain_results = (
    filterchain(source_jpbdinit, source_amzninit, (33997, None))
    if source_amzninit
    else filterchain(source_jpbdinit)
)

# Menampilkan hasil jika dalam mode preview
preview_clips(filterchain_results)

# Melakukan proses muxing hanya jika tidak dalam mode preview
if not is_preview():
    # Membuat pengaturan mux
    setup, settings = create_mux_settings(eps)

    # Mendefinisikan chapters
    chapters = ["Part A", "Part B", "Illustration"]

    # Melakukan proses muxing
    mux_video(
        setup=setup,
        settings=settings,
        source_clip=source_jpbdinit,
        final_clip=filterchain_results["final_clip"],
        source=source_jpbd,
        chtrname=chapters,
    )
