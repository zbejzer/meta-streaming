# Mp3tag — Tag Field Mappings

> Fragment of the official Mp3tag documentation ([docs.mp3tag.de](https://docs.mp3tag.de), "Tag Field Mappings" reference), converted from HTML for offline reference. Companion fragments: [../picard/basic-tags.md](../picard/basic-tags.md), [../picard/advanced-tags.md](../picard/advanced-tags.md).

The list below gives an overview of all tag fields available in Mp3tag, their names to be used in Mp3tag, and how they are mapped to the internal structures of the different tag formats.

You can edit these tag fields via **View → Extended Tags…**, add user-defined fields to the [Tag Panel](https://docs.mp3tag.de/customization/tag-panel), or add user-defined columns to the [File List](https://docs.mp3tag.de/customization/file-list). All listed fields `FIELDNAME` can be referenced via a placeholder `%fieldname%` in [format strings](https://docs.mp3tag.de/format).

Please note that fields of VorbisComments (used with FLAC, OGG, SPX) and of APEv2 tags are not mapped internally by Mp3tag but are displayed with their actual name unless they use a [user-defined field mapping](https://docs.mp3tag.de/customization/options/tags/mapping).

In case you need to change one of the mappings (e.g., for using consistent field names across formats), you can create a [user-defined field mapping](https://docs.mp3tag.de/customization/options/tags/mapping).

An overview of all tag field mappings is also available as a [table](https://docs.mp3tag.de/mapping-table).

## Tag Field Mappings

Empty cells mean the field is not mapped for that format.

| Field | ID3v2.3 | ID3v2.4 | MP4 | Matroska | ASF/Windows Media | RIFF INFO | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `ACOUSTID_ID` | `TXXX:Acoustid Id` | `TXXX:Acoustid Id` | `----:com.apple.iTunes:Acoustid Id` | | | | |
| `ACOUSTID_FINGERPRINT` | `TXXX:Acoustid Fingerprint` | `TXXX:Acoustid Fingerprint` | `----:com.apple.iTunes:Acoustid Fingerprint` | | | | |
| `ALBUM` | `TALB` | `TALB` | `©alb` | MKA: `T=50 TITLE` · MKV: `T=60 TITLE` | `WM/AlbumTitle` | `IPRD` | |
| `ALBUMSORT` | `TSOA` | `TSOA` | `soal` | MKA: `T=50 SORT_WITH` · MKV: `T=60 SORT_WITH` | `WM/AlbumSortOrder` | | |
| `ALBUMARTIST` | `TPE2` | `TPE2` | `aART` | MKA: `T=50 ARTIST` · MKV: `T=60 ARTIST` | `WM/AlbumArtist` | | |
| `ALBUMARTISTSORT` | `TSO2` | `TSO2` | `soaa` | `T=30` | | | |
| `ARTIST` | `TPE1` | `TPE1` | `©art` | MKA: `T=30 ARTIST` · MKV: `T=50 ARTIST` | `Author` | `IART` | |
| `ARTISTSORT` | `TSOP` | `TSOP` | `soar` | `T=30` | `WM/ArtistSortOrder` | | |
| `BARCODE` | `TXXX:BARCODE` | `TXXX:BARCODE` | `----:com.apple.iTunes:BARCODE` | `T=30` | `WM/Barcode` | | Field is used when importing via MusicBrainz (since Mp3tag v3.13). |
| `BPM` | `TBPM` | `TBPM` | `tmpo` | `T=30` | `WM/BeatsPerMinute` | | |
| `CATALOGNUMBER` | `TXXX:CATALOGNUMBER` | `TXXX:CATALOGNUMBER` | `----:com.apple.iTunes:CATALOGNUMBER` | `T=30` | `WM/CatalogNo` | | Field is used when importing via Discogs and MusicBrainz (since Mp3tag v3.13). |
| `COMMENT` | `COMM` | `COMM` | `©cmt` | `T=30` | `Description` | `ICMT` | |
| `COMPILATION` | `TCMP` | `TCMP` | `cpil` | `T=30` | | | Field that is used by iTunes to mark albums as compilation. Either enter the value 1 or delete the field. |
| `COMPOSER` | `TCOM` | `TCOM` | `©wrt` | `T=30` | `WM/Composer` | | |
| `COMPOSERSORT` | `TSOC` | `TSOC` | `soco` | `T=30` | | | |
| `CONDUCTOR` | `TPE3` | `TPE3` | `©con` | `T=30` | `WM/Conductor` | | |
| `CONTENTGROUP` | `TIT1` | `TIT1` | `©grp` | `T=30` | `WM/ContentGroupDescription` | | |
| `COPYRIGHT` | `TCOP` | `TCOP` | `cprt` | `T=30` | `Copyright` | `ICOP` | |
| `DATE` | `TDAT` | `TXXX:DATE` | | | | | |
| `DESCRIPTION` | | | `desc` | `T=30` | | | |
| `DISCNUMBER` | `TPOS` | `TPOS` | `disk` | `T=50 PART_NUMBER` | `WM/PartOfSet` | | Mapped to `TVEPISODE` for Matroska MKV. |
| `ENCODEDBY` | `TENC` | `TENC` | `©enc` | MKA: `T=30 ENCODED_BY` · MKV: `T=50 ENCODED_BY` | `WM/EncodedBy` | | |
| `ENCODERSETTINGS` | `TSSE` | `TSSE` | | MKA: `T=30` · MKV: `T=50` | `WM/EncodingSettings` | | |
| `ENCODINGTIME` | | `TDEN` | | `T=30` | `WM/EncodingTime` | | |
| `FILEOWNER` | `TOWN` | `TOWN` | | MKA: `T=30 PURCHASE_OWNER` · MKV: `T=50 PURCHASE_OWNER` | | | |
| `FILETYPE` | `TFLT` | `TFLT` | | `T=30` | | | |
| `GENRE` | `TCON` | `TCON` | `©gen \| gnre` | `T=30` | `WM/Genre` | `IGNR` | |
| `GROUPING` | `GRP1` | `GRP1` | | `T=30` | | | |
| `INITIALKEY` | `TKEY` | `TKEY` | | `T=30 INITIAL_KEY` | `WM/InitialKey` | | |
| `INVOLVEDPEOPLE` | `IPLS` | `TIPL` | | `T=30` | | | `Role1:Person1;Role2:Person2;…` e.g. `Drums:Jamie Graham;` |
| `ISRC` | `TSRC` | `TSRC` | | `T=30` | `WM/ISRC` | | |
| `LANGUAGE` | `TLAN` | `TLAN` | | `T=30` | `WM/Language` | `ILNG` | |
| `LENGTH` | `TLEN` | `TLEN` | | `T=30` | | | |
| `LYRICIST` | `TEXT` | `TEXT` | | `T=30` | | | |
| `MEDIATYPE` | `TMED` | `TMED` | | `T=50 ORIGINAL_MEDIA_TYPE` | | | |
| `MIXARTIST` | `TPE4` | `TPE4` | | `T=30 REMIXED_BY` | | | |
| `MOOD` | | `TMOO` | | `T=30` | `WM/Mood` | | |
| `MOVEMENTNAME` | `MVNM` | `MVNM` | `©mvn` | `T=20 TITLE` | | | |
| `MOVEMENT` | `MVIN` | `MVIN` | `©mvi` | `T=20 PART_NUMBER` | | | |
| `MOVEMENTTOTAL` | `MVIN` | `MVIN` | `©mvc` | `T=30` | | | |
| `MUSICBRAINZ_ALBUMARTISTID` | `TXXX:MusicBrainz Album Artist Id` | `TXXX:MusicBrainz Album Artist Id` | `----:com.apple.iTunes:MusicBrainz Album Artist Id` | | | | |
| `MUSICBRAINZ_ALBUMID` | `TXXX:MusicBrainz Album Id` | `TXXX:MusicBrainz Album Id` | `----:com.apple.iTunes:MusicBrainz Album Id` | | | | |
| `MUSICBRAINZ_ALBUMRELEASECOUNTRY` | `TXXX:MusicBrainz Album Release Country` | `TXXX:MusicBrainz Album Release Country` | `----:com.apple.iTunes:MusicBrainz Album Release Country` | | | | |
| `MUSICBRAINZ_ALBUMSTATUS` | `TXXX:MusicBrainz Album Status` | `TXXX:MusicBrainz Album Status` | `----:com.apple.iTunes:MusicBrainz Album Status` | | | | |
| `MUSICBRAINZ_ALBUMTYPE` | `TXXX:MusicBrainz Album Type` | `TXXX:MusicBrainz Album Type` | `----:com.apple.iTunes:MusicBrainz Album Type` | | | | |
| `MUSICBRAINZ_ARTISTID` | `TXXX:MusicBrainz Artist Id` | `TXXX:MusicBrainz Artist Id` | `----:com.apple.iTunes:MusicBrainz Artist Id` | | | | |
| `MUSICBRAINZ_DISCID` | `TXXX:MusicBrainz Disc Id` | `TXXX:MusicBrainz Disc Id` | `----:com.apple.iTunes:MusicBrainz Disc Id` | | | | |
| `MUSICBRAINZ_ORIGINALALBUMID` | `TXXX:MusicBrainz Original Album Id` | `TXXX:MusicBrainz Original Album Id` | `----:com.apple.iTunes:MusicBrainz Original Album Id` | | | | |
| `MUSICBRAINZ_ORIGINALARTISTID` | `TXXX:MusicBrainz Original Artist Id` | `TXXX:MusicBrainz Original Artist Id` | `----:com.apple.iTunes:MusicBrainz Original Artist Id` | | | | |
| `MUSICBRAINZ_RELEASEGROUPID` | `TXXX:MusicBrainz Release Group Id` | `TXXX:MusicBrainz Release Group Id` | `----:com.apple.iTunes:MusicBrainz Release Group Id` | | | | |
| `MUSICBRAINZ_RELEASETRACKID` | `TXXX:MusicBrainz Release Track Id` | `TXXX:MusicBrainz Release Track Id` | `----:com.apple.iTunes:MusicBrainz Release Track Id` | | | | |
| `MUSICBRAINZ_TRACKID` | `UFID:http://musicbrainz.org` | `UFID:http://musicbrainz.org` | `----:com.apple.iTunes:MusicBrainz Track Id` | | | | |
| `MUSICBRAINZ_TRMID` | `TXXX:MusicBrainz TRM Id` | `TXXX:MusicBrainz TRM Id` | `----:com.apple.iTunes:MusicBrainz TRM Id` | | | | |
| `MUSICBRAINZ_WORKID` | `TXXX:MusicBrainz Work Id` | `TXXX:MusicBrainz Work Id` | `----:com.apple.iTunes:MusicBrainz Work Id` | | | | |
| `MUSICIANCREDITS` | | `TMCL` | | `T=30` | | | `Role1:Person1;Role2:Person2;…` e.g. `Drums:Jamie Graham;` |
| `NARRATOR` | | | `©nrt` | `T=30` | | | |
| `NETRADIOOWNER` | `TRSO` | `TRSO` | | `T=30` | | | |
| `NETRADIOSTATION` | `TRSN` | `TRSN` | | `T=30` | | | |
| `ORIGALBUM` | `TOAL` | `TOAL` | | `T=30` | `WM/OriginalAlbumTitle` | | |
| `ORIGARTIST` | `TOPE` | `TOPE` | | `T=30` | `WM/OriginalArtist` | | |
| `ORIGFILENAME` | `TOFN` | `TOFN` | | `T=30` | `WM/OriginalFilename` | | |
| `ORIGLYRICIST` | `TOLY` | `TOLY` | | `T=30` | `WM/OriginalLyricist` | | |
| `ORIGYEAR` | `TORY` | `TDOR` | | `T=30` | `WM/OriginalReleaseYear` | | |
| `PODCAST` | `PCST` | `PCST` | `pcst` | `T=30` | | | Field that is used by iTunes to mark tracks as podcasts. Either enter the value 1 or delete the field. |
| `PODCASTCATEGORY` | `TCAT` | `TCAT` | `catg` | `T=30` | | | |
| `PODCASTDESC` | `TDES` | `TDES` | `ldes` | `T=30` | | | |
| `PODCASTID` | `TGID` | `TGID` | `egid` | `T=30` | | | |
| `PODCASTKEYWORDS` | `TKWD` | `TKWD` | `keyw` | `T=30` | | | |
| `PODCASTURL` | `WFED` | `WFED` | `purl` | `T=30` | | | |
| `POPULARIMETER` | `POPM` | `POPM` | | `T=30` | | | This description is for ID3v2 tags only. The playcounter is an optional value. The rating is an integer between 1 (worst) and 255 (best). Syntax: `Email\|Rating\|Playcounter` |
| `PUBLISHER` | `TPUB` | `TPUB` | `©pub` | `T=30` | `WM/Publisher` | | |
| `RATING MM` | `POPM` | `POPM` | | `T=30` | | | Abstraction on `POPULARIMETER` as used in MediaMonkey. Track rating from 1 = Bad to 5 = Very good. You can also enter stars * (and - for half stars) for rating the track. Use **Options → Tags → Advanced** to always display `POPULARIMETER` values. |
| `RATING WMP` | `POPM` | `POPM` | | `T=30` | `WM/SharedUserRating` | | Abstraction on `POPULARIMETER` as used in Windows Media Player. Track rating from 1 = Bad to 5 = Very good. You can also enter stars * for rating the track. Use **Options → Tags → Advanced** to always display `POPULARIMETER` values. |
| `RELEASETIME` | `TDRL` | `TDRL` | | `T=50 DATE_RELEASED` | | | |
| `SETSUBTITLE` | | `TSST` | | MKA: `T=50 SUBTITLE` · MKV: `T=60 SUBTITLE` | | | |
| `SUBTITLE` | `TIT3` | `TIT3` | | MKA: `T=30` · MKV: `T=50` | `WM/SubTitle` | | |
| `TAGGINGTIME` | | `TDTG` | | `T=30 DATE_TAGGED` | | | |
| `TITLE` | `TIT2` | `TIT2` | `©nam` | MKA: `T=30` · MKV: `T=50` | `Title` | `INAM` | |
| `TITLESORT` | `TSOT` | `TSOT` | `sonm` | MKA: `T=30 SORT_WITH` · MKV: `T=50 SORT_WITH` | `WM/TitleSortOrder` | | |
| `TRACK` | `TRCK` | `TRCK` | `trkn` | `T=30 PART_NUMBER` | `WM/TrackNumber` | `ITRK` | |
| `UNIQUEFILEID` | `UFID` | `UFID` | | | | | |
| `UNSYNCEDLYRICS` | `USLT` | `USLT` | `©lyr` | `T=30 LYRICS` | `WM/Lyrics` | | Syntax: `xxx\|\|Lyrics` where xxx = language of the lyrics, abbreviated by 3 characters according to ISO-639-2. |
| `WWW` | `WXXX` | `WXXX` | | `T=30` | | | |
| `WWWARTIST` | `WOAR` | `WOAR` | | `T=30` | `WM/AuthorURL` | | |
| `WWWAUDIOFILE` | `WOAF` | `WOAF` | | `T=30` | `WM/AudioFileURL` | | |
| `WWWAUDIOSOURCE` | `WOAS` | `WOAS` | | `T=30` | `WM/AudioSourceURL` | | |
| `WWWCOMMERCIALINFO` | `WCOM` | `WCOM` | | MKA: `T=30 PURCHASE_INFO` · MKV: `T=50 PURCHASE_INFO` | `WM/PromotionURL` | | |
| `WWWCOPYRIGHT` | `WCOP` | `WCOP` | | `T=30` | `CopyrightURL` | | |
| `WWWPAYMENT` | `WPAY` | `WPAY` | | MKA: `T=30 PURCHASE_ITEM` · MKV: `T=50 PURCHASE_ITEM` | | | |
| `WWWPUBLISHER` | `WPUB` | `WPUB` | | `T=30` | | | |
| `WWWRADIOPAGE` | `WORS` | `WORS` | | `T=30` | | | |
| `YEAR` | `TYER` | `TDRC` | `©day` | `T=50 DATE_RECORDED` | `WM/Year` | `ICRD` | |

## Other fields

Fields not listed above are mapped generically:

| | ID3v2.3 | ID3v2.4 | MP4 | Matroska | ASF/Windows Media | RIFF INFO |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| *Internal* | `TXXX:fieldname` | `TXXX:fieldname` | `----:com.apple.iTunes:fieldname` | `T=30 fieldname` | `fieldname` | |

## Tag fields exclusive to MP4

| Name in Mp3tag | MP4 | iTunes |
| :-- | :-- | :-- |
| `DIRECTOR` | `©dir` | |
| `ITUNESACCOUNT` | `apID` | |
| `ITUNESADVISORY` [^1] | `rtng` | |
| `ITUNESALBUMID` | `plID` | iTunes Album ID |
| `ITUNESARTISTID` | `atID` | iTunes Artist ID |
| `ITUNESCATALOGID` | `cnID` | iTunes Catalog ID |
| `ITUNESCOMPOSERID` | `cmID` | iTunes Composer ID |
| `ITUNESCOUNTRYID` | `sfID` | iTunes Store Country ID |
| `ITUNESGAPLESS` [^2] | `pgap` | Gapless album |
| `ITUNESGENREID` | `geID` | iTunes Genre ID |
| `ITUNESHDVIDEO` | `hdvd` | Boolean flag for HD video (0/1) |
| `ITUNESMEDIATYPE` [^3] | `stik` | Media type |
| `ITUNESOWNER` | `ownr` | Owner |
| `ITUNESPURCHASEDATE` | `purd` | Purchase Date |
| `RATE` | `rate` | Rating |
| `SHOWMOVEMENT` | `shwm` | Show Movement |
| `STOREDESCRIPTION` | `sdes` | Store Description |
| `TOTALDISCS` | `disk` | Total Disc Number |
| `TOTALTRACKS` | `trkn` | Total Track Number |
| `TVEPISODE` | `tves` | TV Episode |
| `TVEPISODEID` | `tven` | TV Episode ID |
| `TVNETWORK` | `tvnn` | |
| `TVSEASON` | `tvsn` | TV Season |
| `TVSHOW` | `tvsh` | Show |
| `TVSHOWSORT` | `sosn` | Sort Show |
| `WORK` | `©wrk` | Work Name |

[^1]: `ITUNESADVISORY` — content rating, use 0 = None, 1 = Explicit, 2 = Clean.
[^2]: `ITUNESGAPLESS` — marks the song as part of a gapless album. Set the value to 1 or delete the field.
[^3]: `ITUNESMEDIATYPE` — possible values: Normal, Audiobook, Bookmark, Music Video, Movie, TV Show, Booklet, Ringtone, Podcast, iTunes U.

## Tag fields exclusive to MKV

| Name in Mp3tag | Matroska |
| :-- | :-- |
| `TVEPISODE` | `T=50 PART_NUMBER` |
| `TVSEASON` | `T=60 PART_NUMBER` |

## Relevance to this plugin

- The table independently corroborates the [mapping audit](../../design/musicbrainz-deezer-mapping.md) claim that the synthetic MBID tags written by Picard have concrete per-format representations everywhere: `MUSICBRAINZ_ALBUMID`, `MUSICBRAINZ_ALBUMARTISTID`, `MUSICBRAINZ_ARTISTID`, `MUSICBRAINZ_RELEASEGROUPID`, `MUSICBRAINZ_TRACKID`, `MUSICBRAINZ_ALBUMSTATUS`, `MUSICBRAINZ_ALBUMTYPE`, and `MUSICBRAINZ_ALBUMRELEASECOUNTRY` all map to `TXXX:…` frames (ID3v2), `----:com.apple.iTunes:…` freeform atoms (MP4), with `MUSICBRAINZ_TRACKID` using `UFID:http://musicbrainz.org` in ID3v2.
- The same holds for the album-level tags the plugin produces from Deezer data: `BARCODE` (from `upc`), `DATE`, `ISRC`, `DISCNUMBER`, `GENRE`, and the MusicBrainz type/status/country fields.
- Mp3tag's *Internal* field names are the uppercase equivalents of Picard's tag names, so tags written by the plugin round-trip losslessly through Mp3tag's Extended Tags editor.