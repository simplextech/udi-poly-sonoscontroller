try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

from sonos import SonosControl as SonosControl


class PlayerNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonos_players, household):
        super(PlayerNode, self).__init__(controller, primary, address, name)
        self.sonos = SonosControl()
        self.sonos_players = sonos_players
        self.household = household

    def start(self):
        print('Starting Player: ' + self.name + ' ------------------')
        if self.get_player_volume():
            self.setDriver('ST', 1)
        else:
            self.setDriver('ST', 0)

    def get_player_volume(self):
        print('Get Volume command')
        for player in self.sonos_players:
            id = player['id']
            address = id.split('_')[1][0:-4].lower()
            if address == self.address:
                volume = SonosControl.get_player_volume(self.sonos, id)
                if volume:
                    self.setDriver('SVOL', volume[0])
                else:
                    print('Error: ' + volume)

    def set_player_volume(self, command):
        print('Set Volume command: ', command)
        volume = command['value']
        for player in self.sonos_players:
            id = player['id']
            address = id.split('_')[1][0:-4].lower()
            if address == self.address:
                _status = SonosControl.set_player_volume(self.sonos, id, volume)
                if _status:
                    self.setDriver('SVOL', volume)
                else:
                    print('Error: ' + _status)

    def set_player_mute(self, command):
        print('Mute Command: ', command)
        for player in self.sonos_players:
            id = player['id']
            address = id.split('_')[1][0:-4].lower()
            if address == self.address:
                _status = SonosControl.set_player_mute(self.sonos, id)
                if _status:
                    self.setDriver('GV0', 1)
                else:
                    print('Error: ' + _status)

    def set_player_unmute(self, command):
        print('unMute Command: ', command)
        for player in self.sonos_players:
            id = player['id']
            address = id.split('_')[1][0:-4].lower()
            if address == self.address:
                _status = SonosControl.set_player_unmute(self.sonos, id)
                if _status:
                    self.setDriver('GV0', 0)
                else:
                    print('Error: ' + _status)

    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'SVOL', 'value': 0, 'uom': 51},
        {'driver': 'GV0', 'value': 0, 'uom': 2},  # Mute/unMute
    ]

    id = 'PLAYER'

    commands = {
        'SVOL': set_player_volume,
        'MUTE': set_player_mute,
        'UNMUTE': set_player_unmute
        }
