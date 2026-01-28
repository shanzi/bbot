---
name: torrent-management
description: Manage BitTorrent downloads with Transmission client. Add torrents with intelligent download directory routing, monitor active downloads with progress tracking, and control torrent lifecycle.
---

# Torrent Management with Transmission

Manage BitTorrent downloads through Transmission BitTorrent client via the `transmission` MCP server.

## Available Operations

### 1. Add Torrent

Add torrent files or magnet links to Transmission.

**Tool:** `add_torrent`

**Parameters:**
- `torrent` - Path to .torrent file or magnet link
- `download_dir` - Optional target download directory

**Workflow for .torrent Files:**
1. User uploads or downloads .torrent file
2. Move to 'data/torrents' folder using `filesystem` tool
3. Analyze filename to determine content type
4. Add torrent with appropriate download directory

**Content Type Detection:**

Analyze the torrent filename to determine where to download:

**Movies:**
- Keywords: movie, film, bluray, 1080p, 2160p, 4k, x264, x265
- Download to: `/media/chase/Secondary/Movies`
- Examples: "Movie.Title.2024.1080p.BluRay.mkv", "Film.Name.4K.x265.mp4"

**TV Shows:**
- Keywords: S01E01, season, episode, complete, series
- Download to: `/media/chase/Secondary/TV Shows` or `/media/chase/Secondary/`
- Examples: "Show.Name.S01E01.mkv", "Series.Complete.Season.1"

**Other Content:**
- Music, software, documents, etc.
- Download to: `/media/chase/Secondary/` (default)

**Example Process:**
```
1. User uploads: "The.Matrix.1999.1080p.BluRay.x264.mkv.torrent"
2. Move to: data/torrents/The.Matrix.1999.1080p.BluRay.x264.mkv.torrent
3. Analyze: Contains "1080p", "BluRay" → It's a movie
4. add_torrent(
     torrent="data/torrents/The.Matrix.1999.1080p.BluRay.x264.mkv.torrent",
     download_dir="/media/chase/Secondary/Movies"
   )
5. Inform user: "Added movie torrent, downloading to Movies folder"
```

### 2. Show Active Downloads

Display detailed status of currently downloading torrents.

**Tool:** `show_active_downloads`

**Returns:**
- Torrent name
- Progress percentage
- Download speed (KB/s or MB/s)
- Upload speed
- ETA (estimated time remaining)
- Remaining size to download
- Status (downloading, seeding, paused)

**Display Format:**
```
📥 Active Downloads:

1. Movie Title (2024)
   Progress: 45.2% (2.1 GB / 4.7 GB)
   Speed: ↓ 5.2 MB/s  ↑ 1.1 MB/s
   ETA: 8 minutes
   Status: Downloading

2. TV Show S01E05
   Progress: 100% (850 MB / 850 MB)
   Speed: ↓ 0 KB/s  ↑ 2.3 MB/s
   Status: Seeding
```

**Use When:**
- User asks "How are my downloads?"
- Checking download progress
- Monitoring torrent status
- Seeing ETA for completion

### 3. List All Torrents

View all torrents (active and completed).

**Tool:** `list_torrents`

**Returns:**
- Complete list of all torrents
- Both active and stopped torrents
- Completed and incomplete downloads
- Seeding torrents

**Use When:**
- User wants to see everything
- Finding specific torrent ID
- Reviewing download history
- Managing completed downloads

### 4. Manage Torrent

Control torrent lifecycle and operations.

**Tool:** `manage_torrent`

**Parameters:**
- `torrent_id` - Torrent identifier (from list_torrents)
- `action` - Operation to perform

**Available Actions:**

**start** - Resume/start downloading
- Use when: Torrent is paused, user wants to begin download
- Example: `manage_torrent(torrent_id=123, action="start")`

**pause** - Pause downloading/seeding
- Use when: Need to free bandwidth, temporary stop
- Example: `manage_torrent(torrent_id=123, action="pause")`

**remove** - Remove torrent from list (keep downloaded files)
- Use when: Torrent completed, want to clean up list
- Example: `manage_torrent(torrent_id=123, action="remove")`

**remove_with_data** - Remove torrent AND delete downloaded files
- Use when: Don't want the content anymore, free disk space
- **Caution:** Permanent deletion! Confirm with user first
- Example: `manage_torrent(torrent_id=123, action="remove_with_data")`

## Torrent Organization

### Directory Structure
```
data/torrents/          # Store .torrent files here
/media/chase/Secondary/
├── Movies/            # Movie torrents
├── TV Shows/          # TV show torrents
├── Music/             # Music torrents
├── Software/          # Software torrents
└── [Other]/           # Default location
```

### Workflow Patterns

