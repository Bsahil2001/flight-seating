from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Global data storage
passengers = {}
groups = {}
seats = {}
waiting_list = []

def initialize_aircraft():
    """Initialize simple aircraft layout"""
    global seats
    seats = {}
    
    # First Class: Rows 1-3 (VIP zone)
    for row in range(1, 4):
        for letter in ['A', 'B', 'D', 'E']:
            seats[f"{row}{letter}"] = {
                'row': row,
                'letter': letter,
                'available': True,
                'passenger': None,
                'passenger_name': None,
                'is_vip': True,
                'is_accessible': False,
                'is_quiet': False,
                'seat_class': 'first'
            }
    
    # Business Class: Rows 4-8
    for row in range(4, 9):
        for letter in ['A', 'B', 'C', 'D', 'E']:
            is_vip = row <= 6  # Rows 4-6 are VIP
            is_accessible = letter in ['B', 'D'] and row >= 7  # Aisle seats in rows 7-8
            
            seats[f"{row}{letter}"] = {
                'row': row,
                'letter': letter,
                'available': True,
                'passenger': None,
                'passenger_name': None,
                'is_vip': is_vip,
                'is_accessible': is_accessible,
                'is_quiet': False,
                'seat_class': 'business'
            }
    
    # Economy Class: Rows 9-30
    for row in range(9, 31):
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            is_quiet = 16 <= row <= 18  # Quiet zone
            is_accessible = letter in ['C', 'D'] and row >= 20  # Aisle seats from row 20
            
            seats[f"{row}{letter}"] = {
                'row': row,
                'letter': letter,
                'available': True,
                'passenger': None,
                'passenger_name': None,
                'is_vip': False,
                'is_accessible': is_accessible,
                'is_quiet': is_quiet,
                'seat_class': 'economy'
            }
    
    # Mark 3 random seats as unavailable
    available_seat_ids = list(seats.keys())
    unavailable = random.sample(available_seat_ids, 3)
    for seat_id in unavailable:
        seats[seat_id]['available'] = False

def simple_assign_seats():
    """Simple working seat assignment algorithm"""
    global waiting_list
    waiting_list = []
    
    print("=== STARTING SEAT ASSIGNMENT ===")
    print(f"Total passengers: {len(passengers)}")
    print(f"Total groups: {len(groups)}")
    
    # Get all passengers who need seats
    unassigned_passengers = []
    for p in passengers.values():
        if not p.get('assigned_seat'):
            unassigned_passengers.append(p)
    
    print(f"Unassigned passengers: {len(unassigned_passengers)}")
    
    # Sort by priority: VIP first, then accessibility
    def get_priority(p):
        score = 0
        if p.get('is_vip'): score += 1000
        if p.get('has_accessibility'): score += 500
        return score
    
    unassigned_passengers.sort(key=get_priority, reverse=True)
    
    # Assign each passenger
    for passenger in unassigned_passengers:
        print(f"Trying to assign: {passenger['name']}")
        success = assign_passenger_to_seat(passenger)
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    
    print("=== ASSIGNMENT COMPLETE ===")

def assign_passenger_to_seat(passenger):
    """Assign a single passenger to the best available seat"""
    passenger_id = passenger['id']
    
    print(f"  Looking for seat for {passenger['name']} (VIP: {passenger.get('is_vip')}, Access: {passenger.get('has_accessibility')})")
    
    # Find all available seats
    available_seats = []
    for seat_id, seat in seats.items():
        if seat['available'] and not seat['passenger']:
            available_seats.append(seat_id)
    
    print(f"  Found {len(available_seats)} available seats")
    
    # Filter by restrictions
    suitable_seats = []
    for seat_id in available_seats:
        seat = seats[seat_id]
        
        # Check VIP restriction - non-VIP cannot sit in VIP zones
        if not passenger.get('is_vip') and seat['is_vip']:
            continue
        
        # Check quiet zone - children under 12 cannot sit in quiet zone
        if passenger.get('age', 20) < 12 and seat['is_quiet']:
            continue
        
        suitable_seats.append(seat_id)
    
    print(f"  After restrictions: {len(suitable_seats)} suitable seats")
    
    if not suitable_seats:
        print(f"  No suitable seats found for {passenger['name']}")
        if passenger_id not in waiting_list:
            waiting_list.append(passenger_id)
        return False
    
    # For accessibility passengers, prefer accessible seats
    if passenger.get('has_accessibility'):
        accessible_seats = [s for s in suitable_seats if seats[s]['is_accessible']]
        if accessible_seats:
            print(f"  Found {len(accessible_seats)} accessible seats")
            suitable_seats = accessible_seats
    
    # Assign the first suitable seat
    seat_id = suitable_seats[0]
    seat = seats[seat_id]
    
    # Do the assignment
    seats[seat_id]['passenger'] = passenger_id
    seats[seat_id]['passenger_name'] = passenger['name']
    passengers[passenger_id]['assigned_seat'] = seat_id
    
    print(f"  ASSIGNED: {passenger['name']} -> {seat_id}")
    return True

