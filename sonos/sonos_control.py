import requests


class SonosControl:
    def __init__(self, access_token):
        # self.auth_host = 'api.sonos.com'
        self.api_host = 'api.ws.sonos.com'
        # self.client_key = '9b381a14-1ce0-4789-ab69-61aedfda21c6'
        # self.client_secret = '6cd01138-4a40-45b2-808e-6281417b5bea'
        # self.redirect_uri = 'https://webhook.site/a45c16b3-1db8-44de-bd05-985956bfa461'
        # self.scope = 'playback-control-all'
        # self.auth_url = 'https://' + self.auth_host + '/login/v3/oauth'
        # self.token_url = 'https://' + self.auth_host + '/login/v3/oauth/access'
        self.household_url = 'https://' + self.api_host + '/control/api/v1/households'
        self.groups_url = 'https://' + self.api_host + '/control/api/v1/groups/'
        self.players_url = 'https://' + self.api_host + '/control/api/v1/players/'
        # self.household = None

        self.bearer_token = 'Bearer ' + access_token
        self.headers = {
            'Authorization': self.bearer_token,
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': self.api_host,
            'Accept-Encoding': "gzip, deflate",
            'Connection': "keep-alive",
            'cache-control': "no-cache"
        }

    def get_households(self):
        """
        Get the Household ID's
        """
        # household = {}
        r = requests.get(self.household_url, headers=self.headers)
        r_json = r.json()
        if len(r_json['households']) > 1:
            household_key = 0
            for household in r_json['households']:
                # print(household['id'])
                household.update({household_key: household['id']})
                household_key += 1
                return household
        elif len(r_json['households']) == 1:
            # print(r_json['households'][0]['id'])
            household = {'0': r_json['households'][0]['id']}
            return household
        else:
            household = None
            return household

    def get_groups(self, household):
        print('DEBUG------- ', household)
        """
        Get Household Groups
        """
        groups_url = self.household_url + '/' + household + '/groups'
        r = requests.get(groups_url, headers=self.headers)
        r_json = r.json()
        groups = r_json['groups']
        sonos_groups = {}
        for group in groups:
            sonos_groups.update({group['id']: group['name']})
        # return sonos_groups
        return groups

    # def get_group_status(self, household):
    #     """
    #     Get Household Groups
    #     """
    #     groups_url = self.household_url + '/' + household + '/groups'
    #     r = requests.get(groups_url, headers=self.headers)
    #     r_json = r.json()
    #     groups = r_json['groups']
    #     sonos_group_status = {}
    #     for group in groups:
    #         sonos_group_status.update({group['id']: group['playbackState']})
    #     return sonos_group_status

    def get_players(self, household):
        """
        Get Househole Players
        :param household:
        :return:
        """
        players_url = self.household_url + '/' + household + '/groups'
        r = requests.get(players_url, headers=self.headers)
        r_json = r.json()
        players = r_json['players']
        sonos_players = {}
        for player in players:
            sonos_players.update({player['id']: player['name']})
        # return sonos_players
        return players

    def get_favorites(self, household):
        """
        Get Favorites
        """
        favorites_url = self.household_url + '/' + household + '/favorites'
        r = requests.get(favorites_url, headers=self.headers)
        r_json = r.json()
        # print(r_json)
        favorites = r_json['items']
        sonos_favorites = {}
        for fav in favorites:
            sonos_favorites.update({fav['id']: fav['name']})
        return sonos_favorites

    def get_playlists(self, household):
        """
        Get Playlists
        """
        playlists_url = self.household_url + '/' + household + '/playlists'
        r = requests.get(playlists_url, headers=self.headers)
        r_json = r.json()
        # print(r_json)
        playlists = r_json['playlists']
        sonos_playlists = {}
        for pl in playlists:
            sonos_playlists.update({pl['id']: pl['name']})
        return sonos_playlists

    def get_group_volume(self, household, group):
        groupVolume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        r = requests.get(groupVolume_url, headers=self.headers)
        r_json = r.json()
        # List 0=volume, 1=muted, 2=fixed(true/false)
        volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
        return volume

    def set_group_volume(self, household, group, volume):
        payload = {"volume": volume}
        setGroupVolume_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume'
        r = requests.post(setGroupVolume_url, headers=self.headers, json=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_group_mute(self, household, group, mute):
        if mute:
            payload = "{\n\t\"muted\": true\n}"
        else:
            payload = "{\n\t\"muted\": false\n}"

        setMute_url = self.household_url + '/' + household + '/groups/' + group + '/groupVolume/mute'
        r = requests.post(setMute_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            print(r.content)
            return True
        else:
            return r.status_code

    def set_favorite(self, group, value):
        setFavorite_url = self.groups_url + group + '/favorites'
        payload = "{\n\t\"favoriteId\": \"" + value + "\",\n\t\"playOnCompletion\": true,\n\t\"playMode\": {\n\t\t\"shuffle\": true\n\t}\n}"
        r = requests.post(setFavorite_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_playlist(self, group, value, shuffle):
        setPlaylist_url = self.groups_url + group + '/playlists'
        if shuffle:
            payload = "{\n\t\"playlistId\": \"" + value + "\",\n\t\"playOnCompletion\": true,\n\t\"playMode\": {\n\t\t\"shuffle\": true\n\t}\n}"
        else:
            payload = "{\n\t\"playlistId\": \"" + value + "\",\n\t\"playOnCompletion\": true,\n\t\"playMode\": {\n\t\t\"shuffle\": false\n\t}\n}"
        r = requests.post(setPlaylist_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_pause(self, group):
        setPause_url = self.groups_url + group + '/playback/pause'
        r = requests.post(setPause_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_play(self, group):
        setPlay_url = self.groups_url + group + '/playback/play'
        r = requests.post(setPlay_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def skipToPreviousTrack(self, group):
        setPlay_url = self.groups_url + group + '/playback/skipToPreviousTrack'
        r = requests.post(setPlay_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def skipToNextTrack(self, group):
        setPlay_url = self.groups_url + group + '/playback/skipToNextTrack'
        r = requests.post(setPlay_url, headers=self.headers)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def get_player_volume(self, player):
        player_volume_url = self.players_url + player + '/playerVolume'
        r = requests.get(player_volume_url, headers=self.headers)
        r_json = r.json()
        # List 0=volume, 1=muted, 2=fixed(true/false)
        volume = [r_json['volume'], r_json['muted'], r_json['fixed']]
        if r.status_code == requests.codes.ok:
            return volume
        else:
            return r.status_code

    def set_player_volume(self, player, volume):
        payload = "{\r\n  \"volume\": " + volume + "\r\n}"
        player_volume_url = self.players_url + player + '/playerVolume'
        r = requests.post(player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_player_mute(self, player):
        payload = "{\r\n  \"muted\": true\r\n}"
        set_player_volume_url = self.players_url + player + '/playerVolume/mute'
        r = requests.post(set_player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code

    def set_player_unmute(self, player):
        payload = "{\r\n  \"muted\": false\r\n}"
        set_player_volume_url = self.players_url + player + '/playerVolume/mute'
        r = requests.post(set_player_volume_url, headers=self.headers, data=payload)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return r.status_code


