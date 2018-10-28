#!/usr/bin/env python

import glob, os, urllib2, imp

from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover

########################################################################
# This takes a directory path and finds all the m4a (AAC) audio files in it
# A search is contructed based on the song metadata and used to pull the album
# artwork from the iTunes store.
# If a song already has artwork embedded, it is skipped
def searchITunes(path):

  # list of all m4a files in the input dir
  audioFiles = glob.glob(path + "/*.m4a")

  tracks=[]
  for file in audioFiles:
    # interpret the file as a MP4 file
    tracks.append(MP4(file))

  if len(tracks) == 0:
    return True
  # If the 'covr' metadata is already present then do not overwrite the
  # album art.  In this case we do nothing
  if 'covr' in tracks[0].keys() and len(tracks[0]['covr']) != 0:
    return True

  # Get the album and artists meta data fields
  album = str(tracks[0].tags["\xa9alb"][0])
  artist tracks[0].tags["\xa9ART"][0].encode('utf-8').strip()
  # Some artists metadata contains annoying "featuring" blah
  # In these cases, try to remove the feat part
  # Not 100% robust, there may be weird cases I haven't thought of!
  feat = artist.find(" Feat.")
  if feat >0 :
    artist = artist[:feat]
  searchstr = album + "+" + artist
  # Another list of annoying special chars to replace
  for s in [" ", "&", "'", ",", "."]:
      searchstr=searchstr.replace(s, "+")

  # If there was a double replace, we end up with ++, which is also bad
  tmpStr=searchstr.replace("++", "+")
  while tmpStr != searchstr:
    searchstr = tmpStr
    tmpStr = searchstr.replace("++", "+")

  # This is our final constructed iTunes query
  search=urllib2.urlopen("https://itunes.apple.com/search?term="+searchstr+"&entity=album&media=music&country=GB")
  # The iTunes store search returns a string which is itself a valid
  # python dict.  We want to execute that python to load the dict.
  # First strip the first 3 chars, which are bogus
  result=search.read()[3:]
  # Then construct a string that when executed assigns the dict to albumdata
  result="albumdata="+result

  # Now we can execute the string.  We have to trust Apple here I guess :/
  module = imp.new_module("albumdata")
  exec result in module.__dict__

  albumdata=module.albumdata

  id=0

  # If the resultCount key is smpty then there aren't any valid results. Nothing to do
  if albumdata["resultCount"] == 0:
    print "no iTunes result found for " + searchstr
    return False
  # If there is more than one result, then we want to find the best fit one
  # Simply choose the one with the best match to the album name
  elif albumdata["resultCount"] != 1:
    counter=0
    # 'results' is a list of dicts, which themselves should contain the 'collectionName'
    for result in albumdata['results']:
      # If the 'collectionName' exactly matches the desired album, choose that one
      if result['collectionName'] == album:
        id=counter
        break
      counter += 1

  # Print the artist and album from teh matching results
  print "artist, album = " + albumdata['results'][id]['artistName'] + ", " + albumdata['results'][id]['collectionName']
  # And this is now a url to the album art in the iTunes store.  Request 1080*1080 resolution :)
  imageURL = albumdata['results'][id]['artworkUrl100'].replace("100x100", "1080x1080")

  # Get the image data
  imageFile = urllib2.urlopen(imageURL)
  imageData = imageFile.read()
  # And use mutagen to turn it into an embeddable album art
  cover = MP4Cover(imageData, MP4Cover.FORMAT_JPEG)

  # Loop over all tracks we found at the start and embed the art
  for track in tracks:
    track['covr'] = [cover]
    track.save()

  imageFile.close()

  return True
########################################################################

# This searches for local jpeg files in the same dir as m4a files
# If there is a jpeg, it embeds it as album art into any m4a files in
# the same dir

def searchJPEG(path):
  
  # jpeg files could end in jpeg or jpg.
  # We could use magic numbers here instead to find jpeg files with
  # unexpected suffixes, in case someone is being perverse.
  jpgFiles = glob.glob(path + "/*.jpg")
  jpgFiles = jpgFiles + glob.glob(path + "/*.jpeg")
  
  # If there aren't any jpegs then give up
  if len(jpgFiles) == 0:
    print "No local jpeg file for " + path
    return False
  
  # Use only the first image found
  jpgFile = open(jpgFiles[0], "r")
  jpgData = jpgFile.read()
  # use mutagen to convert the image data to album artwork
  cover = MP4Cover(jpgData, MP4Cover.FORMAT_JPEG)

  # get the list of audio files ending m4a
  audioFiles = glob.glob(path + "/*.m4a")
  tracks = []
  for file in audioFiles:
    tracks.append(MP4(file))

  # embed the artwork in each of the found tracks
  for track in tracks:
    track['covr'] = [cover]
    track.save()

  jpgFile.close()

  return True

########################################################################

# This is the main loop.  It just runs in the execution dir to find all
# songs and first search the iTunes store for album art.  If that fails
# it will search for a local jpeg to embed

for dir in os.walk("."):
  success = searchITunes(dir[0])
  if not success:
    success = searchJPEG(dir[0])

  if not success:
    print "Album art missing for " + dir[0]


