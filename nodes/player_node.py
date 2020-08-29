try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

from sonos import SonosControl

LOGGER = polyinterface.LOGGER


class PlayerNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonos_players, household):
        super(PlayerNode, self).__init__(controller, primary, address, name)
        self.SonosControl = None
        self.sonos_players = sonos_players
        self.household = household

    def start(self):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)

        if self.get_player_volume():
            self.setDriver('ST', 1, force=True)
        else:
            self.setDriver('ST', 0, force=True)

    def get_player_volume(self):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                volume = self.SonosControl.get_player_volume(player_id)
                if volume:
                    # List 0=volume, 1=muted, 2=fixed(true/false)
                    self.setDriver('SVOL', volume[0])
                    if volume[1]:
                        self.setDriver('GV0', 1, force=True)
                    else:
                        self.setDriver('GV0', 0, force=True)
                    return True
                else:
                    polyinterface.LOGGER.error('Error: ' + volume)
                    return False

    def set_player_volume(self, command):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)
        volume = command['value']
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = self.SonosControl.set_player_volume(player_id, volume)
                if _status:
                    self.setDriver('SVOL', volume)
                else:
                    polyinterface.LOGGER.error('Error: ' + str(_status))

    def set_player_mute(self, command):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = self.SonosControl.set_player_mute(player_id)
                if _status:
                    self.setDriver('GV0', 1)
                else:
                    polyinterface.LOGGER.error('Error: ' + str(_status))

    def set_player_unmute(self, command):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = self.SonosControl.set_player_unmute(player_id)
                if _status:
                    self.setDriver('GV0', 0)
                else:
                    polyinterface.LOGGER.error('Error: ' + str(_status))

    def send_say_tts(self, command):
        access_token = self.controller.polyConfig['customData']['access_token']
        self.SonosControl = SonosControl(access_token)
        val = command['value']
        say_cmd = 'SAY_TTS-' + str(val)
        say_tts = self.controller.polyConfig['customParams'][say_cmd]

        voice_rss_codec = self.controller.polyConfig['customParams']['codec']
        voice_rss_format = self.controller.polyConfig['customParams']['format']
        voice_rss_language = self.controller.polyConfig['customParams']['language']
        voice_rss_api_key = self.controller.polyConfig['customParams']['api_key']

        if voice_rss_api_key != 'none':
            raw_url = 'http://api.voicerss.org/?key=' + \
                      voice_rss_api_key + \
                      '&hl=' + voice_rss_language + \
                      '&c=' + voice_rss_codec + \
                      '&f=' + voice_rss_format + \
                      '&src=' + say_tts

            for player in self.sonos_players:
                player_id = player['id']
                player_address = 'p' + player_id.split('_')[1][0:-5].lower()
                if player_address == self.address:
                    polyinterface.LOGGER.info("Sending to VoiceRSS for Player: " + player_id)
                    _status = self.SonosControl.send_voice_rss(player_id, raw_url)
                    polyinterface.LOGGER.info("send_say_tts: " + str(_status))
        else:
            polyinterface.LOGGER.info(("VoiceRSS API Key is NOT Set"))

    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'SVOL', 'value': 0, 'uom': 51},
        {'driver': 'SAYTTS', 'value': 0, 'uom': 25},
        {'driver': 'GV0', 'value': 0, 'uom': 2},  # Mute/unMute
    ]

    id = 'PLAYER'

    commands = {
        'SVOL': set_player_volume,
        'MUTE': set_player_mute,
        'UNMUTE': set_player_unmute,
        'SAYTTS': send_say_tts
        }
