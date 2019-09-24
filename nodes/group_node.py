
import polyinterface
from sonos import SonosControl as SonosControl


class GroupNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonos_groups, household):
        super(GroupNode, self).__init__(controller, primary, address, name)
        self.sonos = SonosControl()
        self.sonos_groups = sonos_groups
        self.household = household
        self.shuffle = False

    def start(self):
        print('Starting Group: ' + self.name + ' ------------------')
        # print(self.sonos_groups)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                playback_state = group['playbackState']
                if playback_state == 'PLAYBACK_STATE_PLAYING':
                    playbackstate = 1
                elif playback_state == 'PLAYBACK_STATE_TRANSITIONING':
                    playbackstate = 2
                elif playback_state == 'PLAYBACK_STATE_PAUSED':
                    playbackstate = 3
                elif playback_state == 'PLAYBACK_STATE_IDLE':
                    playbackstate = 4
                else:
                    playbackstate = 0
                self.setDriver('ST', playbackstate)

                volume = SonosControl.get_groupVolume(self.sonos, self.household, id)
                # List 0=volume, 1=muted, 2=fixed(true/false)
                self.setDriver('SVOL', volume[0])
                self.setDriver('GV0', volume[1])

    def player_volume(self, command):
        print('Volume command: ', command)
        volume = command['value']
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_groupVolume(self.sonos, self.household, id, volume)
                if _status:
                    self.setDriver('SVOL', volume)
                else:
                    print('Error: ' + _status)

    def player_mute(self, command):
        print('Mute Command: ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_groupMute(self.sonos, self.household, id, mute=True)
                if _status:
                    self.setDriver('GV0', 1)
                else:
                    print('Error: ' + _status)

    def player_unmute(self, command):
        print('unMute Command: ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_groupMute(self.sonos, self.household, id, mute=False)
                if _status:
                    self.setDriver('GV0', 0)
                else:
                    print('Error: ' + _status)

    def player_playlist(self, command):
        print('Playlist: ', command)
        playlist = command['value']
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_playlist(self.sonos, id, playlist, self.shuffle)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def player_favorite(self, command):
        print('Favorite: ', command)
        favorite = command['value']
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_favorite(self.sonos, id, favorite)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def player_play(self, command):
        print('Play: ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_play(self.sonos, id)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def player_pause(self, command):
        print('Pause: ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.set_pause(self.sonos, id)
                if _status:
                    self.setDriver('ST', 3)
                else:
                    print('Error: ' + _status)

    def player_skipToPreviousTrack(self, command):
        print('Previous Track ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.skipToPreviousTrack(self.sonos, id)
                if _status:
                    pass
                else:
                    print('Error: ' + _status)


    def player_skipToNextTrack(self, command):
        print('Previous Track ', command)
        for group in self.sonos_groups:
            id = group['id']
            address = str(id.split(':')[1]).lower()
            if address == self.address:
                _status = SonosControl.skipToNextTrack(self.sonos, id)
                if _status:
                    pass
                else:
                    print('Error: ' + _status)

    def player_shuffle_on(self, command):
        print('Shuffle: ', command)
        self.setDriver('GV1', 1)
        self.shuffle = True

    def player_shuffle_off(self, command):
        print('Shuffle: ', command)
        self.setDriver('GV1', 0)
        self.shuffle = False

    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 25},
        {'driver': 'SVOL', 'value': 0, 'uom': 51},
        {'driver': 'GV0', 'value': 0, 'uom': 2},  # Mute/unMute
        {'driver': 'PLAYLST', 'value': 0, 'uom': 25},
        {'driver': 'FAV', 'value': 0, 'uom': 25},
        {'driver': 'GV1', 'value': 0, 'uom': 2}  # Shuffle
    ]

    id = 'PLAYER'

    commands = {
        'SVOL': player_volume,
        'PLAY': player_play,
        'PAUSE': player_pause,
        'PREVIOUS': player_skipToPreviousTrack,
        'NEXT': player_skipToNextTrack,
        'MUTE': player_mute,
        'UNMUTE': player_unmute,
        'PLAYLST': player_playlist,
        'FAV': player_favorite,
        'SHUFFLEON': player_shuffle_on,
        'SHUFFLEOFF': player_shuffle_off
        }
