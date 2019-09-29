
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

from sonos import SonosControl as SonosControl

class PlaylistNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(PlaylistNode, self).__init__(controller, primary, address, name)
        access_token = self.polyConfig['customParams']['access_token']
        self.sonos = SonosControl(access_token)

    def start(self):
        print('Starting Group: ' + self.name + ' ------------------')

        # r = requests.get('http://192.168.1.10:5005/zones')
        # _zones = r.json()
        # if len(_zones) > 0:
        #     for z in _zones:
        #         _uuid = str(z['coordinator']['uuid']).lower().split('_')[1]
        #         zone_uuid = _uuid[0:-4]
        #         if zone_uuid == self.address:
        #             _playbackState = str(z['coordinator']['state']['playbackState'])
        #             if _playbackState == 'PLAYING':
        #                 playbackstate = 1
        #             elif _playbackState == 'TRANSITIONING':
        #                 playbackstate = 2
        #             elif _playbackState == 'PAUSED':
        #                 playbackstate = 3
        #             elif _playbackState == 'STOPPED':
        #                 playbackstate = 4
        #             else:
        #                 playbackstate = 0
        #
        #             self.setDriver('ST', playbackstate)
        #
        #             _volume = z['coordinator']['state']['volume']
        #             self.setDriver('SVOL', _volume)

    # def player_volume(self, command):
    #     # print('Volume command: ', command)
    #     player = self.name
    #     val = command['value']
    #     r = requests.get('http://192.168.1.10:5005/' + player + '/volume/' + val)
    #     resp = r.json()
    #     if resp['status'] == 'success':
    #         self.setDriver('SVOL', val)
    #
    # def player_playlist(self, command):
    #     print('Playlist: ', command)
    #     pl_number = int(command['value']) - 1
    #     r = requests.get('http://192.168.1.10:5005/playlists')
    #     _play_list = r.json()
    #     print('Playlist Number: ' + str(pl_number))
    #     print('Sonos Playlist: ' + _play_list[pl_number])
    #     playlist = _play_list[pl_number]
    #     self.controller.play_playlist(self.name, playlist)
    #
    # def player_favorite(self, command):
    #     print('Favorite: ', command)
    #     fav_number = int(command['value']) - 1
    #     r = requests.get('http://192.168.1.10:5005/favorites')
    #     _favorites = r.json()
    #     print('Favorite Number: ' + str(fav_number))
    #     print('Sonos Playlist: ' + _favorites[fav_number])
    #     favorite = _favorites[fav_number]
    #     self.controller.play_favorite(self.name, favorite)


    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
                {'driver': 'ST', 'value': 0, 'uom': 25},
                {'driver': 'SVOL', 'value': 0, 'uom': 51},
                {'driver': 'GV01', 'value': 0, 'uom': 25},
                {'driver': 'GV02', 'value': 0, 'uom': 25}
            ]

    id = 'PLAYER'

    commands = {
                    # 'DON': setOn, 'DOF': setOff
                    # 'SVOL': player_volume, 'GV01': player_playlist,
                    # 'GV02': player_favorite
                }
