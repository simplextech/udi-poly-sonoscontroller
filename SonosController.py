#!/usr/bin/env python
import base64
import fileinput
import re
import requests

# import logging
# logging.basicConfig(level=logging.DEBUG)

from sonos import sonos_control, SonosControl
from nodes import group_node, GroupNode
from nodes import player_node, PlayerNode
from nodes import favorite_node, FavoriteNode
from nodes import playlist_node, PlaylistNode
from nodes import group_parent_node, GroupParentNode

try:
    import polyinterface
    CLOUD = False
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True
import sys
import time

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Sonos Controller'
        self.poly.onConfig(self.process_config)
        self.auth_url = 'https://api.sonos.com/login/v3/oauth'
        self.token_url = 'https://api.sonos.com/login/v3/oauth/access'
        self.household_url = 'https://api.ws.sonos.com/control/api/v1/households'
        self.household = {}
        self.sonos = None
        self.server_data = {}
        self.cloud = CLOUD

    def local_get_credentials(self):
        self.server_data = {'clientId': '9b381a14-1ce0-4789-ab69-61aedfda21c6',
                            'clientSecret': '6cd01138-4a40-45b2-808e-6281417b5bea',
                            'url': 'https://pgtest.isy.io/api/oauth/callback',
                            'worker': self.poly.init['worker']}
        if 'worker' in self.server_data:
            return True
        else:
            return False

    # def get_credentials(self):
    #     if 'clientId' in self.poly.init['oauth']:
    #         self.server_data['clientId'] = self.poly.init['oauth']['clientId']
    #     else:
    #         LOGGER.error('Unable to find Client ID in the init data')
    #         return False
    #     if 'clientSecret' in self.poly.init['oauth']:
    #         self.server_data['clientSecret'] = self.poly.init['oauth']['clientSecret']
    #     else:
    #         LOGGER.error('Unable to find Client Secret in the init data')
    #         return False
    #     if 'url' in self.poly.init['oauth']:
    #         self.server_data['url'] = self.poly.init['oauth']['url']
    #     else:
    #         LOGGER.error('Unable to find URL in the init data')
    #         return False
    #     if self.poly.init['worker']:
    #         self.server_data['worker'] = self.poly.init['worker']
    #     else:
    #         return False

    def auth_prompt(self):
        print('------------' + self.server_data['worker'] + '----------------------------')

        _redirect_uri = self.server_data['url']
        redirect_uri = requests.utils.quote(_redirect_uri)

        user_auth_url = self.auth_url + \
                        '?client_id=' + self.server_data['clientId'] + \
                        '&response_type=code' \
                        '&scope=playback-control-all' \
                        '&state=' + self.server_data['worker'] + \
                        '&redirect_uri=' + redirect_uri

        self.addNotice({'myNotice': 'Click <a target="_blank" href="' + user_auth_url + '">here</a> to link your Sonos account'})

    def oauth(self, oauth):
        LOGGER.info('OAUTH Received: {}'.format(oauth))
        if 'code' in oauth:
            if self.get_token(oauth['code']):
                self.removeNoticesAll()
                self.discover()

    def get_token(self, code):
        print('-------- Getting the Sonos Token -----------')
        print('---- Code: ' + code + '----')
        print('---- Client Key: ' + self.server_data['clientId'])
        print('---- Secret: ' + self.server_data['clientSecret'])

        _encode_string = self.server_data['clientId'] + ':' + self.server_data['clientSecret']
        byte_encoded = base64.b64encode(_encode_string.encode('UTF-8'))
        string_encoded = byte_encoded.decode('UTF-8')
        redirect_uri = self.server_data['url'] + '&state=' + self.server_data['worker']

        headers = {'Authorization': 'Basic ' + string_encoded,
                   'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}

        payload = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': redirect_uri}

        r = requests.post(self.token_url, headers=headers, data=payload)
        resp = r.json()

        if r.status_code == requests.codes.ok:
            access_token = resp['access_token']
            refresh_token = resp['refresh_token']
            expires_in = resp['expires_in']

            self.addCustomParam({'access_token': access_token,
                                 'refresh_token': refresh_token,
                                 'expires_in': expires_in})

            self.sonos = SonosControl(access_token)
            return True
        else:
            return False

    def refresh_token(self):
        _encode_string = self.server_data['clientId'] + ':' + self.server_data['clientSecret']
        byte_encoded = base64.b64encode(_encode_string.encode('UTF-8'))
        string_encoded = byte_encoded.decode('UTF-8')

        headers = {'Authorization': 'Basic ' + string_encoded,
                   'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}

        if 'refresh_token' in self.polyConfig['customParams']:
            refresh_token = self.polyConfig['customParams']['refresh_token']
            payload = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}

            r = requests.post(self.token_url, headers=headers, data=payload)
            resp = r.json()

            if r.status_code == requests.codes.ok:
                access_token = resp['access_token']
                refresh_token = resp['refresh_token']
                expires_in = resp['expires_in']

                self.addCustomParam({'access_token': access_token,
                                     'refresh_token': refresh_token,
                                     'expires_in': expires_in})

                self.sonos = SonosControl(access_token)
                return True
            else:
                return False
        else:
            LOGGER.error('Refresh token not in customParams')
            return False

    def start(self):
        LOGGER.info('Started Template NodeServer')
        # self.get_credentials()
        self.local_get_credentials()
        if 'access_token' not in self.polyConfig['customParams']:
            self.auth_prompt()
        else:
            self.removeNoticesAll()
            self.refresh_token()
            self.discover()

    def shortPoll(self):
        # print('Running ShortPoll')
        if self.household is not None:
            for key in self.household:
                household = self.household[key]
                sonos_groups = SonosControl.get_groups(self.sonos, household)
                for group in sonos_groups:
                    id = group['id']
                    address = str(id.split(':')[1]).lower()
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
                    self.nodes[address].setDriver('ST', playbackstate)

                    volume = SonosControl.get_group_volume(self.sonos, household, id)
                    # List 0=volume, 1=muted, 2=fixed(true/false)
                    self.nodes[address].setDriver('SVOL', volume[0], force=True)
                    self.nodes[address].setDriver('GV0', volume[1], force=True)

    def longPoll(self):
        self.refresh_token()

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        if self.sonos is not None:
            self.household = SonosControl.get_households(self.sonos)

        if self.household is not None:
            for key in self.household:
                household = self.household[key]

                # print('Sonos Groups -----------------------------------------------')
                sonos_groups = SonosControl.get_groups(self.sonos, household)
                self.addNode(GroupParentNode(self, 'groups', 'groups', 'Sonos Groups'))

                for group in sonos_groups:
                    # RINCON_7828CA96B78201400:2253119126
                    id = group['id']
                    name = group['name']
                    address = str(id.split(':')[1]).lower()
                    self.addNode(GroupNode(self, 'groups', address, name, self.sonos, sonos_groups, household))
                # print('End ---------------------------------------------------------')


                # print('Sonos Players ------------------------------------------------')
                sonos_players = SonosControl.get_players(self.sonos, household)
                self.addNode(GroupParentNode(self, 'players', 'players', 'Sonos Players'))

                for player in sonos_players:
                    # RINCON_48A6B8A2895201400
                    id = player['id']
                    name = player['name']
                    address = id.split('_')[1][0:-4].lower()
                    self.addNode(PlayerNode(self, 'players', address, name, self.sonos, sonos_players, household))
                # print('End -----------------------------------------------------------')

                """
                Updating of Favorites and Playlists modifies the profile and sends the update
                """
                file_input = 'profile/nls/en_us.txt'

                # Remove PLAY_LIST-NAME Entries
                for line in fileinput.input(file_input, inplace=True, backup='.bak'):
                    if re.match(r'^PLAY_LIST-\d+\s=\s\w+.+', line):
                        pass
                    elif re.match(r'^FAVORITE-\d+\s=\s\w+.+', line):
                        pass
                    else:
                        print(line.rstrip())

                # Add new PLAY_LIST-NAME Entries
                nls_file = open(file_input, 'a')

                # print('Sonos Favorites')
                sonos_favorites = SonosControl.get_favorites(self.sonos, household)
                # self.addNode(FavoriteNode(self, 'favorites', 'favorites', 'Sonos Favorites'))

                for favorite in sonos_favorites:
                    # address = 'fav_' + str(favorite)
                    name = sonos_favorites[favorite]
                    nls_file.write('FAVORITE-' + str(favorite) + ' = ' + name + '\n')
                    # self.addNode(FavoriteNode(self, 'favorites', address, name))
                # print('End------------')

                # print('Sonos Playlists')
                sonos_playlists = SonosControl.get_playlists(self.sonos, household)
                # self.addNode(PlaylistNode(self, 'playlists', 'playlists', 'Sonos Playlists'))

                for playlist in sonos_playlists:
                    # address = 'playlist_' + str(playlist)
                    name = sonos_playlists[playlist]
                    nls_file.write('PLAY_LIST-' + str(playlist) + ' = ' + name + '\n')
                    # self.addNode(PlaylistNode(self, 'playlists', address, name))
                # print('End------------')

                nls_file.close()
                self.poly.installprofile()

    def delete(self):
        LOGGER.info('Removing SonosController Nodeserver')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def check_params(self):
        pass

        # self.addNotice('Hello Friends! (with key)','hello')
        # self.addNotice('Hello Friends! (without key)')
        # default_user = "YourUserName"
        # default_password = "YourPassword"
        # if 'user' in self.polyConfig['customParams']:
        #     self.user = self.polyConfig['customParams']['user']
        # else:
        #     self.user = default_user
        #     LOGGER.error('check_params: user not defined in customParams, please add it.  Using {}'.format(self.user))
        #     st = False
        #
        # if 'password' in self.polyConfig['customParams']:
        #     self.password = self.polyConfig['customParams']['password']
        # else:
        #     self.password = default_password
        #     LOGGER.error('check_params: password not defined in customParams, please add it.  Using {}'.format(self.password))
        #     st = False
        #
        # # Make sure they are in the params
        # self.addCustomParam({'password': self.password, 'user': self.user, 'some_example': '{ "type": "TheType", "host": "host_or_IP", "port": "port_number" }'})
        #
        # # Add a notice if they need to change the user/password from the default.
        # # if self.user == default_user or self.password == default_password:
        #     # This doesn't pass a key to test the old way.
        #     # self.addNotice('Please set proper user and password in configuration page, and restart this nodeserver')
        # # This one passes a key to test the new way.
        # # self.addNotice('This is a test','test')

    def remove_notice_test(self,command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    id = 'controller'
    commands = {
        # 'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        # 'REMOVE_NOTICES_ALL': remove_notices_all,
        # 'REMOVE_NOTICE_TEST': remove_notice_test
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('Template')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
