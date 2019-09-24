#!/usr/bin/env python
"""
This is a NodeServer template for Polyglot v2 written in Python2/3
by Einstein.42 (James Milne) milne.james@gmail.com
"""
import fileinput
import re

import requests

# from sonos.sonos_control import SonosControl
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
import sys
import time
"""
Import the polyglot interface module. This is in pypy so you can just install it
normally. Replace pip with pip3 if you are using python3.

Virtualenv:
pip install polyinterface

Not Virutalenv:
pip install polyinterface --user

*I recommend you ALWAYS develop your NodeServers in virtualenv to maintain
cleanliness, however that isn't required. I do not condone installing pip
modules globally. Use the --user flag, not sudo.
"""

LOGGER = polyinterface.LOGGER
"""
polyinterface has a LOGGER that is created by default and logs to:
logs/debug.log
You can use LOGGER.info, LOGGER.warning, LOGGER.debug, LOGGER.error levels as needed.
"""


class Controller(polyinterface.Controller):
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.

    Class Variables:
    self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
    self.name: String name of the node
    self.address: String Address of Node, must be less than 14 characters (ISY limitation)
    self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
    self.added: Boolean Confirmed added to ISY as primary node
    self.config: Dictionary, this node's Config

    Class Methods (not including the Node methods):
    start(): Once the NodeServer config is received from Polyglot this method is automatically called.
    addNode(polyinterface.Node, update = False): Adds Node to self.nodes and polyglot/ISY. This is called
        for you on the controller itself. Update = True overwrites the existing Node data.
    updateNode(polyinterface.Node): Overwrites the existing node data here and on Polyglot.
    delNode(address): Deletes a Node from the self.nodes/polyglot and ISY. Address is the Node's Address
    longPoll(): Runs every longPoll seconds (set initially in the server.json or default 10 seconds)
    shortPoll(): Runs every shortPoll seconds (set initially in the server.json or default 30 seconds)
    query(): Queries and reports ALL drivers for ALL nodes to the ISY.
    getDriver('ST'): gets the current value from Polyglot for driver 'ST' returns a STRING, cast as needed
    runForever(): Easy way to run forever without maxing your CPU or doing some silly 'time.sleep' nonsense
                  this joins the underlying queue query thread and just waits for it to terminate
                  which never happens.
    """
    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(Controller, self).__init__(polyglot)
        self.name = 'Sonos Controller'
        # self.poly.onConfig(self.process_config)
        self.auth_host = 'api.sonos.com'
        self.api_host = 'api.ws.sonos.com'
        self.client_key = '9b381a14-1ce0-4789-ab69-61aedfda21c6'
        self.client_secret = '6cd01138-4a40-45b2-808e-6281417b5bea'
        self.redirect_uri = 'https://webhook.site/a45c16b3-1db8-44de-bd05-985956bfa461'
        self.scope = 'playback-control-all'
        self.auth_url = 'https://' + self.auth_host + '/login/v3/oauth'
        self.token_url = 'https://' + self.auth_host + '/login/v3/oauth/access'
        self.household_url = 'https://' + self.api_host + '/control/api/v1/households'
        self.household = {}
        self.sonos = SonosControl()

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a discovery method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        LOGGER.info('Started Template NodeServer')
        self.removeNoticesAll()

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

                    volume = SonosControl.get_groupVolume(self.sonos, household, id)
                    # List 0=volume, 1=muted, 2=fixed(true/false)
                    self.nodes[address].setDriver('SVOL', volume[0])
                    self.nodes[address].setDriver('GV0', volume[1])

    def longPoll(self):
        """
        Optional.
        This runs every 30 seconds. You would probably update your nodes either here
        or shortPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def query(self):
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Example
        Do discovery here. Does not have to be called discovery. Called from example
        controller start method and from DISCOVER command recieved from ISY as an exmaple.
        """
        # self.addNode(TemplateNode(self, self.address, 'templateaddr', 'Template Node Name'))

        # sonos = SonosControl()
        self.household = SonosControl.get_households(self.sonos)
        if self.household is not None:

            for key in self.household:
                household = self.household[key]

                sonos_groups = SonosControl.get_groups(self.sonos, household)
                self.addNode(GroupParentNode(self, 'groups', 'groups', 'Sonos Groups'))

                print('Sonos Groups-----------------------------------------------')
                for group in sonos_groups:
                    # RINCON_7828CA96B78201400:2253119126
                    id = group['id']
                    name = group['name']
                    address = str(id.split(':')[1]).lower()
                    self.addNode(GroupNode(self, 'groups', address, name, sonos_groups, household))
                print('End---------------------------------------------------------')

                # sonos_players = SonosControl.get_players(sonos, household)
                # self.addNode(PlayerNode(self, 'players', 'players', 'Sonos Players'))

                # print('Sonos Players')
                # for player in sonos_players:
                #     # RINCON_48A6B8A2895201400
                #     _split = player.split('_')
                #     _cut = _split[1][0:-4]
                #     address = str(_cut).lower()
                #     name = sonos_players[player]
                #     self.addNode(PlayerNode(self, 'players', address, name))
                # print('End----------')

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
        """
        Example
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def check_params(self):
        """
        This is an example if using custom Params for user and password and an example with a Dictionary
        """
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

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.
    The id must match the nodeDef id="controller"
    In the nodedefs.xml
    """
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
        """
        Instantiates the Interface to Polyglot.
        The name doesn't really matter unless you are starting it from the
        command line then you need a line Template=N
        where N is the slot number.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