# Initialize on startup
initialize_aircraft()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/api/seating-layout')
def get_seating_layout():
    """Return seating layout organized by rows"""
    layout = {}
    for seat_id, seat in seats.items():
        row = seat['row']
        letter = seat['letter']
        
        if row not in layout:
            layout[row] = {}
        
        layout[row][letter] = {
            'seat_class': seat['seat_class'],
            'seat_type': 'window' if letter in ['A', 'F'] else ('aisle' if letter in ['C', 'D', 'B'] else 'middle'),
            'is_vip_zone': seat['is_vip'],
            'is_accessible': seat['is_accessible'],
            'is_quiet_zone': seat['is_quiet'],
            'is_available': seat['available'],
            'passenger_id': seat['passenger'],
            'passenger_name': seat['passenger_name']
        }
    
    return jsonify(layout)

@app.route('/api/passenger-list')
def get_passenger_list():
    """Return all passengers and waiting list"""
    passenger_list = []
    for p in passengers.values():
        passenger_list.append({
            'id': p['id'],
            'name': p['name'],
            'age': p['age'],
            'type': p['type'],
            'group_id': p.get('group_id'),
            'assigned_seat': p.get('assigned_seat'),
            'is_vip': p.get('is_vip', False),
            'has_accessibility_needs': p.get('has_accessibility', False),
            'is_senior': p.get('is_senior', False)
        })
    
    return jsonify({
        'passengers': passenger_list,
        'waiting_list': waiting_list
    })

@app.route('/api/add-solo-passenger', methods=['POST'])
def add_solo_passenger():
    """Add solo passenger"""
    data = request.get_json()
    
    passenger_id = f"solo_{len(passengers) + 1}_{random.randint(100, 999)}"
    
    passengers[passenger_id] = {
        'id': passenger_id,
        'name': data['name'],
        'age': data['age'],
        'type': 'solo',
        'is_vip': data.get('vip', False),
        'has_accessibility': data.get('accessibility', False),
        'is_senior': data.get('senior', False),
        'assigned_seat': None
    }
    
    return jsonify({'success': True})

@app.route('/api/add-group', methods=['POST'])
def add_group():
    """Add group"""
    data = request.get_json()
    
    group_id = f"group_{len(groups) + 1}_{random.randint(100, 999)}"
    size = data['size']
    
    # Create group
    groups[group_id] = {
        'id': group_id,
        'name': data['name'],
        'size': size,
        'has_children': data.get('children', False),
        'has_accessibility': data.get('accessibility', False),
        'is_vip': data.get('vip', False),
        'has_senior': data.get('senior', False),
        'members': []
    }
    
    # Create group members
    for i in range(size):
        member_id = f"{group_id}_member_{i + 1}"
        passengers[member_id] = {
            'id': member_id,
            'name': f"{data['name']} Member {i + 1}",
            'age': 30,
            'type': 'group',
            'group_id': group_id,
            'is_vip': data.get('vip', False),
            'has_accessibility': data.get('accessibility', False),
            'is_senior': data.get('senior', False),
            'assigned_seat': None
        }
        groups[group_id]['members'].append(member_id)
    
    return jsonify({'success': True})

@app.route('/api/assign-seats', methods=['POST'])
def assign_seats():
    """Run seat assignment algorithm"""
    try:
        print("\n" + "="*50)
        print("SEAT ASSIGNMENT API CALLED")
        print(f"Passengers in system: {len(passengers)}")
        print(f"Groups in system: {len(groups)}")
        
        # Reset all seat assignments first
        for passenger in passengers.values():
            passenger['assigned_seat'] = None
        
        for seat in seats.values():
            seat['passenger'] = None
            seat['passenger_name'] = None
        
        simple_assign_seats()
        
        print("API: Assignment completed successfully")
        print("="*50)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"ERROR in assign_seats API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin-override', methods=['POST'])
