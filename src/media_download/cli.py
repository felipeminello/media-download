"""CLI para baixar vídeos e áudios do YouTube usando yt-dlp."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from . import __version__

QUALIDADES = ["best", "2160", "1440", "1080", "720", "480", "360"]
FORMATOS_AUDIO = ["mp3", "m4a", "opus", "flac", "wav"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ytdl",
        description="Baixa vídeos (ou só o áudio) do YouTube.",
    )
    p.add_argument("urls", nargs="+", metavar="URL", help="URL(s) de vídeo, playlist ou canal")
    p.add_argument(
        "-o", "--output", type=Path, default=Path.cwd(),
        help="diretório de destino (padrão: diretório atual)",
    )
    p.add_argument(
        "-q", "--quality", choices=QUALIDADES, default="best",
        help="altura máxima do vídeo em pixels (padrão: best)",
    )
    p.add_argument(
        "-a", "--audio", nargs="?", const="mp3", choices=FORMATOS_AUDIO, metavar="FORMATO",
        help=f"baixa só o áudio; FORMATO em {{{','.join(FORMATOS_AUDIO)}}} (padrão: mp3)",
    )
    p.add_argument("--no-playlist", action="store_true", help="se a URL tiver &list=, baixa só o vídeo")
    p.add_argument("--subs", action="store_true", help="baixa legendas (pt e en) e embute no vídeo")
    p.add_argument("-F", "--list-formats", action="store_true", help="lista os formatos disponíveis e sai")
    p.add_argument("-i", "--info", action="store_true", help="mostra informações do vídeo sem baixar")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def js_runtimes() -> dict:
    # O YouTube exige um runtime JS para liberar todos os formatos; usa o que houver.
    return {rt: {} for rt in ("deno", "node", "bun") if shutil.which(rt)} or {"deno": {}}


def format_sort(quality: str) -> list[str]:
    # Maior resolução primeiro (limitada por -q); na mesma resolução prefere
    # H.264/AAC, que tocam em qualquer player. Acima de 1080p o YouTube só
    # oferece VP9/AV1, e aí eles são usados.
    res = "res" if quality == "best" else f"res:{quality}"
    return [res, "vcodec:h264", "acodec:aac"]


def build_options(args: argparse.Namespace) -> dict:
    has_ffmpeg = shutil.which("ffmpeg") is not None
    if (args.audio or args.subs) and not has_ffmpeg:
        sys.exit("erro: ffmpeg é necessário para --audio/--subs (brew install ffmpeg)")

    playlist_tmpl = "%(playlist_title|)s/%(playlist_index&{:03d} - |)s"
    opts: dict = {
        "outtmpl": str(args.output / f"{playlist_tmpl}%(title)s [%(id)s].%(ext)s"),
        "noplaylist": args.no_playlist,
        "ignoreerrors": "only_download",  # numa playlist, um vídeo indisponível não derruba o resto
        "windowsfilenames": True,
        "js_runtimes": js_runtimes(),
        "postprocessors": [],
    }

    if args.audio:
        opts["format"] = "ba/b"
        opts["postprocessors"].append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": args.audio,
            "preferredquality": "0",
        })
        opts["postprocessors"].append({"key": "FFmpegMetadata"})
        opts["postprocessors"].append({"key": "EmbedThumbnail"})
        opts["writethumbnail"] = True
    else:
        if has_ffmpeg:
            opts["format"] = "bv*+ba/b"
            opts["format_sort"] = format_sort(args.quality)
            opts["merge_output_format"] = "mp4"
        else:
            opts["format"] = "b"
            print("aviso: ffmpeg não encontrado; baixando formato único (qualidade limitada)", file=sys.stderr)

    if args.subs:
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["pt.*", "en.*"],
        })
        opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})

    return opts


def fmt_duracao(segundos: float | None) -> str:
    if not segundos:
        return "-"
    s = int(segundos)
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def show_info(urls: list[str], noplaylist: bool) -> int:
    with YoutubeDL({
        "quiet": True,
        "noplaylist": noplaylist,
        "extract_flat": "in_playlist",
        "js_runtimes": js_runtimes(),
    }) as ydl:
        for url in urls:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                entries = list(info.get("entries") or [])
                print(f"Playlist: {info.get('title')}  ({len(entries)} vídeos)")
                for i, e in enumerate(entries, 1):
                    print(f"  {i:3d}. {e.get('title')}  [{fmt_duracao(e.get('duration'))}]")
            else:
                print(f"Título:   {info.get('title')}")
                print(f"Canal:    {info.get('uploader')}")
                print(f"Duração:  {fmt_duracao(info.get('duration'))}")
                print(f"Views:    {info.get('view_count')}")
                print(f"Publicado:{' ' + info['upload_date'] if info.get('upload_date') else ' -'}")
            print()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.info:
            return show_info(args.urls, args.no_playlist)

        if args.list_formats:
            with YoutubeDL({"listformats": True, "noplaylist": True, "js_runtimes": js_runtimes()}) as ydl:
                ydl.download(args.urls)
            return 0

        args.output.mkdir(parents=True, exist_ok=True)
        with YoutubeDL(build_options(args)) as ydl:
            retcode = ydl.download(args.urls)
        return retcode
    except DownloadError:
        return 1  # o yt-dlp já imprimiu a mensagem de erro
    except KeyboardInterrupt:
        print("\ninterrompido", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
