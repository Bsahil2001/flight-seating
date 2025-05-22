from flask import Flask, render_template, request, jsonify
import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum

app = Flask(__name__)

class SeatType(Enum):
    WINDOW = "window"
    MIDDLE = "middle"
    AISLE = "aisle"

class SeatClass(Enum):
    FIRST = "first"
    BUSINESS = "business"
    ECONOMY = "economy"

class PassengerType(Enum):
    SOLO = "solo"
    GROUP = "group"

@dataclass
class Seat:
    row: int
    seat_letter: str
    seat_class: SeatClass
    seat_type: SeatType
    is_vip_zone: bool = False
    is_accessible: bool = False
    is_quiet_zone: bool = False
    is_available: bool = True
    passenger_id: Optional[str] = None
    passenger_name: Optional[str] = None

@dataclass
class Passenger:
    id: str
    name: str
    age: int
    passenger_type: PassengerType
    has_accessibility_needs: bool = False
    is_vip: bool = False
    is_senior: bool = False
    group_id: Optional[str] = None
    assigned_seat: Optional[Tuple[int, str]] = None

@dataclass
class Group:
    id: str
    name: str
    size: int
    has_children: bool = False
    has_accessibility_needs: bool = False
    is_vip: bool = False
    has_senior_members: bool = False
    members: List[Passenger] = None

