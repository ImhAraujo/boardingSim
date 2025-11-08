from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class  DefaultPlane:
    """Defines a plane, narrow-body only for now"""
    dt: float = field(repr=False, default=0.1)
    lines: int = 30
    seats_per_row: int = 6
    initial_distance: float = 2.4
    seat_size: float = 0.8
    t = 0

    def __post_init__(self):
        names = ("side", "row", "position")
        s1 = [x for x in range(int(self.seats_per_row/2))]
        s2 = [x for x in range(self.seats_per_row - int(self.seats_per_row/2))]
        seat1 = [(0, row, pos) for pos in s1 for row in range(self.lines)]
        seat2 = [(1, row, pos) for pos in s2 for row in range(self.lines)]
        self.seats = tuple(seat1 + seat2)
        self.seat_status = np.zeros((2, self.lines, int(self.seats_per_row/2)))
        #self.seats = pd.MultiIndex.from_tuples(
        #    self.seats,
        #    names=names)
        #self.seat_status = pd.DataFrame(
        #        np.zeros(self.lines*self.seats_per_row, dtype=bool),
         #       index=self.seats)[0]

    def get_seat_shuffle(self, seat):
        side, row, pos = seat
        if pos == 0: return 1
        elif pos == 1:
            # Aisle seat occupied
            if self.seat_status[side, row, 0]: return 2
            else: return 1
        else: # pos == 2
            middle_seat = self.seat_status[side, row, 1]
            aisle_seat = self.seat_status[side, row, 0]
            if aisle_seat and middle_seat: return 4
            elif middle_seat: return 3
            elif aisle_seat: return 2
            else: return 1
    
    def get_seat_distance(self, seat):
        _, row, _ = seat
        return self.initial_distance + (row)*self.seat_size

    def set_passenger_order(self, passenger_list):
        # resets current condition
        self.ended = False
        self.t = 0
        self._waiting_list = list(passenger_list)
        self._embarking_list = []
        self._embarking_counter = len(passenger_list)
        self._embarked_list = []

    def _add_passenger_to_line(self):
        if len(self._waiting_list) > 0:
            current_passenger = self._waiting_list.pop(0)
            self._embarking_list.append(current_passenger)
            current_passenger.enter_plane()
            self.is_new_passenger = True
            current_passenger.enter_time = self.t

    def step(self):
        # advance time
        
        self.is_new_passenger = False
        self.n_seated_passenger = 0
        self.up_time_list = []
        if self._embarking_counter == 0:# check if everyone in place
            self.ended = True

        if len(self._embarking_list) == 0:
            # no one embarking -> add passenger
            self._add_passenger_to_line()
        elif self._embarking_list[-1].get_back_position() >= 0:
            # there is space for another passenger
            self._add_passenger_to_line()

        front_passenger = None
        for passenger in self._embarking_list.copy():
            if passenger._step(front_passenger=front_passenger):
                self._embarking_list.remove(passenger)
                self._embarked_list.append(passenger)
                self.seat_status[passenger.seat] = True
                self._embarking_counter -= 1
                self.n_seated_passenger += 1
                self.up_time_list.append(str(self.t - passenger.enter_time))
            front_passenger = passenger

        self.t += self.dt

