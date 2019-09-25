#!/usr/bin/env python

import fileinput
import re

import requests

from sonos import sonos_control, SonosControl
from nodes import group_node, GroupNode
from nodes import player_node, PlayerNode
from nodes import favorite_node, FavoriteNode
from nodes import playlist_node, PlaylistNode
from nodes import group_parent_node, GroupParentNode

try:
    import polyinterface
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
        # self.poly.onConfig(self.process_config)
        self.auth_host = 'api.sonos.com'
        self.api_host = 'api.ws.sonos.com'
        # self.client_key = '9b381a14-1ce0-4789-ab69-61aedfda21c6'
        # self.client_secret = '6cd01138-4a40-45b2-808e-6281417b5bea'
        # self.redirect_uri = 'https://webhook.site/a45c16b3-1db8-44de-bd05-985956bfa461'
        self.scope = 'playback-control-all'
        self.auth_url = 'https://' + self.auth_host + '/login/v3/oauth'
        self.token_url = 'https://' + self.auth_host + '/login/v3/oauth/access'
        self.household_url = 'https://' + self.api_host + '/control/api/v1/households'
        self.household = {}
        self.sonos = SonosControl()
        self.server_data = {}
        self.worker = self.poly.init['worker']
        self.cloud = CLOUD

    def _get_credentials(self):
        if 'clientId' in self.poly.init['oauth']:
            self.server_data['clientId'] = self.poly.init['oauth']['clientId']
        else:
            LOGGER.error('Unable to find Client ID in the init data')
            return False
        if 'clientSecret' in self.poly.init['oauth']:
            self.server_data['clientSecret'] = self.poly.init['oauth']['clientSecret']
        else:
            LOGGER.error('Unable to find Client Secret in the init data')
            return False
        if 'url' in self.poly.init['oauth']:
            self.server_data['url'] = self.poly.init['oauth']['url']
        else:
            LOGGER.error('Unable to find URL in the init data')
            return False

    def _auth_prompt(self):
        _worker = self.worker
        print('------------' + _worker + '----------------------------')
        _clientId = '27474fa1-1a1e-4cc0-a101-61e486bfcd0d'
        # _clientId = self.server_data['clientId']

        _redirect_url = requests.utils.quote('https://pgtest.isy.io')
        # _redirect_url = self.server_data['url']
        _user_auth_url = 'https://api.sonos.com/login/v3/oauth?' \
                         'client_id=' + _clientId + \
                         '&response_type=code' \
                         '&state=' + _worker + '' \
                         '&scope=playback-control-all' \
                         '&redirect_uri=' + _redirect_url

        self.addNotice({'myNotice': 'Click <a target="_blank" href="' + _user_auth_url + '">here</a> to link your Sonos account'})

    def oauth(self, oauth):
        LOGGER.info('OAUTH Received: {}'.format(oauth))
        if 'code' in oauth:
            if self._getToken(oauth['code']):
                self.removeNoticesAll()
                self.discover()

    def start(self):
        LOGGER.info('Started Template NodeServer')
        self.removeNoticesAll()
        self._auth_prompt()
        self.check_params()
        self.discover()
        self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def shortPoll(self):
        print('Running ShortPoll  ----------------------------')
        if self.household is not None:
            for key in self.household:
                household = self.household[key]
                sonos_groups = SonosControl.get_groups(self.sonos, household)
                for group in sonos_groups:
                    print(group)
                    id = group['id']
                    address = str(id.split(':')[1]).lower()
                    playback_state = group['playbackState']
                    print(playback_state)

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
                    self.nodes[address].setDriver('SVOL', volume[0])
                    self.nodes[address].setDriver('GV0', volume[1])

    def longPoll(self):
        pass

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        self.household = SonosControl.get_households(self.sonos)
        if self.household is not None:
            for key in self.household:
                household = self.household[key]


                print('Sonos Groups -----------------------------------------------')
                sonos_groups = SonosControl.get_groups(self.sonos, household)
                self.addNode(GroupParentNode(self, 'groups', 'groups', 'Sonos Groups'))

                for group in sonos_groups:
                    # RINCON_7828CA96B78201400:2253119126
                    id = group['id']
                    name = group['name']
                    address = str(id.split(':')[1]).lower()
                    self.addNode(GroupNode(self, 'groups', address, name, sonos_groups, household))
                print('End ---------------------------------------------------------')


                print('Sonos Players ------------------------------------------------')
                sonos_players = SonosControl.get_players(self.sonos, household)
                self.addNode(GroupParentNode(self, 'players', 'players', 'Sonos Players'))

                for player in sonos_players:
                    # RINCON_48A6B8A2895201400
                    id = player['id']
                    name = player['name']
                    address = id.split('_')[1][0:-4].lower()
                    self.addNode(PlayerNode(self, 'players', address, name, sonos_players, household))
                print('End -----------------------------------------------------------')

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

                print('Sonos Favorites')
                sonos_favorites = SonosControl.get_favorites(self.sonos, household)
                # self.addNode(FavoriteNode(self, 'favorites', 'favorites', 'Sonos Favorites'))

                for favorite in sonos_favorites:
                    # address = 'fav_' + str(favorite)
                    name = sonos_favorites[favorite]
                    nls_file.write('FAVORITE-' + str(favorite) + ' = ' + name + '\n')
                    # self.addNode(FavoriteNode(self, 'favorites', address, name))
                print('End------------')

                print('Sonos Playlists')
                sonos_playlists = SonosControl.get_playlists(self.sonos, household)
                # self.addNode(PlaylistNode(self, 'playlists', 'playlists', 'Sonos Playlists'))

                for playlist in sonos_playlists:
                    # address = 'playlist_' + str(playlist)
                    name = sonos_playlists[playlist]
                    nls_file.write('PLAY_LIST-' + str(playlist) + ' = ' + name + '\n')
                    # self.addNode(PlaylistNode(self, 'playlists', address, name))
                print('End------------')

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
        # self.addNotice('Hello Friends! (with key)','hello')
        # self.addNotice('Hello Friends! (without key)')
        default_user = "YourUserName"
        default_password = "YourPassword"
        if 'user' in self.polyConfig['customParams']:
            self.user = self.polyConfig['customParams']['user']
        else:
            self.user = default_user
            LOGGER.error('check_params: user not defined in customParams, please add it.  Using {}'.format(self.user))
            st = False

        if 'password' in self.polyConfig['customParams']:
            self.password = self.polyConfig['customParams']['password']
        else:
            self.password = default_password
            LOGGER.error('check_params: password not defined in customParams, please add it.  Using {}'.format(self.password))
            st = False

        # Make sure they are in the params
        self.addCustomParam({'password': self.password, 'user': self.user, 'some_example': '{ "type": "TheType", "host": "host_or_IP", "port": "port_number" }'})

        # Add a notice if they need to change the user/password from the default.
        # if self.user == default_user or self.password == default_password:
            # This doesn't pass a key to test the old way.
            # self.addNotice('Please set proper user and password in configuration page, and restart this nodeserver')
        # This one passes a key to test the new way.
        # self.addNotice('This is a test','test')

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
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all,
        'REMOVE_NOTICE_TEST': remove_notice_test
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
