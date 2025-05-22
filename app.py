from flask import Flask, render_template, request, jsonify
import random
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum

app = Flask(__name__)

# Production configuration
app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'

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
    members: List[Passenger] = field(default_factory=list)

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
                    is_vip_zone=(row <= 6),
                    is_accessible=(seat_letter in ['B', 'D'] and row == 8)
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
                    is_quiet_zone=(16 <= row <= 18),
                    is_accessible=(seat_letter in ['C', 'D'] and row >= 25)
                )

    def mark_unavailable_seats(self):
        """Randomly mark 5 seats as unavailable"""
        available_seats = [(row, letter) for (row, letter), seat in self.seats.items() if seat.is_available]
        unavailable_count = min(5, len(available_seats))
        if unavailable_count > 0:
            unavailable_seats = random.sample(available_seats, unavailable_count)
            for row, letter in unavailable_seats:
                self.seats[(row, letter)].is_available = False

    def add_solo_passenger(self, name: str, age: int, has_accessibility_needs: bool = False, 
                          is_vip: bool = False, is_senior: bool = False) -> bool:
        """Add a solo passenger"""
        try:
            passenger_id = f"solo_{len(self.passengers) + 1}_{random.randint(1000, 9999)}"
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
        except Exception as e:
            print(f"Error adding solo passenger: {e}")
            return False

    def add_group(self, name: str, size: int, has_children: bool = False,
                  has_accessibility_needs: bool = False, is_vip: bool = False,
                  has_senior_members: bool = False) -> bool:
        """Add a group"""
        try:
            if not (2 <= size <= 7):
                return False
            
            group_id = f"group_{len(self.groups) + 1}_{random.randint(1000, 9999)}"
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
                    age=30,
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
        except Exception as e:
            print(f"Error adding group: {e}")
            return False

    def assign_seats(self) -> bool:
        """Main seating algorithm"""
        try:
            # Clear waiting list
            self.waiting_list = []
            
            # Step 1: Process VIP passengers first
            vip_passengers = [p for p in self.passengers.values() 
                            if p.is_vip and p.passenger_type == PassengerType.SOLO and p.assigned_seat is None]
            for passenger in vip_passengers:
                self._assign_vip_passenger(passenger)
            
            # Step 2: Handle passengers with accessibility needs
            accessibility_passengers = [p for p in self.passengers.values() 
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
            remaining_solo = [p for p in self.passengers.values() 
                            if p.passenger_type == PassengerType.SOLO and p.assigned_seat is None]
            for passenger in remaining_solo:
                self._assign_solo_passenger(passenger)
            
            return True
        except Exception as e:
            print(f"Error in assign_seats: {e}")
            return False

    def _assign_vip_passenger(self, passenger: Passenger) -> bool:
        """Assign VIP passenger to VIP zone"""
        try:
            vip_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                        if seat.is_vip_zone and seat.is_available and seat.passenger_id is None]
            
            preferred_seats = [(row, letter) for row, letter in vip_seats
                              if self.seats[(row, letter)].seat_type in [SeatType.WINDOW, SeatType.AISLE]]
            
            target_seats = preferred_seats if preferred_seats else vip_seats
            
            if target_seats:
                row, letter = target_seats[0]
                return self._assign_seat_to_passenger(passenger, row, letter)
            
            return False
        except Exception as e:
            print(f"Error assigning VIP passenger: {e}")
            return False

    def _assign_accessibility_passenger(self, passenger: Passenger) -> bool:
        """Assign passenger with accessibility needs"""
        try:
            accessible_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                               if seat.is_accessible and seat.is_available and seat.passenger_id is None]
            
            if not passenger.is_vip:
                accessible_seats = [(row, letter) for row, letter in accessible_seats
                                   if not self.seats[(row, letter)].is_vip_zone]
            
            if accessible_seats:
                row, letter = accessible_seats[0]
                return self._assign_seat_to_passenger(passenger, row, letter)
            
            # Fallback to aisle seats
            aisle_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                          if seat.seat_type == SeatType.AISLE and seat.is_available and seat.passenger_id is None]
            
            if not passenger.is_vip:
                aisle_seats = [(row, letter) for row, letter in aisle_seats
                              if not self.seats[(row, letter)].is_vip_zone]
            
            if aisle_seats:
                row, letter = aisle_seats[0]
                return self._assign_seat_to_passenger(passenger, row, letter)
            
            return False
        except Exception as e:
            print(f"Error assigning accessibility passenger: {e}")
            return False

    def _assign_group(self, group: Group) -> bool:
        """Assign seats to a group"""
        try:
            available_rows = self._find_available_rows_for_group(group)
            
            if not available_rows:
                for member in group.members:
                    if member.assigned_seat is None and member.id not in self.waiting_list:
                        self.waiting_list.append(member.id)
                return False
            
            for row_num, available_seats in available_rows:
                if len(available_seats) >= group.size:
                    # Check VIP zone restriction
                    if not group.is_vip and any(self.seats[(row_num, letter)].is_vip_zone 
                                              for row_num, letter in available_seats[:group.size]):
                        continue
                    
                    # Check quiet zone restriction
                    if group.has_children and any(self.seats[(row_num, letter)].is_quiet_zone 
                                                for row_num, letter in available_seats[:group.size]):
                        continue
                    
                    # Assign seats to group members
                    seats_to_assign = available_seats[:group.size]
                    success_count = 0
                    for i, member in enumerate(group.members):
                        if i < len(seats_to_assign) and member.assigned_seat is None:
                            row, letter = seats_to_assign[i]
                            if self._assign_seat_to_passenger(member, row, letter):
                                success_count += 1
                    
                    if success_count > 0:
                        return True
            
            # If can't fit in one row, split group
            return self._assign_split_group(group)
        except Exception as e:
            print(f"Error assigning group: {e}")
            return False

    def _find_available_rows_for_group(self, group: Group) -> List[Tuple[int, List[Tuple[int, str]]]]:
        """Find rows with enough consecutive seats for a group"""
        available_rows = []
        
        for row_num in range(1, 31):
            # Get all seats in this row that exist in our aircraft
            row_seats = [(row_num, letter) for letter in ['A', 'B', 'C', 'D', 'E', 'F']
                        if (row_num, letter) in self.seats]
            
            available_in_row = [(row_num, letter) for row_num, letter in row_seats
                               if self.seats[(row_num, letter)].is_available and 
                               self.seats[(row_num, letter)].passenger_id is None]
            
            if len(available_in_row) >= 2:
                available_rows.append((row_num, available_in_row))
        
        return available_rows

    def _assign_split_group(self, group: Group) -> bool:
        """Split group across adjacent rows if necessary"""
        try:
            unassigned_members = [m for m in group.members if m.assigned_seat is None]
            
            for member in unassigned_members:
                if not self._assign_solo_passenger(member):
                    if member.id not in self.waiting_list:
                        self.waiting_list.append(member.id)
            
            return True
        except Exception as e:
            print(f"Error splitting group: {e}")
            return False

    def _assign_solo_passenger(self, passenger: Passenger) -> bool:
        """Assign seat to solo passenger"""
        try:
            preferred_seats = [(row, letter) for (row, letter), seat in self.seats.items()
                              if seat.is_available and seat.passenger_id is None and
                              seat.seat_type in [SeatType.WINDOW, SeatType.AISLE]]
            
            if not passenger.is_vip:
                preferred_seats = [(row, letter) for row, letter in preferred_seats
                                  if not self.seats[(row, letter)].is_vip_zone]
            
            if passenger.age < 12:
                preferred_seats = [(row, letter) for row, letter in preferred_seats
                                  if not self.seats[(row, letter)].is_quiet_zone]
            
            if preferred_seats:
                row, letter = preferred_seats[0]
                return self._assign_seat_to_passenger(passenger, row, letter)
            
            # Fallback to any available seat
            any_available = [(row, letter) for (row, letter), seat in self.seats.items()
                            if seat.is_available and seat.passenger_id is None]
            
            if not passenger.is_vip:
                any_available = [(row, letter) for row, letter in any_available
                                if not self.seats[(row, letter)].is_vip_zone]
            
            if any_available:
                row, letter = any_available[0]
                return self._assign_seat_to_passenger(passenger, row, letter)
            
            if passenger.id not in self.waiting_list:
                self.waiting_list.append(passenger.id)
            return False
        except Exception as e:
            print(f"Error assigning solo passenger: {e}")
            return False

    def _assign_seat_to_passenger(self, passenger: Passenger, row: int, seat_letter: str) -> bool:
        """Assign a specific seat to a passenger"""
        try:
            if (row, seat_letter) not in self.seats:
                return False
            
            seat = self.seats[(row, seat_letter)]
            if not seat.is_available or seat.passenger_id is not None:
                return False
            
            seat.passenger_id = passenger.id
            seat.passenger_name = passenger.name
            passenger.assigned_seat = (row, seat_letter)
            return True
        except Exception as e:
            print(f"Error assigning seat: {e}")
            return False

    def admin_override(self, passenger_id: str, row: int, seat_letter: str) -> bool:
        """Admin override to manually assign seat"""
        try:
            if passenger_id not in self.passengers:
                return False
            
            if (row, seat_letter) not in self.seats:
                return False
            
            passenger = self.passengers[passenger_id]
            target_seat = self.seats[(row, seat_letter)]
            
            # Remove passenger from current seat if assigned
            if passenger.assigned_seat:
                old_row, old_letter = passenger.assigned_seat
                if (old_row, old_letter) in self.seats:
                    self.seats[(old_row, old_letter)].passenger_id = None
                    self.seats[(old_row, old_letter)].passenger_name = None
            
            # If target seat is occupied, move that passenger to waiting list
            if target_seat.passenger_id and target_seat.passenger_id != passenger_id:
                displaced_passenger = self.passengers.get(target_seat.passenger_id)
                if displaced_passenger:
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
        except Exception as e:
            print(f"Error in admin override: {e}")
            return False

    def cancel_booking(self, passenger_id: str) -> bool:
        """Cancel a passenger's booking"""
        try:
            if passenger_id not in self.passengers:
                return False
            
            passenger = self.passengers[passenger_id]
            
            # Free up the seat
            if passenger.assigned_seat:
                row, letter = passenger.assigned_seat
                if (row, letter) in self.seats:
                    self.seats[(row, letter)].passenger_id = None
                    self.seats[(row, letter)].passenger_name = None
            
            # Remove from waiting list if present
            if passenger_id in self.waiting_list:
                self.waiting_list.remove(passenger_id)
            
            # If part of a group, handle group cancellation
            if passenger.group_id and passenger.group_id in self.groups:
                group = self.groups[passenger.group_id]
                group.members = [m for m in group.members if m.id != passenger_id]
                group.size = len(group.members)
                if group.size == 0:
                    del self.groups[passenger.group_id]
            
            # Remove passenger
            del self.passengers[passenger_id]
            
            return True
        except Exception as e:
            print(f"Error canceling booking: {e}")
            return False

    def reset_system(self):
        """Reset the entire system"""
        try:
            self.passengers = {}
            self.groups = {}
            self.waiting_list = []
            
            # Reset all seats
            for seat in self.seats.values():
                if seat.is_available:  # Don't reset unavailable seats
                    seat.passenger_id = None
                    seat.passenger_name = None
            
            # Re-mark unavailable seats
            for seat in self.seats.values():
                seat.is_available = True
            self.mark_unavailable_seats()
        except Exception as e:
            print(f"Error resetting system: {e}")

    def get_seating_layout(self):
        """Get the current seating layout for display"""
        try:
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
        except Exception as e:
            print(f"Error getting seating layout: {e}")
            return {}

    def get_passenger_list(self):
        """Get list of all passengers with their details"""
        try:
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
        except Exception as e:
            print(f"Error getting passenger list: {e}")
            return []