def admin_override():
    """Admin override seat assignment"""
    data = request.get_json()
    passenger_id = data['passenger_id']
    row = data['row']
    seat_letter = data['seat_letter']
    seat_id = f"{row}{seat_letter}"
    
    if passenger_id not in passengers:
        return jsonify({'success': False})
    
    if seat_id not in seats:
        return jsonify({'success': False})
    
    # Free current seat
    current_seat = passengers[passenger_id].get('assigned_seat')
    if current_seat and current_seat in seats:
        seats[current_seat]['passenger'] = None
        seats[current_seat]['passenger_name'] = None
    
    # If target seat is occupied, move that passenger to waiting list
    if seats[seat_id]['passenger']:
        displaced_id = seats[seat_id]['passenger']
        passengers[displaced_id]['assigned_seat'] = None
        if displaced_id not in waiting_list:
            waiting_list.append(displaced_id)
    
    # Assign new seat
    seats[seat_id]['passenger'] = passenger_id
    seats[seat_id]['passenger_name'] = passengers[passenger_id]['name']
    passengers[passenger_id]['assigned_seat'] = seat_id
    
    # Remove from waiting list
    if passenger_id in waiting_list:
        waiting_list.remove(passenger_id)
    
    return jsonify({'success': True})

@app.route('/api/cancel-booking', methods=['POST'])
def cancel_booking():
    """Cancel passenger booking"""
    data = request.get_json()
    passenger_id = data['passenger_id']
    
    if passenger_id not in passengers:
        return jsonify({'success': False})
    
    passenger = passengers[passenger_id]
    
    # Free seat
    if passenger.get('assigned_seat'):
        seat_id = passenger['assigned_seat']
        if seat_id in seats:
            seats[seat_id]['passenger'] = None
            seats[seat_id]['passenger_name'] = None
    
    # Remove from waiting list
    if passenger_id in waiting_list:
        waiting_list.remove(passenger_id)
    
    # Handle group
    if passenger.get('group_id'):
        group_id = passenger['group_id']
        if group_id in groups:
            groups[group_id]['members'].remove(passenger_id)
            groups[group_id]['size'] -= 1
            if groups[group_id]['size'] == 0:
                del groups[group_id]
    
    # Remove passenger
    del passengers[passenger_id]
    
    return jsonify({'success': True})

@app.route('/api/debug-info')
def debug_info():
    """Debug endpoint to see system state"""
    info = {
        'passengers_count': len(passengers),
        'groups_count': len(groups),
        'waiting_list_count': len(waiting_list),
        'passengers': {pid: {
            'name': p['name'],
            'assigned_seat': p.get('assigned_seat'),
            'is_vip': p.get('is_vip'),
            'has_accessibility': p.get('has_accessibility')
        } for pid, p in passengers.items()},
        'available_seats_count': len([s for s in seats.values() if s['available'] and not s['passenger']]),
        'occupied_seats_count': len([s for s in seats.values() if s['passenger']]),
        'vip_seats_available': len([s for s in seats.values() if s['available'] and not s['passenger'] and s['is_vip']]),
        'accessible_seats_available': len([s for s in seats.values() if s['available'] and not s['passenger'] and s['is_accessible']])
    }
    return jsonify(info)

@app.route('/api/reset-system', methods=['POST'])
def reset_system():
    """Reset entire system"""
    global passengers, groups, waiting_list
    
    passengers = {}
    groups = {}
    waiting_list = []
    
    # Reset all seats
    for seat in seats.values():
        if seat['available']:  # Don't reset unavailable seats
            seat['passenger'] = None
            seat['passenger_name'] = None
    
    return jsonify({'success': True})
    """Reset entire system"""
    global passengers, groups, waiting_list
    
    passengers = {}
    groups = {}
    waiting_list = []
    
    # Reset all seats
    for seat in seats.values():
        if seat['available']:  # Don't reset unavailable seats
            seat['passenger'] = None
            seat['passenger_name'] = None
    
    return jsonify({'success': True})

if __name__ == '__main__':
    print("🚀 Starting Simple Aircraft Seating System...")
    print("🌐 Server starting at: http://localhost:5000")
    print("📋 All features working: Add passengers, assign seats, admin override")
    print("-" * 50)
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