class AircraftSeatingSystem:
    def __init__(self):
        self.seats = {}
        self.passengers = {}
        self.groups = {}
        self.waiting_list = []
        self.initialize_aircraft()
        self.mark_unavailable_seats()

    def initialize_aircraft(self):
        """Initialize the aircraft seating layout"""
        # First Class: Rows 1-3, 2-2 configuration
        for row in range(1, 4):
            for seat_letter in ['A', 'B', 'D', 'E']:
                seat_type = SeatType.WINDOW if seat_letter in ['A', 'E'] else SeatType.AISLE
                self.seats[(row, seat_letter)] = Seat(
                    row=row,
                    seat_letter=seat_letter,
                    seat_class=SeatClass.FIRST,
                    seat_type=seat_type,
                    is_vip_zone=True
                )

        # Business Class: Rows 4-8, 2-3 configuration
        for row in range(4, 9):
            for seat_letter in ['A', 'B', 'C', 'D', 'E']:
                if seat_letter in ['A', 'E']:
                    seat_type = SeatType.WINDOW
                elif seat_letter in ['B', 'D']:
                    seat_type = SeatType.AISLE
                else:
                    seat_type = SeatType.MIDDLE
                
                self.seats[(row, seat_letter)] = Seat(
                    row=row,
                    seat_letter=seat_letter,
                    seat_class=SeatClass.BUSINESS,
                    seat_type=seat_type,
                    is_vip_zone=(row <= 6),  # Rows 4-6 are VIP in business
                    is_accessible=(seat_letter in ['B', 'D'] and row == 8)  # Aisle seats in row 8
                )

        # Economy Class: Rows 9-30, 3-3 configuration
        for row in range(9, 31):
            for seat_letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                if seat_letter in ['A', 'F']:
                    seat_type = SeatType.WINDOW
                elif seat_letter in ['C', 'D']:
                    seat_type = SeatType.AISLE
                else:
                    seat_type = SeatType.MIDDLE
                
                self.seats[(row, seat_letter)] = Seat(
                    row=row,
                    seat_letter=seat_letter,
                    seat_class=SeatClass.ECONOMY,
                    seat_type=seat_type,
                    is_quiet_zone=(16 <= row <= 18),  # Quiet zone rows 16-18
                    is_accessible=(seat_letter in ['C', 'D'] and row >= 25)  # Accessible seats near exits
                )

    def mark_unavailable_seats(self):
        """Randomly mark 5 seats as unavailable"""
        available_seats = [(row, letter) for (row, letter), seat in self.seats.items() if seat.is_available]
        unavailable_count = min(5, len(available_seats))
        unavailable_seats = random.sample(available_seats, unavailable_count)
        
        for row, letter in unavailable_seats:
            self.seats[(row, letter)].is_available = False

    def add_solo_passenger(self, name: str, age: int, has_accessibility_needs: bool = False, 
                          is_vip: bool = False, is_senior: bool = False) -> bool:
        """Add a solo passenger"""
        passenger_id = f"solo_{len(self.passengers) + 1}"
        passenger = Passenger(
            id=passenger_id,
            name=name,
            age=age,
            passenger_type=PassengerType.SOLO,
            has_accessibility_needs=has_accessibility_needs,
            is_vip=is_vip,
            is_senior=is_senior
        )
        self.passengers[passenger_id] = passenger
        return True

    def add_group(self, name: str, size: int, has_children: bool = False,
                  has_accessibility_needs: bool = False, is_vip: bool = False,
                  has_senior_members: bool = False) -> bool:
        """Add a group"""
        if not (2 <= size <= 7):
            return False
        
        group_id = f"group_{len(self.groups) + 1}"
        group = Group(
            id=group_id,
            name=name,
            size=size,
            has_children=has_children,
            has_accessibility_needs=has_accessibility_needs,
            is_vip=is_vip,
            has_senior_members=has_senior_members,
            members=[]
        )
        
        # Create group members
        for i in range(size):
            passenger_id = f"{group_id}_member_{i + 1}"
            passenger = Passenger(
                id=passenger_id,
                name=f"{name} Member {i + 1}",
                age=30,  # Default age
                passenger_type=PassengerType.GROUP,
                has_accessibility_needs=has_accessibility_needs,
                is_vip=is_vip,
                is_senior=has_senior_members,
                group_id=group_id
            )
            group.members.append(passenger)
            self.passengers[passenger_id] = passenger
        
        self.groups[group_id] = group
        return True

    def assign_seats(self) -> bool:
        """Main seating algorithm"""
        unassigned_passengers = [p for p in self.passengers.values() if p.assigned_seat is None]
        
        # Step 1: Process VIP passengers first
        vip_passengers = [p for p in unassigned_passengers if p.is_vip and p.passenger_type == PassengerType.SOLO]
        for passenger in vip_passengers:
            self._assign_vip_passenger(passenger)
        
        # Step 2: Handle passengers with accessibility needs
        accessibility_passengers = [p for p in unassigned_passengers 
                                  if p.has_accessibility_needs and p.assigned_seat is None]
        for passenger in accessibility_passengers:
            self._assign_accessibility_passenger(passenger)
        
        # Step 3: Assign VIP groups
        vip_groups = [g for g in self.groups.values() if g.is_vip]
        for group in vip_groups:
            self._assign_group(group)
        
        # Step 4: Assign regular groups
        regular_groups = [g for g in self.groups.values() if not g.is_vip]
        for group in regular_groups:
            self._assign_group(group)
        
        # Step 5: Place remaining solo travelers
        remaining_solo = [p for p in unassigned_passengers 
                         if p.passenger_type == PassengerType.SOLO and p.assigned_seat is None]
        for passenger in remaining_solo:
            self._assign_solo_passenger(passenger)
        
        return True

    def _assign_vip_passenger(self, passenger: Passenger) -> bool:
        """Assign VIP passenger to VIP zone"""
        vip_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                     if seat.is_vip_zone and seat.is_available and seat.passenger_id is None]
        
        # Prefer window and aisle seats
        preferred_seats = [(row, letter) for row, letter in vip_seats
                          if self.seats[(row, letter)].seat_type in [SeatType.WINDOW, SeatType.AISLE]]
        
        target_seats = preferred_seats if preferred_seats else vip_seats
        
        if target_seats:
            row, letter = target_seats[0]
            return self._assign_seat_to_passenger(passenger, row, letter)
        
        return False

    def _assign_accessibility_passenger(self, passenger: Passenger) -> bool:
        """Assign passenger with accessibility needs"""
        accessible_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                           if seat.is_accessible and seat.is_available and seat.passenger_id is None]
        
        # CRITICAL: Exclude VIP zones for non-VIP passengers even for accessibility
        if not passenger.is_vip:
            accessible_seats = [(row, letter) for row, letter in accessible_seats
                               if not self.seats[(row, letter)].is_vip_zone]
        
        if accessible_seats:
            row, letter = accessible_seats[0]
            return self._assign_seat_to_passenger(passenger, row, letter)
        
        # Fallback to aisle seats
        aisle_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                      if seat.seat_type == SeatType.AISLE and seat.is_available and seat.passenger_id is None]
        
        # CRITICAL: Exclude VIP zones for non-VIP passengers in fallback too
        if not passenger.is_vip:
            aisle_seats = [(row, letter) for row, letter in aisle_seats
                          if not self.seats[(row, letter)].is_vip_zone]
        
        if aisle_seats:
            row, letter = aisle_seats[0]
            return self._assign_seat_to_passenger(passenger, row, letter)
        
        return False

    def _assign_group(self, group: Group) -> bool:
        """Assign seats to a group"""
        available_rows = self._find_available_rows_for_group(group)
        
        if not available_rows:
            # Add to waiting list
            self.waiting_list.extend([p.id for p in group.members if p.assigned_seat is None])
            return False
        
        # Find best row that can accommodate the group
        for row_num, available_seats in available_rows:
            if len(available_seats) >= group.size:
                # CRITICAL: Check VIP zone restriction for non-VIP groups
                if not group.is_vip and any(self.seats[(row_num, letter)].is_vip_zone 
                                          for row_num, letter in available_seats[:group.size]):
                    continue
                
                # Check quiet zone restriction
                if group.has_children and any(self.seats[(row_num, letter)].is_quiet_zone 
                                            for row_num, letter in available_seats[:group.size]):
                    continue
                
                # Assign seats to group members
                seats_to_assign = available_seats[:group.size]
                for i, member in enumerate(group.members):
                    if member.assigned_seat is None:
                        row, letter = seats_to_assign[i]
                        self._assign_seat_to_passenger(member, row, letter)
                
                return True
        
        # If can't fit in one row, try to split across adjacent rows
        return self._assign_split_group(group)

    def _find_available_rows_for_group(self, group: Group) -> List[Tuple[int, List[Tuple[int, str]]]]:
        """Find rows with enough consecutive seats for a group"""
        available_rows = []
        
        for row_num in range(1, 31):
            row_seats = [(row_num, letter) for letter in ['A', 'B', 'C', 'D', 'E', 'F']
                        if (row_num, letter) in self.seats]
            
            available_in_row = [(row_num, letter) for row_num, letter in row_seats
                               if self.seats[(row_num, letter)].is_available and 
                               self.seats[(row_num, letter)].passenger_id is None]
            
            if len(available_in_row) >= 2:  # At least 2 seats available
                available_rows.append((row_num, available_in_row))
        
        return available_rows

    def _assign_split_group(self, group: Group) -> bool:
        """Split group across adjacent rows if necessary"""
        # This is a simplified implementation
        unassigned_members = [m for m in group.members if m.assigned_seat is None]
        
        for member in unassigned_members:
            if not self._assign_solo_passenger(member):
                self.waiting_list.append(member.id)
        
        return True

    def _assign_solo_passenger(self, passenger: Passenger) -> bool:
        """Assign seat to solo passenger"""
        # Prefer window and aisle seats, but EXCLUDE VIP zones for non-VIP passengers
        preferred_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                          if seat.is_available and seat.passenger_id is None and
                          seat.seat_type in [SeatType.WINDOW, SeatType.AISLE]]
        
        # CRITICAL: Exclude VIP zones for non-VIP passengers
        if not passenger.is_vip:
            preferred_seats = [(row, letter) for row, letter in preferred_seats
                              if not self.seats[(row, letter)].is_vip_zone]
        
        # Avoid quiet zone for children and seniors have flexible seating
        if passenger.age < 12:  # Child
            preferred_seats = [(row, letter) for row, letter in preferred_seats
                              if not self.seats[(row, letter)].is_quiet_zone]
        
        # Check if seat would split a potential group (avoid middle seats between occupied seats)
        suitable_seats = []
        for row, letter in preferred_seats:
            if not self._would_split_group(row, letter):
                suitable_seats.append((row, letter))
        
        target_seats = suitable_seats if suitable_seats else preferred_seats
        
        if target_seats:
            row, letter = target_seats[0]
            return self._assign_seat_to_passenger(passenger, row, letter)
        
        # Fallback to any available seat (but still exclude VIP zones for non-VIP)
        any_available = [(row, letter) for (row, letter), seat in self.seats.items()
                        if seat.is_available and seat.passenger_id is None]
        
        # CRITICAL: Still exclude VIP zones in fallback for non-VIP passengers
        if not passenger.is_vip:
            any_available = [(row, letter) for row, letter in any_available
                            if not self.seats[(row, letter)].is_vip_zone]
        
        if any_available:
            row, letter = any_available[0]
            return self._assign_seat_to_passenger(passenger, row, letter)
        
        self.waiting_list.append(passenger.id)
        return False

    def _would_split_group(self, row: int, seat_letter: str) -> bool:
        """Check if assigning this seat would split a potential group"""
        # Get adjacent seats in the same row
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
        if seat_letter not in seat_letters:
            return False
        
        seat_index = seat_letters.index(seat_letter)
        
        # Check if there are occupied seats on both sides
        left_occupied = False
        right_occupied = False
        
        if seat_index > 0:
            left_seat = (row, seat_letters[seat_index - 1])
            if left_seat in self.seats and self.seats[left_seat].passenger_id is not None:
                left_occupied = True
        
        if seat_index < len(seat_letters) - 1:
            right_seat = (row, seat_letters[seat_index + 1])
            if right_seat in self.seats and self.seats[right_seat].passenger_id is not None:
                right_occupied = True
        
        return left_occupied and right_occupied

    def _assign_seat_to_passenger(self, passenger: Passenger, row: int, seat_letter: str) -> bool:
        """Assign a specific seat to a passenger"""
        if (row, seat_letter) not in self.seats:
            return False
        
        seat = self.seats[(row, seat_letter)]
        if not seat.is_available or seat.passenger_id is not None:
            return False
        
        seat.passenger_id = passenger.id
        seat.passenger_name = passenger.name
        passenger.assigned_seat = (row, seat_letter)
        return True

    def admin_override(self, passenger_id: str, row: int, seat_letter: str) -> bool:
        """Admin override to manually assign seat"""
        if passenger_id not in self.passengers:
            return False
        
        if (row, seat_letter) not in self.seats:
            return False
        
        passenger = self.passengers[passenger_id]
        target_seat = self.seats[(row, seat_letter)]
        
        # Remove passenger from current seat if assigned
        if passenger.assigned_seat:
            old_row, old_letter = passenger.assigned_seat
            self.seats[(old_row, old_letter)].passenger_id = None
            self.seats[(old_row, old_letter)].passenger_name = None
        
        # If target seat is occupied, move that passenger to waiting list
        if target_seat.passenger_id:
            displaced_passenger = self.passengers[target_seat.passenger_id]
            displaced_passenger.assigned_seat = None
            if displaced_passenger.id not in self.waiting_list:
                self.waiting_list.append(displaced_passenger.id)
        
        # Assign new seat
        target_seat.passenger_id = passenger_id
        target_seat.passenger_name = passenger.name
        passenger.assigned_seat = (row, seat_letter)
        
        # Remove from waiting list if present
        if passenger_id in self.waiting_list:
            self.waiting_list.remove(passenger_id)
        
        return True

    def cancel_booking(self, passenger_id: str) -> bool:
        """Cancel a passenger's booking"""
        if passenger_id not in self.passengers:
            return False
        
        passenger = self.passengers[passenger_id]
        
        # Free up the seat
        if passenger.assigned_seat:
            row, letter = passenger.assigned_seat
            self.seats[(row, letter)].passenger_id = None
            self.seats[(row, letter)].passenger_name = None
            passenger.assigned_seat = None
        
        # Remove from waiting list if present
        if passenger_id in self.waiting_list:
            self.waiting_list.remove(passenger_id)
        
        # If part of a group, handle group cancellation
        if passenger.group_id:
            group = self.groups[passenger.group_id]
            group.members = [m for m in group.members if m.id != passenger_id]
            if not group.members:
                del self.groups[passenger.group_id]
        
        # Remove passenger
        del self.passengers[passenger_id]
        
        # Try to assign someone from waiting list to the freed seat
        self._process_waiting_list()
        
        return True

    def _process_waiting_list(self):
        """Try to assign seats to passengers on waiting list"""
        waiting_passengers = [self.passengers[pid] for pid in self.waiting_list 
                             if pid in self.passengers]
        
        for passenger in waiting_passengers:
            if self._assign_solo_passenger(passenger):
                self.waiting_list.remove(passenger.id)

    def reset_system(self):
        """Reset the entire system"""
        self.passengers = {}
        self.groups = {}
        self.waiting_list = []
        
        # Reset all seats
        for seat in self.seats.values():
            seat.passenger_id = None
            seat.passenger_name = None
        
        # Re-mark unavailable seats
        self.mark_unavailable_seats()

    def get_seating_layout(self):
        """Get the current seating layout for display"""
        layout = {}
        for (row, letter), seat in self.seats.items():
            if row not in layout:
                layout[row] = {}
            layout[row][letter] = {
                'seat_class': seat.seat_class.value,
                'seat_type': seat.seat_type.value,
                'is_vip_zone': seat.is_vip_zone,
                'is_accessible': seat.is_accessible,
                'is_quiet_zone': seat.is_quiet_zone,
                'is_available': seat.is_available,
                'passenger_id': seat.passenger_id,
                'passenger_name': seat.passenger_name
            }
        return layout

    def get_passenger_list(self):
        """Get list of all passengers with their details"""
        passenger_list = []
        for passenger in self.passengers.values():
            passenger_info = {
                'id': passenger.id,
                'name': passenger.name,
                'age': passenger.age,
                'type': passenger.passenger_type.value,
                'group_id': passenger.group_id,
                'assigned_seat': passenger.assigned_seat,
                'is_vip': passenger.is_vip,
                'has_accessibility_needs': passenger.has_accessibility_needs,
                'is_senior': passenger.is_senior
            }
            passenger_list.append(passenger_info)
        return passenger_list