# Global system instance
seating_system = AircraftSeatingSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Render deployment"""
    return {
        'status': 'healthy', 
        'service': 'Aircraft Seating Optimization System',
        'version': '1.0.0'
    }, 200

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
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success = seating_system.add_solo_passenger(
            name=data.get('name', ''),
            age=int(data.get('age', 0)),
            has_accessibility_needs=data.get('accessibility', False),
            is_vip=data.get('vip', False),
            is_senior=data.get('senior', False)
        )
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error adding solo passenger: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-group', methods=['POST'])
def add_group():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success = seating_system.add_group(
            name=data.get('name', ''),
            size=int(data.get('size', 0)),
            has_children=data.get('children', False),
            has_accessibility_needs=data.get('accessibility', False),
            is_vip=data.get('vip', False),
            has_senior_members=data.get('senior', False)
        )
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error adding group: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assign-seats', methods=['POST'])
def assign_seats():
    try:
        success = seating_system.assign_seats()
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error assigning seats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin-override', methods=['POST'])
def admin_override():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success = seating_system.admin_override(
            passenger_id=data.get('passenger_id', ''),
            row=int(data.get('row', 0)),
            seat_letter=data.get('seat_letter', '')
        )
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error in admin override: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cancel-booking', methods=['POST'])
def cancel_booking():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success = seating_system.cancel_booking(data.get('passenger_id', ''))
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error canceling booking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset-system', methods=['POST'])
def reset_system():
    try:
        seating_system.reset_system()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error resetting system: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        # Production configuration for Render
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try changing the port by modifying the PORT environment variable")
