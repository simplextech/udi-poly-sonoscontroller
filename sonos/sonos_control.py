import socket
from http.client import RemoteDisconnected
import requests
import requests.utils
import urllib3

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

LOGGER = polyinterface.LOGGER


class SonosControl:
    def __init__(self, access_token):
        self.api_host = 'api.ws.sonos.com'
        self.household_url = 'https://' + self.api_host + '/control/api/v1/households'
        self.groups_url = 'https://' + self.api_host + '/control/api/v1/groups/'
        self.players_url = 'https://' + self.api_host + '/control/api/v1/players/'
        self.bearer_token = 'Bearer ' + access_token
        self.headers = {
            'Authorization': self.bearer_token,
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': self.api_host,
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
            'cache-control': "no-cache",
            'Content-Type': "application/json"
        }

    def sonos_get_api(self, url):
        try:
            req = requests.get(url, headers=self.headers)
            if req.status_code == requests.codes.ok:
                if req.json() is not None:
                    return req.json()
                else:
                    LOGGER.error('SonosControl.sonos_get_api: API response was None')
                    return None
        # except RemoteDisconnected as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except ConnectionResetError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except socket.gaierror as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except urllib3.exceptions.NewConnectionError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except requests.exceptions.ConnectionError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        except(ConnectionError, ConnectionResetError, RemoteDisconnected, socket.gaierror, 
            urllib3.exceptions.NewConnectionError, urllib3.exceptions.ConnectionResetError) as Ex:
            LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
            return None

    def sonos_post_api(self, url, payload=None):
        try:
            req = requests.post(url, headers=self.headers, json=payload)
            if req.status_code == requests.codes.ok:
                return True
            else:
                LOGGER.error('SonosControl.sonos_api: ' + str(req.content))
                return False
        # except RemoteDisconnected as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except ConnectionResetError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except socket.gaierror as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except urllib3.exceptions.NewConnectionError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        # except requests.exceptions.ConnectionError as Ex:
        #     LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
        #     return None
        except(ConnectionError, ConnectionResetError, RemoteDisconnected, socket.gaierror, 
            urllib3.exceptions.NewConnectionError, urllib3.exceptions.ConnectionResetError) as Ex:
            LOGGER.error('SonosControl.sonos_api: ' + str(Ex))
            return None

    def get_households(self):
        """
        Get the Household ID's
        """
        r_json = self.sonos_get_api(self.household_url)
        if r_json is not None:
            if len(r_json['households']) > 1:
                household_key = 0
                for household in r_json['households']:
                    household.update({household_key: household['id']})
                    household_key += 1
                    return household
            elif len(r_json['households']) == 1:
                household = {'0': r_json['households'][0]['id']}
                return household
            else:
                household = None
                LOGGER.error("Error sonos_control.get_households")
                return household
        else:
            return None

    def get_groups(self, household):
        """
        Get Household Groups
        """
        groups_url = self.household_url + '/' + household + '/groups'
        r_json = self.sonos_get_api(groups_url)
        if r_json is not None:
            if r_json['groups']:
                return r_json['groups']
            else:
                return None
        else:
            LOGGER.error("Error sonos_control.get_groups")
            return None

    def get_players(self, household):
        """
        Get Household Players
        :param household:
        :return:
        """
        players_url = self.household_url + '/' + household + '/groups'
        r_json = self.sonos_get_api(players_url)
        if r_json is not None:
            if r_json['players']:
                return r_json['players']
            else:
                return None
        else:
            LOGGER.error("Error sonos_control.get_players")
            return None

    def get_favorites(self, household):
        """
        Get Favorites
        """
        favorites_url = self.household_url + '/' + household + '/favorites'
        r_json = self.sonos_get_api(favorites_url)
        if r_json is not None:
            favorites = r_json['items']
            sonos_favorites = {}
            for fav in favorites:
                sonos_favorites.update({fav['id']: fav['name']})
            return sonos_favorites
        else:
            LOGGER.error("Error sonos_control.get_favorites")
            return None

    def get_playlists(self, household):
        """
        Get Playlists
        """
        playlists_url = self.household_url + '/' + household + '/playlists'
        r_json = self.sonos_get_api(playlists_url)
        if r_json is not None:
            playlists = r_json['playlists']
            sonos_playlists = {}
            for pl in playlists:
                sonos_playlists.update({pl['id']: pl['name']})
            return sonos_playlists
        else:
            LOGGER.error("Error sonos_control.get_playlists")
            return None

    def get_group_volume(self, household, group):
        group_volume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        r_json = self.sonos_get_api(group_volume_url)
        if r_json is not None:
            if r_json['volume']:
                # List 0=volume, 1=muted, 2=fixed(true/false)
                volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
                return volume
            else:
                LOGGER.error("Error sonos_control.get_group_volume")
                return None
        else:
            return None

    def get_player_volume(self, player):
        player_volume_url = self.players_url + player + '/playerVolume'
        r_json = self.sonos_get_api(player_volume_url)
        if r_json is not None:
            # List 0=volume, 1=muted, 2=fixed(true/false)
            volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
            if volume is not None:
                return volume
            else:
                LOGGER.error("Error sonos_control.get_player_volume")
                return None
        else:
            return None

    def set_group_volume(self, household, group, volume):
        payload = {"volume": volume}
        set_group_volume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        if self.sonos_post_api(set_group_volume_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_group_volume")
            return False

    def set_group_mute(self, household, group, mute):
        if mute:
            payload = {"muted": True}
        else:
            payload = {"muted": False}

        set_mute_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume/mute'
        if self.sonos_post_api(set_mute_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_group_mute")
            return False

    def set_favorite(self, group, value):
        set_favorite_url = self.groups_url + group + '/favorites'
        payload = {"favoriteId": value,
                   "playOnCompletion": True,
                   "playMode": {"shuffle": False}}
        if self.sonos_post_api(set_favorite_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_favorite")
            return False

    def set_playlist(self, group, value, shuffle):
        set_playlist_url = self.groups_url + group + '/playlists'
        if shuffle:
            payload = {"playlistId": value,
                       "playOnCompletion": True,
                       "playMode": {"shuffle": True}}
        else:
            payload = {"playlistId": value,
                       "playOnCompletion": True,
                       "playMode": {"shuffle": False}}
        if self.sonos_post_api(set_playlist_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_playlist")
            return False

    def set_pause(self, group):
        set_pause_url = self.groups_url + group + '/playback/pause'
        if self.sonos_post_api(set_pause_url, payload=None):
            return True
        else:
            LOGGER.error("sonos_control.set_pause")
            return False

    def set_play(self, group):
        set_play_url = self.groups_url + group + '/playback/play'
        if self.sonos_post_api(set_play_url, payload=None):
            return True
        else:
            LOGGER.error("sonos_control.set_play")
            return False

    def skip_to_previous_track(self, group):
        skip_to_previous_track_url = self.groups_url + group + '/playback/skipToPreviousTrack'
        if self.sonos_post_api(skip_to_previous_track_url, payload=None):
            return True
        else:
            LOGGER.error("sonos_control.skip_to_previous_track")
            return False

    def skip_to_next_track(self, group):
        skip_to_next_track_url = self.groups_url + group + '/playback/skipToNextTrack'
        if self.sonos_post_api(skip_to_next_track_url, payload=None):
            return True
        else:
            LOGGER.error("sonos_control.skip_to_next_track")
            return False

    def set_player_volume(self, player, volume):
        player_volume_url = self.players_url + player + '/playerVolume'
        payload = {"volume": volume}
        if self.sonos_post_api(player_volume_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.player_volume")
            return False

    def set_player_mute(self, player):
        set_player_mute_url = self.players_url + player + '/playerVolume/mute'
        payload = {"muted": True}
        if self.sonos_post_api(set_player_mute_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_player_mute")
            return False

    def set_player_unmute(self, player):
        set_player_unmute_url = self.players_url + player + '/playerVolume/mute'
        payload = {"muted": False}
        if self.sonos_post_api(set_player_unmute_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_player_unmute")
            return False

    def send_voice_rss(self, player, raw_url):
        stream_url = requests.utils.requote_uri(raw_url)
        payload = {
            'name': "Sonos TTS",
            'appId': "net.simplextech",
            'streamUrl': stream_url,
            'clipType': "CUSTOM",
            'priority': "high"
        }
        print("VoiceRSS Payload: " + str(payload))
        audio_clip_url = self.players_url + player + '/audioClip'
        r = requests.post(audio_clip_url, headers=self.headers, json=payload)
        if r.status_code == requests.codes.ok:
            print("Success: " + str(r.content))
            return True
        else:
            print("Error sonos_control.send_voice_rss: " + str(r.content))
            return False
