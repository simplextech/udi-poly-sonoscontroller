try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

from sonos import SonosControl as SonosControl


class PlayerNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonos, sonos_players, household):
        super(PlayerNode, self).__init__(controller, primary, address, name)
        # access_token = self.polyConfig['customParams']['access_token']
        # self.sonos = SonosControl(access_token)
        self.sonos = sonos
        self.sonos_players = sonos_players
        self.household = household

    def start(self):
        # print('Starting Player: ' + self.name + ' ------------------')
        if self.get_player_volume():
            self.setDriver('ST', 1, force=True)
        else:
            self.setDriver('ST', 0, force=True)

    def get_player_volume(self):
        # print('Get Volume command')
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                volume = SonosControl.get_player_volume(self.sonos, player_id)
                if volume:
                    # List 0=volume, 1=muted, 2=fixed(true/false)
                    self.setDriver('SVOL', volume[0])
                    if volume[1] == 'true':
                        self.setDriver('GV0', 1, force=True)
                    else:
                        self.setDriver('GV0', 0, force=True)
                    return True
                else:
                    print('Error: ' + volume)
                    return False

    def set_player_volume(self, command):
        # print('Set Volume command: ', command)
        volume = command['value']
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = SonosControl.set_player_volume(self.sonos, player_id, volume)
                if _status:
                    self.setDriver('SVOL', volume)
                else:
                    print('Error: ' + _status)

    def set_player_mute(self, command):
        # print('Mute Command: ', command)
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = SonosControl.set_player_mute(self.sonos, player_id)
                if _status:
                    self.setDriver('GV0', 1)
                else:
                    print('Error: ' + _status)

    def set_player_unmute(self, command):
        # print('unMute Command: ', command)
        for player in self.sonos_players:
            player_id = player['id']
            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
            if player_address == self.address:
                _status = SonosControl.set_player_unmute(self.sonos, player_id)
                if _status:
                    self.setDriver('GV0', 0)
                else:
                    print('Error: ' + _status)

    def send_say_tts(self, command):
        val = command['value']
        say_cmd = 'SAY_TTS-' + str(val)
        say_tts = self.controller.polyConfig['customParams'][say_cmd]

        codec = self.controller.polyConfig['customParams']['codec']
        format = self.controller.polyConfig['customParams']['format']
        language = self.controller.polyConfig['customParams']['language']
        apiKey = self.controller.polyConfig['customParams']['apiKey']

        if apiKey != 'none':
            raw_url = 'http://api.voicerss.org/?key=' + \
                      apiKey + \
                      '&hl=' + language + \
                      '&c=' + codec + \
                      '&f=' + format + \
                      '&src=' + say_tts

            for player in self.sonos_players:
                player_id = player['id']
                player_address = 'p' + player_id.split('_')[1][0:-5].lower()
                if player_address == self.address:
                    polyinterface.LOGGER.info("Sending to VoiceRSS for Player: " + player_id)
                    _status = SonosControl.send_voice_rss(self.sonos, player_id, raw_url)
                    print("send_say_tts: " + str(_status))

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
