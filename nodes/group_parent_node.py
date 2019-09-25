
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True

# from ...sonos import SonosControl
# from .. import sonos
from sonos import SonosControl as SonosControl


class GroupParentNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(GroupParentNode, self).__init__(controller, primary, address, name)

    def start(self):
        # print('Starting Group: ' + self.name + ' ------------------')
        self.setDriver('ST', 1)

    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [
                {'driver': 'ST', 'value': 1, 'uom': 2},
                # {'driver': 'SVOL', 'value': 0, 'uom': 51},
                # {'driver': 'GV01', 'value': 0, 'uom': 25},
                # {'driver': 'GV02', 'value': 0, 'uom': 25}
            ]

    id = 'PARENT'

    commands = {
                    # 'DON': setOn, 'DOF': setOff
                    # 'SVOL': player_volume, 'GV01': player_playlist,
                    # 'GV02': player_favorite
                }
