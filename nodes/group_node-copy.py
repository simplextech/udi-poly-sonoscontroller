try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

# from sonos import SonosControl as SonosControl
from sonos import SonosControl

LOGGER = polyinterface.LOGGER


class GroupNode(polyinterface.Node):
    # def __init__(self, controller, primary, address, name, sonos, sonos_groups, household):
    def __init__(self, controller, primary, address, name, sonos_groups, household):
        super(GroupNode, self).__init__(controller, primary, address, name)
        self.access_token = None
        self.sonos = None
        # self.sonos = sonos
        self.sonos_groups = sonos_groups
        self.household = household
        self.shuffle = False

    def start(self):
        # print('Starting Group: ' + self.name + ' ------------------')
        # print(self.sonos_groups)
        self.access_token = self.controller.polyConfig['customParams']['access_token']
        self.sonos = SonosControl(self.access_token)

        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()

            if group_address == self.address:
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

                volume = SonosControl.get_group_volume(self.sonos, self.household, group_id)
                # List 0=volume, 1=muted, 2=fixed(true/false)
                self.setDriver('SVOL', volume[0], force=True)
                if volume[1] == 'true':
                    self.setDriver('GV0', 1, force=True)
                else:
                    self.setDriver('GV0', 0, force=True)

    def group_volume(self, command):
        # print('Volume command: ', command)
        volume = command['value']
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_group_volume(self.sonos, self.household, group_id, volume)
                if _status:
                    self.setDriver('SVOL', volume)
                else:
                    print('Error: ' + _status)

    def group_mute(self, command):
        # print('Mute Command: ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_group_mute(self.sonos, self.household, group_id, mute=True)
                if _status:
                    self.setDriver('GV0', 1)
                else:
                    print('Error: ' + _status)

    def group_unmute(self, command):
        # print('unMute Command: ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_group_mute(self.sonos, self.household, group_id, mute=False)
                if _status:
                    self.setDriver('GV0', 0)
                else:
                    print('Error: ' + _status)

    def group_playlist(self, command):
        # print('Playlist: ', command)
        playlist = command['value']
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_playlist(self.sonos, group_id, playlist, self.shuffle)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def group_favorite(self, command):
        # print('Favorite: ', command)
        favorite = command['value']
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_favorite(self.sonos, group_id, favorite)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def group_play(self, command):
        # print('Play: ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_play(self.sonos, group_id)
                if _status:
                    self.setDriver('ST', 1)
                else:
                    print('Error: ' + _status)

    def group_pause(self, command):
        # print('Pause: ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.set_pause(self.sonos, group_id)
                if _status:
                    self.setDriver('ST', 3)
                else:
                    print('Error: ' + _status)

    def group_skip_to_previous_track(self, command):
        # print('Previous Track ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.skipToPreviousTrack(self.sonos, group_id)
                if _status:
                    pass
                else:
                    print('Error: ' + _status)

    def group_skip_to_next_track(self, command):
        # print('Previous Track ', command)
        for group in self.sonos_groups:
            # group_id = group['id']
            # address = str(group_id.split(':')[1]).lower()

            group_id = group['id']
            coordinator_id = group['coordinatorId']
            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
            if group_address == self.address:
                _status = SonosControl.skipToNextTrack(self.sonos, group_id)
                if _status:
                    pass
                else:
                    print('Error: ' + _status)

    def group_shuffle_on(self, command):
        # print('Shuffle: ', command)
        self.setDriver('GV1', 1)
        self.shuffle = True

    def group_shuffle_off(self, command):
        # print('Shuffle: ', command)
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

    id = 'GROUP'

    commands = {
        'SVOL': group_volume,
        'PLAY': group_play,
        'PAUSE': group_pause,
        'PREVIOUS': group_skip_to_previous_track,
        'NEXT': group_skip_to_next_track,
        'MUTE': group_mute,
        'UNMUTE': group_unmute,
        'PLAYLST': group_playlist,
        'FAV': group_favorite,
        'SHUFFLEON': group_shuffle_on,
        'SHUFFLEOFF': group_shuffle_off
        }