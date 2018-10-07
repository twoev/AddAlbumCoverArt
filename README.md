# AddAlbumCoverArt
Python funcs to search mp4 audio meta data, construct an itunes store query to extract album art and then use mutagen to embed it in the tracks

Currently everything is just in a single script - I may split things up if it grows more complicated.  You simply execute 

  ./bin/addArt.py
  
And it will query the iTunes store to find album artwork for any m4a audio files in the execution dir.  If the query fails, it will fall back on searching for any jpeg files in the same dir.  Any artwork it finds is embedded as metadata inside the audio files.  This is the most reliable way of having ncie album art across different audio players :)


