<div align="center">

  <img src="https://github.com/ponzischeme89/Sublogue/blob/master/docs/sublogue_v2.png" height="256" width="456">

  <h4>Favarr is your favourites manager for Emby, Jellyfin, Plesk and Audiobookshelf.</h4>

</div>

Favarr lets admins add favourites on behalf of other users — perfect for parents, kids, or anyone who just wants to press play without hunting. 

It keeps everyone’s libraries tidy, personalised, and blissfully low-effort.

Works for Emby, Jellyfin, Plesk and Audiobookshelf (limited functionality due to the way ABS handles "favourites").

## Features
- Insert plot summaries into existing .srt files without shifting timings
- Fetch metadata (plot, runtime, director, cast, IMDb/RT ratings) using OMDb, TMDb, TVMaze and Wikipedia - add these integrations under Settings before scanning
- Automatically strips OCR junk, music-only lines, timecodes, and other subtitle noise for a cleaner, more readable SRT.
- Preserve original dialogue and timing with safe insertion logic while cleaning watermarks (YTS, OpenSubtitles, etc.)
- Automation rules can run cleanup-only mode on schedules, or combined cleanup + metadata enrichment
- Folder Rules to have seperate logic for different folders (for example TV shows could have runtime but not actors, etc)
- Clean, fast web UI for scanning and batch processing built with Svelte (frontend) + Python/Flask (server)
- Three themes included: OLED, Ocean, and Dracula White

## Screenshots
<div align="center">

  <img src="https://github.com/ponzischeme89/Sublogue/blob/master/docs/screenshots/screenshot_scan.png" height="256" width="456">
  <img src="https://github.com/ponzischeme89/Sublogue/blob/master/docs/screenshots/screenshot_settings.png" height="256" width="456">

</div>

## Getting started
To get started installing Sublogue, choose on your ☠️ below!

Personally, I recommend **Komodo**. It's great.

**Quick Start with Docker:**

```sh
docker run -d \
  --name sublogue \
  -p 5050:5000 \
  -v /path/to/config:/config \
  -v /path/to/media:/media \
  ghcr.io/ponzischeme89/sublogue:latest
```

**Installation Methods (Expand sections to see details)**

<details>
<summary>⚓ Docker Compose</summary>
Create `data/` and `media/` folders next to the compose file, then run:

```yaml
version: "3.9"
services:
  sublogue:
    image: ghcr.io/ponzischeme89/sublogue:latest
    container_name: sublogue
    restart: unless-stopped
    environment:
      - TZ=Pacific/Auckland
    volumes:
      - ./data:/config
      - ./media:/media
    ports:
      - "5000:5000"
```

Start the stack:

```bash
docker compose up -d
```

Open `http://localhost:5000`.
</details>
<details>
  <summary>🧡 Unraid</summary>

Use the included template at `unraid-sublogue.xml`.

- `/mnt/user/appdata/sublogue` -> `/config`
- `/mnt/user/appdata/sublogue/media` -> `/media`

Start the container and open `http://<UNRAID-IP>:5000`.
</details>

<details>
<summary>🦎 Komodo</summary>

Create a new stack and paste a Komodo template like this:

```yaml
version: "3.9"
services:
  sublogue:
    image: ghcr.io/ponzischeme89/sublogue:latest
    container_name: sublogue

    ports:
      - "5000:5000"

    environment:
      - TZ=Etc/UTC
      - PUID=1000
      - PGID=1000

    volumes:
      - /volume1/Docker/sublogue/data:/config
      - /volume1/Media:/media

    restart: unless-stopped

    networks:
      - npm_network

networks:
  npm_network:
    external: true
```
</details>

## Timing And Insertion Logic
Sublogue never shifts existing subtitle timing. It only inserts metadata blocks into safe gaps.

| Decision | What Sublogue checks | Outcome |
| --- | --- | --- |
| Find insertion gap (start) | Time before the first dialogue subtitle (minus a 500ms safety buffer) | Uses that gap for intro blocks |
| Find insertion gap (end) | Time after the last dialogue subtitle (plus a 500ms safety buffer) | Uses that gap for outro blocks |
| Insufficient gap | No space to fit the intro/outro blocks | Skips insertion and reports “Insufficient Gap” |
| Reading speed | Word count vs a 160 WPM target (min 1.2s, max 6.0s per block) | Splits plot into readable blocks |
| Existing Sublogue blocks | Looks for `{SUBLOGUE}` markers or legacy signatures | Removes old blocks before inserting new ones |

## Integrations
| Provider | Signup / API key | Rate limits (see provider for current limits) | Notes |
| --- | --- | --- | --- |
| OMDb | https://www.omdbapi.com/apikey.aspx | Free tier has a daily cap 1000 | Requires API key |
| TMDb | https://www.themoviedb.org/settings/api | Per-second rate limit | Requires API key |
| TVmaze | https://www.tvmaze.com/api | Polite usage limits | No API key required |
| Wikipedia | https://www.mediawiki.org/wiki/API:Main_page | No hard limits, be polite | No API key required; strict title matching |

## Limitations
- API rate limits: OMDb is tight, TMDb is better, TVMaze is polite-but-limited. Heavy scans may hit caps.
- Metadata gaps: If providers don’t have it, Sublogue won’t either. Ratings/plots can be missing or stale.
- Localisation: Only TMDb supports proper language/region data. OMDb/TVMaze are mostly English-only.
- Long plots: Big summaries go in as-is. Your TV may split them across multiple screens.
- Formats: Only .srt is supported. No WebVTT, ASS/SSA, or embedded subs yet.
- Duplicate inserts: Reprocessing the same file will stack multiple plot blocks.
- Offline use: Requires internet for metadata lookups — no offline mode.
- File access: Read-only or locked files cannot be processed.

## Roadmap
- [x] TVMaze integration
- [ ] More UI themes (OLED variants, Ocean+, and high-contrast)
- [ ] Poster + backdrop previews in results
- [ ] Smart duplicate-detection (don’t re-insert plot blocks)
- [ ] Automatic rate-limit backoff + retry logic
- [ ] Optional “short plot mode” for long summaries
- [ ] Expanded localisation using TMDb (title, plot, cast where available)
- [ ] Multi-format subtitle support (WebVTT, ASS/SSA)
- [ ] Offline caching of recent metadata lookups
- [ ] Per-scan analytics: success/fail counts, rate-limit warnings
- [ ] CLI mode for batch operations

## Support
- Help spread the word about Sublogue by telling your friends about this repo
- Give the repo a star (This really helps)
- Check out my other project, which is an open source renamer tool (with a very poor naming choice, but i'll likely change this in future) 
