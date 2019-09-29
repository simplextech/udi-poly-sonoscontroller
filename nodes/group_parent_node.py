
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    CLOUD = True


class GroupParentNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(GroupParentNode, self).__init__(controller, primary, address, name)

    def start(self):
        # print('Starting Group: ' + self.name + ' ------------------')
        self.setDriver('ST', 1, force=True)

    def query(self):
        self.reportDrivers()

    # "Hints See: https://github.com/UniversalDevicesInc/hints"
    # hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]

    id = 'PARENT'

    commands = {
                    # 'DON': setOn, 'DOF': setOff
                    # 'SVOL': player_volume, 'GV01': player_playlist,
                    # 'GV02': player_favorite
                }
