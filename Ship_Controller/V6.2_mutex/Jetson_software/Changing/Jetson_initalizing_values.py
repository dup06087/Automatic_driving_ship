def initialize_variables(self):
    self.end = 0
    self.flag_exit = False
    self.distance_to_target = 0

    self.isready = False
    self.isdriving = False
    self.isfirst = True
    # enddriving="0"
    self.driveindex = 0

    self.flag_avoidance = False
    self.message = None
