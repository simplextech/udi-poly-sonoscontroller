# Sonos Controller Polyglot NodeServer

#### Installation
- This nodeserver can be installed through the Polyglot Cloud Store.

#### Sonos Control Support
- Sonos Groups
  * Sonos group nodes are created
  * Playback status, Volume, Mute, Shuffle
  * Favorites Selection and Playback
  * Playlist Selection and Playback
- Sonos Players
  * Player playback status, volume, mute status
  * Individual Player volume and mute control
  * Experimental TTS Support
    * [VoiceRSS](http://www.voicerss.org/default.aspx)
    
 #### Configuration
 After installation the Polyglot Configuration "should" list options in the 
 Custom Configuration Parameters for configuration of Voice RSS and Say TTS phrases
 
  * [VoiceRSS Documentation](http://www.voicerss.org/api/documentation.aspx)
    * Reference the documentation above if you want to change any of the VoiceRSS configuration parameters such as 
    language, codec or format
    
  - api_key = YOUR VoiceRSS API KEY
  - codec = mp3
  - format = 24khz_16bit_stereo
  - language = en-us
  
  * Say / TTS phrases are the value entered for the keys.  At the moment five (5)
  separate phrases are currently supported.  Once further testing is performed
  or another way of doing this dynamicaly is figured out this will be expanded
  
  - SAY_TTS-1 = Your Phrase
  - SAY_TTS-2
  - SAY_TTS-3
  - SAY_TTS-4
  - SAY_TTS-5

#### Requirements
- ISY994i Firmware 5.x
- Polyglot Cloud

#### Support / Contributions
[Support/Contributions/Coffee](https://www.paypal.me/simplextech)

#### Attributions
- [Universal Devices](https://www.universal-devices.com/)
- [Polyglot](https://github.com/UniversalDevicesInc/polyglot-v2)
