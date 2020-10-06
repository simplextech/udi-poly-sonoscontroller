#!/usr/bin/env python
import base64
import fileinput
import re
import requests
import requests.utils
import sys
import time

from sonos import SonosControl
from nodes import GroupNode
from nodes import PlayerNode
from nodes import GroupParentNode


try:
    import polyinterface
    CLOUD = False
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Sonos Controller'
        # self.poly.onConfig(self.process_config)
        self.auth_url = 'https://api.sonos.com/login/v3/oauth'
        self.token_url = 'https://api.sonos.com/login/v3/oauth/access'
        self.household_url = 'https://api.ws.sonos.com/control/api/v1/households'
        self.household = {}
        self.SonosControl = None
        self.server_data = {}
        self.cloud = CLOUD
        self.disco = 0

    def start(self):
        LOGGER.info('Started SonosController NodeServer')
        self.check_params()
        if self.get_credentials():
            if self.refresh_token():
                self.removeNoticesAll()
                self.discover()
            else:
                self.auth_prompt()
        else:
            self.auth_prompt()

    def get_credentials(self):
        LOGGER.info('---- Environment: ' + self.poly.stage + ' ----')

        if self.poly.stage == 'test':
            if 'clientId' in self.poly.init['oauth']['test']:
                self.server_data['clientId'] = self.poly.init['oauth']['test']['clientId']
            else:
                LOGGER.error('Unable to find Client ID in the init data')
                return False
            if 'secret' in self.poly.init['oauth']['test']:
                self.server_data['clientSecret'] = self.poly.init['oauth']['test']['secret']
            else:
                LOGGER.error('Unable to find Client Secret in the init data')
                return False
            if 'redirectUrl' in self.poly.init['oauth']['test']:
                self.server_data['url'] = self.poly.init['oauth']['test']['redirectUrl']
            else:
                LOGGER.error('Unable to find URL in the init data')
                return False
            if self.poly.init['worker']:
                self.server_data['worker'] = self.poly.init['worker']
            else:
                return False
            return True
        elif self.poly.stage == 'prod':
            if 'clientId' in self.poly.init['oauth']['prod']:
                self.server_data['clientId'] = self.poly.init['oauth']['prod']['clientId']
            else:
                LOGGER.error('Unable to find Client ID in the init data')
                return False
            if 'secret' in self.poly.init['oauth']['test']:
                self.server_data['clientSecret'] = self.poly.init['oauth']['prod']['secret']
            else:
                LOGGER.error('Unable to find Client Secret in the init data')
                return False
            if 'redirectUrl' in self.poly.init['oauth']['test']:
                self.server_data['url'] = self.poly.init['oauth']['prod']['redirectUrl']
            else:
                LOGGER.error('Unable to find URL in the init data')
                return False
            if self.poly.init['worker']:
                self.server_data['worker'] = self.poly.init['worker']
            else:
                return False
            return True

    def auth_prompt(self):
        _redirect_uri = self.server_data['url']
        redirect_uri = requests.utils.quote(_redirect_uri)

        user_auth_url = self.auth_url + \
            '?client_id=' + self.server_data['clientId'] + \
            '&response_type=code' \
            '&scope=playback-control-all' \
            '&state=' + self.server_data['worker'] + \
            '&redirect_uri=' + redirect_uri

        self.addNotice(
            {'myNotice': 'Click <a href="' + user_auth_url + '">here</a> to link your Sonos account'})

    def oauth(self, oauth):
        LOGGER.info('OAUTH Received: {}'.format(oauth))
        if 'code' in oauth:
            if self.get_token(oauth['code']):
                self.remove_notices_all()
                self.discover()

    def get_token(self, code):
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

            cust_data = {'access_token': access_token,
                         'refresh_token': refresh_token,
                         'expires_in': expires_in}

            self.saveCustomData(cust_data)
            self.SonosControl = SonosControl(access_token)
            return True
        else:
            return False

    def refresh_token(self):
        _encode_string = self.server_data['clientId'] + ':' + self.server_data['clientSecret']
        byte_encoded = base64.b64encode(_encode_string.encode('UTF-8'))
        string_encoded = byte_encoded.decode('UTF-8')

        headers = {'Authorization': 'Basic ' + string_encoded,
                   'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}

        if 'refresh_token' in self.polyConfig['customData']:
            refresh_token = self.polyConfig['customData']['refresh_token']

            payload = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}

            r = requests.post(self.token_url, headers=headers, data=payload)
            resp = r.json()

            if r.status_code == requests.codes.ok:
                access_token = resp['access_token']
                refresh_token = resp['refresh_token']
                expires_in = resp['expires_in']

                cust_data = {'access_token': access_token,
                             'refresh_token': refresh_token,
                             'expires_in': expires_in}

                self.saveCustomData(cust_data)
                self.SonosControl = SonosControl(access_token)

                self.removeNoticesAll()
                return True
            else:
                return False
        else:
            LOGGER.error('Refresh token not in customData')
            return False

    def shortPoll(self):
        if self.disco == 1:
            if self.household is not None:
                for key in self.household:
                    household = self.household[key]
                    try:
                        sonos_groups = self.SonosControl.get_groups(household)
                        if sonos_groups is not None:
                            for group in sonos_groups:
                                group_id = group['id']
                                coordinator_id = group['coordinatorId']
                                group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
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

                                if self.getNode[group_address]:
                                    self.nodes[group_address].setDriver('ST', playbackstate)
                                else:
                                    LOGGER.error("shortPoll:playbackstate: Group does not exist")

                                # List 0=volume, 1=muted, 2=fixed(true/false)
                                group_volume = self.SonosControl.get_group_volume(household, group_id)
                                if group_volume is not None:
                                    if self.getNode[group_address]:
                                        self.nodes[group_address].setDriver('SVOL', group_volume[0])
                                        if group_volume[1]:
                                            self.nodes[group_address].setDriver('GV0', 1)
                                        else:
                                            self.nodes[group_address].setDriver('GV0', 0)
                                    else:
                                        LOGGER.error("shortPoll:group_volume: Group does not exist")
                                else:
                                    LOGGER.error("shortPoll:group_volume: None")
                        else:
                            LOGGER.error("shortPoll:sonos_groups: Sonos Groups is None")
                    except KeyError as ex:
                        LOGGER.error('shortPoll:sonos_groups: Sonos Groups Error: ' + str(ex))

                    try:
                        sonos_players = self.SonosControl.get_players(household)
                        if sonos_players is not None:
                            for player in sonos_players:
                                player_id = player['id']
                                player_address = 'p' + player_id.split('_')[1][0:-5].lower()
                                player_volume = self.SonosControl.get_player_volume(player_id)
                                # List 0=volume, 1=muted, 2=fixed(true/false)
                                if player_volume is not None:
                                    if self.getNode[player_address]:
                                        self.nodes[player_address].setDriver('SVOL', player_volume[0])
                                        if player_volume[1]:
                                            self.nodes[player_address].setDriver('GV0', 1)
                                        else:
                                            self.nodes[player_address].setDriver('GV0', 0)
                                    else:
                                        LOGGER.error("shortPoll: Player node does not exist")
                                else:
                                    LOGGER.error("shortPoll: SonosControl.get_player_volume is None")
                        else:
                            LOGGER.error("shortPoll: SonosControl.get_players is None")
                    except KeyError as ex:
                        LOGGER.error("shortPoll Get Players: " + str(ex))

    def longPoll(self):
        self.refresh_token()

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def voice_rss(self):
        if 'api_key' not in self.polyConfig['customParams']:
            self.addCustomParam({'api_key': 'none'})
            time.sleep(2)
        if 'language' not in self.polyConfig['customParams']:
            self.addCustomParam({'language': 'en-us'})
            time.sleep(2)
        if 'codec' not in self.polyConfig['customParams']:
            self.addCustomParam({'codec': 'mp3'})
            time.sleep(2)
        if 'format' not in self.polyConfig['customParams']:
            self.addCustomParam({'format': '24khz_16bit_stereo'})
            time.sleep(2)

    def say_tts_params(self):
        if 'SAY_TTS-1' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-1': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-2' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-2': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-3' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-3': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-4' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-4': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-5' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-5': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-6' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-6': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-7' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-7': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-8' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-8': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-9' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-9': 'empty'})
            time.sleep(2)
        if 'SAY_TTS-10' not in self.polyConfig['customParams']:
            self.addCustomParam({'SAY_TTS-10': 'empty'})
            time.sleep(2)

    def update_nls(self):
        """
        Updating of Playlists modifies the profile and sends the update
        """
        file_input = 'profile/nls/en_us.txt'

        if self.household is not None:
            for key in self.household:
                household = self.household[key]

                # Remove PLAY_LIST-NAME, FAVORITE-, SAY_TTS- Entries
                for line in fileinput.input(file_input, inplace=True, backup='.bak'):
                    if re.match(r'^PLAY_LIST-\d+\s=\s\w+.+', line):
                        pass
                    elif re.match(r'^FAVORITE-\d+\s=\s\w+.+', line):
                        pass
                    elif re.match(r'^SAY_TTS-\d+\s=\s\w+.+', line):
                        pass
                    else:
                        print(line.rstrip())

                # Open NLS File in Append Mode
                nls_file = open(file_input, 'a')

                # print('Sonos Playlists')
                sonos_playlists = self.SonosControl.get_playlists(household)
                for playlist in sonos_playlists:
                    name = sonos_playlists[playlist]
                    nls_file.write('PLAY_LIST-' + str(playlist) + ' = ' + name + '\n')

                # print('Sonos Favorites')
                sonos_favorites = self.SonosControl.get_favorites(household)
                for favorite in sonos_favorites:
                    name = sonos_favorites[favorite]
                    nls_file.write('FAVORITE-' + str(favorite) + ' = ' + name + '\n')

                # Add new SAY_TTS Entries
                if 'SAY_TTS-1' in self.polyConfig['customParams']:
                    say_tts1 = self.polyConfig['customParams']['SAY_TTS-1']
                    nls_file.write('SAY_TTS-1' + ' = ' + say_tts1 + '\n')
                if 'SAY_TTS-2' in self.polyConfig['customParams']:
                    say_tts2 = self.polyConfig['customParams']['SAY_TTS-2']
                    nls_file.write('SAY_TTS-2' + ' = ' + say_tts2 + '\n')
                if 'SAY_TTS-3' in self.polyConfig['customParams']:
                    say_tts3 = self.polyConfig['customParams']['SAY_TTS-3']
                    nls_file.write('SAY_TTS-3' + ' = ' + say_tts3 + '\n')
                if 'SAY_TTS-4' in self.polyConfig['customParams']:
                    say_tts4 = self.polyConfig['customParams']['SAY_TTS-4']
                    nls_file.write('SAY_TTS-4' + ' = ' + say_tts4 + '\n')
                if 'SAY_TTS-5' in self.polyConfig['customParams']:
                    say_tts5 = self.polyConfig['customParams']['SAY_TTS-5']
                    nls_file.write('SAY_TTS-5' + ' = ' + say_tts5 + '\n')
                if 'SAY_TTS-6' in self.polyConfig['customParams']:
                    say_tts6 = self.polyConfig['customParams']['SAY_TTS-6']
                    nls_file.write('SAY_TTS-6' + ' = ' + say_tts6 + '\n')
                if 'SAY_TTS-7' in self.polyConfig['customParams']:
                    say_tts7 = self.polyConfig['customParams']['SAY_TTS-7']
                    nls_file.write('SAY_TTS-7' + ' = ' + say_tts7 + '\n')
                if 'SAY_TTS-8' in self.polyConfig['customParams']:
                    say_tts8 = self.polyConfig['customParams']['SAY_TTS-8']
                    nls_file.write('SAY_TTS-8' + ' = ' + say_tts8 + '\n')
                if 'SAY_TTS-9' in self.polyConfig['customParams']:
                    say_tts9 = self.polyConfig['customParams']['SAY_TTS-9']
                    nls_file.write('SAY_TTS-9' + ' = ' + say_tts9 + '\n')
                if 'SAY_TTS-10' in self.polyConfig['customParams']:
                    say_tts10 = self.polyConfig['customParams']['SAY_TTS-10']
                    nls_file.write('SAY_TTS-10' + ' = ' + say_tts10 + '\n')

                nls_file.close()

    def discover(self, *args, **kwargs):
        if self.SonosControl is not None:
            self.household = self.SonosControl.get_households()

        if self.household is not None:
            for key in self.household:
                household = self.household[key]

                try:
                    sonos_groups = self.SonosControl.get_groups(household)
                    if sonos_groups is not None:
                        self.addNode(GroupParentNode(self, 'groups', 'groups', 'Sonos Groups'))
                        time.sleep(2)
                        for group in sonos_groups:
                            coordinator_id = group['coordinatorId']
                            group_address = 'g' + coordinator_id.split('_')[1][0:-5].lower()
                            group_name = group['name'].split("+")[0]
                            self.addNode(GroupNode(self, 'groups', group_address, group_name, sonos_groups, household))
                            time.sleep(2)
                    else:
                        LOGGER.error("SonosControl.get_groups is None")
                except KeyError as ex:
                    LOGGER.error("SonosControl.get_groups Error: " + str(ex))

                try:
                    sonos_players = self.SonosControl.get_players(household)
                    if sonos_players is not None:
                        self.addNode(GroupParentNode(self, 'players', 'players', 'Sonos Players'))
                        time.sleep(2)
                        for player in sonos_players:
                            player_id = player['id']
                            name = player['name']
                            player_address = 'p' + player_id.split('_')[1][0:-5].lower()
                            self.addNode(PlayerNode(self, 'players', player_address, name, sonos_players, household))
                            time.sleep(2)
                    else:
                        LOGGER.error("SonosControl.get_players is None")
                except KeyError as ex:
                    LOGGER.error("SonosControl.get_players Error: " + str(ex))

        self.update_nls()
        self.poly.installprofile()
        time.sleep(3)
        self.disco = 1
        self.setDriver('ST', 1, force=True)

    def delete(self):
        LOGGER.info('Removing SonosController Nodeserver')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config))
        LOGGER.info("process_config: Exit")

    def check_params(self):
        self.voice_rss()
        time.sleep(2)
        self.say_tts_params()
        time.sleep(2)

    def remove_notice_test(self, command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        self.update_nls()
        st = self.poly.installprofile()
        return st

    id = 'controller'
    commands = {
        # 'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('SonosController')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