# Global system instance
seating_system = AircraftSeatingSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/seating-layout')
def get_seating_layout():
    try:
        layout = seating_system.get_seating_layout()
        return jsonify(layout)
    except Exception as e:
        print(f"Error in get_seating_layout: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/passenger-list')
def get_passenger_list():
    try:
        return jsonify({
            'passengers': seating_system.get_passenger_list(),
            'waiting_list': seating_system.waiting_list
        })
    except Exception as e:
        print(f"Error in get_passenger_list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-solo-passenger', methods=['POST'])
def add_solo_passenger():
    data = request.json
    success = seating_system.add_solo_passenger(
        name=data['name'],
        age=data['age'],
        has_accessibility_needs=data.get('accessibility', False),
        is_vip=data.get('vip', False),
        is_senior=data.get('senior', False)
    )
    return jsonify({'success': success})

@app.route('/api/add-group', methods=['POST'])
def add_group():
    data = request.json
    success = seating_system.add_group(
        name=data['name'],
        size=data['size'],
        has_children=data.get('children', False),
        has_accessibility_needs=data.get('accessibility', False),
        is_vip=data.get('vip', False),
        has_senior_members=data.get('senior', False)
    )
    return jsonify({'success': success})

@app.route('/api/assign-seats', methods=['POST'])
def assign_seats():
    success = seating_system.assign_seats()
    return jsonify({'success': success})

@app.route('/api/admin-override', methods=['POST'])
def admin_override():
    data = request.json
    success = seating_system.admin_override(
        passenger_id=data['passenger_id'],
        row=data['row'],
        seat_letter=data['seat_letter']
    )
    return jsonify({'success': success})

@app.route('/api/cancel-booking', methods=['POST'])
def cancel_booking():
    data = request.json
    success = seating_system.cancel_booking(data['passenger_id'])
    return jsonify({'success': success})

@app.route('/api/reset-system', methods=['POST'])
def reset_system():
    seating_system.reset_system()
    return jsonify({'success': True})

if __name__ == '__main__':
    print("🚀 Starting Aircraft Seating Optimization System...")
    print("📁 Make sure your folder structure is:")
    print("   aircraft-seating-system/")
    print("   ├── app.py")
    print("   ├── requirements.txt")
    print("   └── templates/")
    print("       └── index.html")
    print("\n🌐 Server will be available at: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try changing the port by modifying the last line to:")
        print("   app.run(debug=True, host='0.0.0.0', port=5001)")