@dataclass
class DefaultPassenger:
    """Object for a passenger propertys (SI units)"""
    plane: DefaultPlane = field(repr=False) 
    seat: tuple
    size: float = 0.4
    speed: float = 0.8
    luggage: int = None
    """
    position: float = None
    goal: float = None
    intention: float = None
    wait: float = None
    """
    def __post_init__(self):
        self.seat = tuple(self.seat)
        self.goal = self.plane.get_seat_distance(self.seat)
        self.row = self.seat[1]
    """
    def __repr__(self):
        if self.intention is None: # Waiting
            return f"(x: {self.position:.2f}, wait: {self.wait:.2f})"
        else:
            return f"(x: {self.position:.2f})"
    """

    def get_front_position(self):

        if self.position is None: return None
        return self.position + self.size/2

    def get_back_position(self):

        if self.position is None: return None
        return self.position - self.size/2

    def _seat_movement_time(self, n_times=1):
        return sum(np.random.triangular(1.8, 2.4, 3, n_times))

    def _luggage_delay(self, n_times=1):
        # weilbull distribution
        a = 1.7 # scale parameter
        b = 16.0 # form parameter
        return sum(b*(-np.log(np.random.rand(n_times)))**(1/a))
    
    def enter_plane(self):
        self.position = -self.size/2
        self.intention = self.position + self.speed*self.plane.dt

    def get_sit_time(self, shuffling_type):
        
        # time response
        time = np.random.triangular(6, 9, 20)

        # luggage delay
        if self.luggage is None:
            pass
        else:
            time += self._luggage_delay(n_times=self.luggage)

        # seat shuffling time
        if shuffling_type == 1:
            # No one in front
            time += self._seat_movement_time(n_times=1)

        elif shuffling_type == 2:
            # Blocked aisle
            time += self._seat_movement_time(n_times=4)

        elif shuffling_type == 3:
            # Blocked middle
            time += self._seat_movement_time(n_times=5)

        elif shuffling_type == 4:
            # Blocked both
            time += self._seat_movement_time(n_times=9)
        """
        print(f"luggage: {self.luggage}")
        print(f"s_type: {shuffling_type}")
        print(f"time: {time}")
        """
        return time

        
    def _step(self, front_passenger=None):
        # Advance the passenger
        t = self.plane.t
        dt = self.plane.dt

        def check_goal():
            if self.intention >= self.goal:
                # Arrives
                self.position = self.goal
                self.intention = None
                self.wait = (t 
                + self.get_sit_time(self.plane.get_seat_shuffle(self.seat)))
            else:
                self.position = self.intention
                self.intention = self.position + self.speed*dt

        # Passenger is not stowing/sitting
        if self.intention is not None:
            
            if front_passenger is None:
                check_goal()                
            else:
                front_limit = front_passenger.get_back_position() - self.size/2

                if front_limit >= self.goal:
                    # Goal closer than next passenger
                    check_goal()

                else:
                    # Next passenger closer
                    if self.intention >= front_limit:
                        # Blocked
                        self.position = front_limit
                    else:
                        self.position = self.intention
                    self.intention = self.position + self.speed*dt


        else:
            # Passenger is stowing/sitting

            if self.wait <= t:
                return True

        return False

def luggage_number():
    random_number = np.random.random()
    if random_number <= 0.6:
        luggage = 1
    elif random_number <= 0.9:
        luggage = 2
    else:
        luggage = 3
    return luggage

# Functions for creating boarding strategies
def random_order(plane):
    line = []
    rng = np.random.default_rng()
    return rng.permutation(plane.seats)

def group_order(plane, n_groups=3):
    rng = np.random.default_rng()
    line = rng.permutation(plane.seats)
    line = sorted(line, key=lambda x: int(x[1]*n_groups/plane.lines))
    line.reverse()
    return line

def WMA_order(plane):
    rng = np.random.default_rng()
    line = rng.permutation(plane.seats)
    line = sorted(line, key=lambda x: x[2])
    return line[::-1]

def reversePyramid_order(plane, n_groups=5):
    rng = np.random.default_rng()
    line = rng.permutation(plane.seats)
    n_line = plane.lines
    n_seats = plane.lines*round(plane.seats_per_row/2)
    ord_func = lambda x: int((x[1]+n_line*x[2])*n_groups/n_seats)
    line = sorted(line, key=ord_func)
    return line[::-1]

def Steffen_order(plane):
    rng = np.random.default_rng()
    line = rng.permutation(plane.seats)
    n_seats = round(plane.lines/2)
    
    def ord_func(seat):
        side, row, pos = seat
        d, m = divmod(row,2)
        return d + 2*n_seats*m + 4*n_seats*pos + n_seats*side
    
    line = sorted(line, key=ord_func)
    return line[::-1]

def organize_test(passenger_line, n_ok):
    rng = np.random.default_rng()
    ok_list = n_ok*[True] + (len(passenger_line) - n_ok)*[False]
    ok_list = rng.permutation(ok_list)
    final_line = [(*seat, ok) for seat, ok in zip(passenger_line, ok_list)]

    change = True
    while change:
        change = False
        for i, (_, row, _, ok) in enumerate(final_line[:-1]):
            if ok and final_line[i+1][1] > row:
                final_line[i], final_line[i+1] = final_line[i+1], final_line[i]
                change = True
                break
    return [seat[:3] for seat in final_line]

def make_line(line, plane):
    rng = np.random.default_rng()
    bags_list = 108*[1] + 54*[2] + 18*[3]
    return [DefaultPassenger(plane=plane, seat=seat, luggage=n) for seat, n in zip(line, rng.permutation(bags_list))]

def simulate(plane, line):
    plane.set_passenger_order(line)
    while True:
        plane.step()
        if plane.ended: break;

    return plane.t

teste = lambda x: int((x[1]+4*x[2])*5/12)

a = DefaultPlane(lines=4)
if __name__ == "__main__":
    a = DefaultPlane(lines=4)