#### Pattern 1: Add Movie Torrent
```
User uploads: "Inception.2010.1080p.BluRay.x264.torrent"

1. Save to: data/attachment/Inception.2010.1080p.BluRay.x264.torrent
2. Move to: data/torrents/Inception.2010.1080p.BluRay.x264.torrent
3. Analyze: "1080p" + "BluRay" = Movie
4. add_torrent(
     torrent="data/torrents/Inception.2010.1080p.BluRay.x264.torrent",
     download_dir="/media/chase/Secondary/Movies"
   )
5. Response: "Added movie 'Inception' to download queue. Will save to Movies folder."
6. show_active_downloads() to display status
```

#### Pattern 2: Monitor Downloads
```
User: "How are my downloads going?"

1. show_active_downloads()
2. Parse response
3. Format nicely with progress bars, speeds, ETAs
4. Display active torrents with visual indicators
```

#### Pattern 3: Remove Completed Torrent
```
User: "Remove the completed movie download"

1. list_torrents() to find completed torrents
2. Identify movie torrent that's 100%
3. manage_torrent(torrent_id=X, action="remove")
4. Confirm: "Removed torrent from list. Files remain in Movies folder."
```

#### Pattern 4: Clean Up Unwanted Download
```
User: "Delete that TV show torrent I added by mistake"

1. list_torrents() to find the torrent
2. Confirm with user: "This will delete the downloaded files. Are you sure?"
3. User confirms
4. manage_torrent(torrent_id=X, action="remove_with_data")
5. Confirm: "Torrent and all downloaded files have been deleted."
```

## Content Type Recognition

### Movie Indicators
- Patterns: `\d{4}` (year), `1080p`, `2160p`, `4K`, `BluRay`, `WEB-DL`, `HDRip`
- Codecs: `x264`, `x265`, `H.264`, `HEVC`
- Extensions: `.mkv`, `.mp4`, `.avi`
- Destination: `/media/chase/Secondary/Movies`

### TV Show Indicators
- Patterns: `S\d{2}E\d{2}`, `Season.\d+`, `Complete.Series`
- Keywords: `episode`, `season`, `series`
- Examples: `S01E01`, `S02`, `Complete.Season.1`
- Destination: `/media/chase/Secondary/TV Shows` or default

### Music Indicators
- Patterns: `FLAC`, `MP3`, `320kbps`, `Album`, `Discography`
- Keywords: `soundtrack`, `OST`, `audio`
- Extensions: `.flac`, `.mp3`, `.m4a`
- Destination: `/media/chase/Secondary/Music`

### Default Category
- Anything that doesn't match above patterns
- Software, documents, archives, etc.
- Destination: `/media/chase/Secondary/`

## Progress Display

Format download progress for readability:

**Percentage:**
- `█████████░░░░░░░░░░` 45.2%
- Use filled blocks for completed, empty for remaining

**Size:**
- Show completed / total (e.g., "2.1 GB / 4.7 GB")
- Use appropriate units (KB, MB, GB, TB)

**Speed:**
- Download: ↓ 5.2 MB/s
- Upload: ↑ 1.1 MB/s
- Show both speeds

**ETA:**
- Convert seconds to readable format
- "8 minutes", "2 hours", "3 days"
- "Unknown" if calculating or stalled

**Status Icons:**
- 📥 Downloading
- 📤 Seeding
- ⏸️ Paused
- ✅ Completed
- ❌ Error

## Best Practices

1. **Always move .torrent files to data/torrents/** - Keeps organized
2. **Analyze filename before adding** - Route to correct directory
3. **Inform user of download location** - They should know where files go
4. **Use show_active_downloads for status** - More detailed than list_torrents
5. **Confirm before remove_with_data** - Permanent deletion!
6. **Display progress updates** - Keep user informed
7. **Monitor disk space** - Warn if downloads might fill disk
8. **Clean up completed torrents** - Remove from list after seeding
9. **Use descriptive messages** - Tell user what's happening
10. **Handle errors gracefully** - Invalid torrents, connection issues

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Torrent won't start | Invalid file/magnet | Verify torrent file validity |
| Slow download | No seeders | Check torrent health, find better source |
| Disk full | Not enough space | Check available space before adding |
| Can't remove | Torrent active | Pause first, then remove |
| Wrong location | Misclassified content | Manually specify download_dir |

## Magnet Links

Magnet links can be added directly without .torrent file:

**Format:**
```
magnet:?xt=urn:btih:...
```

**Process:**
```
add_torrent(
  torrent="magnet:?xt=urn:btih:...",
  download_dir="/media/chase/Secondary/Movies"
)
```

**Advantages:**
- No need to download .torrent file first
- More convenient for users
- Works same as .torrent files

## Integration with Other Skills

Torrent management works with:

- **Document Management**: Organize .torrent files
- **File System**: Move and organize downloaded content
- **Notifications**: Alert when downloads complete
- **Disk Management**: Monitor space usage

## Security and Privacy

- Don't share download directories outside appropriate locations
- Respect copyright laws
- Verify torrents before adding
- Use VPN if privacy is a concern
- Clean up .torrent files after adding
- Don't log or expose user's download history unnecessarily
