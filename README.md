# media-download

CLI para baixar vídeos e áudios do YouTube, construída sobre o [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Requisitos

- Python 3.10+ e [uv](https://docs.astral.sh/uv/)
- `ffmpeg` (`brew install ffmpeg`): necessário para juntar vídeo+áudio em alta qualidade, extrair áudio e embutir legendas
- Um runtime JavaScript (`node`, `deno` ou `bun`): o YouTube exige um para liberar todos os formatos. A CLI usa o que estiver no PATH.

## Instalação

```sh
uv tool install .          # instala o comando `ytdl` globalmente
# ou, sem instalar:
uv run ytdl --help
```

## Uso

```sh
ytdl https://youtu.be/VIDEO_ID                  # melhor qualidade, mp4
ytdl -q 720 https://youtu.be/VIDEO_ID           # limita a 720p
ytdl -a https://youtu.be/VIDEO_ID               # só áudio, mp3 com capa e metadados
ytdl -a m4a https://youtu.be/VIDEO_ID           # só áudio, m4a
ytdl -o ~/Downloads URL1 URL2                   # vários vídeos, para outro diretório
ytdl "https://www.youtube.com/playlist?list=…"  # playlist inteira (subpasta numerada)
ytdl --no-playlist "https://youtube.com/watch?v=…&list=…"  # só o vídeo
ytdl --subs URL                                 # embute legendas pt/en
ytdl -i URL                                     # mostra informações sem baixar
ytdl -F URL                                     # lista formatos disponíveis
```

No zsh, coloque entre aspas as URLs que têm `?` ou `&` (ex.: `watch?v=…`), senão o shell tenta expandi-las.

Na mesma resolução, a CLI prefere H.264/AAC, que tocam em qualquer player. Acima de 1080p, o YouTube só oferece VP9/AV1.

Os arquivos são salvos como `Título [id].mp4`; playlists vão para `Nome da playlist/001 - Título [id].mp4`.

Se os downloads começarem a falhar, atualize o yt-dlp (o YouTube muda com frequência):

```sh
uv tool upgrade media-download   # ou: uv lock --upgrade-package yt-dlp
```

Use apenas para conteúdo que você tem direito de baixar.
