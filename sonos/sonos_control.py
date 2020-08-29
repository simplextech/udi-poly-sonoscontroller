from http.client import RemoteDisconnected
import requests

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
        except RemoteDisconnected as Ex:
            LOGGER.error('SonosControl.sonos_api: ' + Ex)
            return None

    def sonos_post_api(self, url, payload=None):
        try:
            req = requests.post(url, headers=self.headers, json=payload)
            if req.status_code == requests.codes.ok:
                return True
            else:
                LOGGER.error('SonosControl.sonos_api: ' + req.json())
                return False
        except RemoteDisconnected as Ex:
            LOGGER.error('SonosControl.sonos_post_api: ' + Ex)
            return False

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
                LOGGER.error("Error sonos_control.get_households: " + r_json)
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
            LOGGER.error("Error sonos_control.get_groups: " + r_json)
            return None

    def get_players(self, household):
        """
        Get Househole Players
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
            LOGGER.error("Error sonos_control.get_players: " + r_json)
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
            LOGGER.error("Error sonos_control.get_favoritess: " + r_json)
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
            LOGGER.error("Error sonos_control.get_playlists: " + r_json)
            return None

    def get_group_volume(self, household, group):
        group_volume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        r_json = self.sonos_get_api(group_volume_url)
        if r_json is not None:
            if r_json['volume']:
                print("====================================================")
                print(r_json)
                print("====================================================")
                # List 0=volume, 1=muted, 2=fixed(true/false)
                volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
                return volume
            else:
                LOGGER.error("Error sonos_control.get_group_volume: " + r_json)
                return None
        else:
            return None

    def get_player_volume(self, player):
        player_volume_url = self.players_url + player + '/playerVolume'
        # r = requests.get(player_volume_url, headers=self.headers)
        # r_json = r.json()
        r_json = self.sonos_get_api(player_volume_url)
        if r_json is not None:
            # List 0=volume, 1=muted, 2=fixed(true/false)
            volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
            if volume is not None:
                return volume
            else:
                LOGGER.error("Error sonos_control.get_player_volume: " + r_json)
                return None
        else:
            return None

    def set_group_volume(self, household, group, volume):
        payload = {"volume": volume}
        set_group_volume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        # r = requests.post(set_group_volume_url, headers=self.headers, json=payload)
        # if r.status_code == requests.codes.ok:
        #     return True
        # else:
        #     print("sonos_control.set_group_volume: " + str(r.content))
        #     return False
        # r_json = self.sonos_post_api(set_group_volume_url, payload=payload)
        # if r_json is not None:
        #     return True
        if self.sonos_post_api(set_group_volume_url, payload=payload):
            return True
        else:
            LOGGER.error("sonos_control.set_group_volume")
            return False

    def set_group_mute(self, household, group, mute):
        if mute:
            # payload = "{\n\t\"muted\": true\n}"
            payload = {"muted": True}
        else:
            # payload = "{\n\t\"muted\": false\n}"
            payload = {"muted": False}

        set_mute_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume/mute'
        # r = requests.post(set_mute_url, headers=self.headers, data=payload)
        # if r.status_code == requests.codes.ok:
        #     print(r.content)
        #     return True
        # else:
        #     print("Error sonos_control.set_group_mute: " + str(r.content))
        #     return False
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
        r = requests.post(set_pause_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.set_pause: " + str(r.content))
            return False

    def set_play(self, group):
        set_play_url = self.groups_url + group + '/playback/play'
        r = requests.post(set_play_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.set_play: " + str(r.content))
            return False

    def skip_to_previous_track(self, group):
        set_play_url = self.groups_url + group + '/playback/skip_to_previous_track'
        r = requests.post(set_play_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.skip_to_previous_track: " + str(r.content))
            return False

    def skip_to_next_track(self, group):
        set_play_url = self.groups_url + group + '/playback/skip_to_next_track'
        r = requests.post(set_play_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.skip_to_next_track: " + str(r.content))
            return False



    def set_player_volume(self, player, volume):
        payload = "{\r\n  \"volume\": " + volume + "\r\n}"
        player_volume_url = self.players_url + player + '/playerVolume'
        r = requests.post(player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.set_player_volume: " + str(r.content))
            return False

    def set_player_mute(self, player):
        payload = "{\r\n  \"muted\": true\r\n}"
        set_player_volume_url = self.players_url + player + '/playerVolume/mute'
        r = requests.post(set_player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.set_player_mute: " + str(r.content))
            return False

    def set_player_unmute(self, player):
        payload = "{\r\n  \"muted\": false\r\n}"
        set_player_volume_url = self.players_url + player + '/playerVolume/mute'
        r = requests.post(set_player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            print("Error sonos_control.set_player_unmute: " + str(r.content))
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
