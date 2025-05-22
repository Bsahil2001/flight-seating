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
    
    all_passengers = list(passengers.values())
    
    # Sort passengers by priority
    def get_priority(p):
        score = 0
        if p.get('is_vip'): score += 1000
        if p.get('has_accessibility'): score += 500
        return score
    
    all_passengers.sort(key=get_priority, reverse=True)
    
    # First assign groups
    for group_id, group in groups.items():
        assign_group(group)
    
    # Then assign solo passengers
    solo_passengers = [p for p in all_passengers if not p.get('group_id')]
    for passenger in solo_passengers:
        if not passenger.get('assigned_seat'):
            assign_solo_passenger(passenger)

def assign_group(group):
    """Assign a group to seats"""
    unassigned_members = [p for p in group['members'] if not passengers[p].get('assigned_seat')]
    
    if not unassigned_members:
        return
    
    group_size = len(unassigned_members)
    
    # Find a row with enough seats
    for row in range(1, 31):
        available_in_row = []
        for seat_id, seat in seats.items():
            if seat['row'] == row and seat['available'] and not seat['passenger']:
                # Check restrictions
                if not group.get('is_vip') and seat['is_vip']:
                    continue
                if group.get('has_children') and seat['is_quiet']:
                    continue
                available_in_row.append(seat_id)
        
        if len(available_in_row) >= group_size:
            # Assign seats
            for i, member_id in enumerate(unassigned_members):
                if i < len(available_in_row):
                    seat_id = available_in_row[i]
                    assign_seat(member_id, seat_id)
            return
    
    # If couldn't assign together, assign individually
    for member_id in unassigned_members:
        assign_solo_passenger(passengers[member_id])

def assign_solo_passenger(passenger):
    """Assign solo passenger to best available seat"""
    passenger_id = passenger['id']
    
    # Find suitable seats
    suitable_seats = []
    
    for seat_id, seat in seats.items():
        if not seat['available'] or seat['passenger']:
            continue
        
        # Check VIP restriction
        if not passenger.get('is_vip') and seat['is_vip']:
            continue
        
        # Check accessibility
        if passenger.get('has_accessibility') and not seat['is_accessible']:
            # For accessibility, prefer accessible seats but allow others
            pass
        
        # Check quiet zone for children
        if passenger.get('age', 20) < 12 and seat['is_quiet']:
            continue
        
        suitable_seats.append(seat_id)
    
    if suitable_seats:
        # Prefer accessible seats for accessibility passengers
        if passenger.get('has_accessibility'):
            accessible_seats = [s for s in suitable_seats if seats[s]['is_accessible']]
            if accessible_seats:
                suitable_seats = accessible_seats
        
        # Assign first suitable seat
        seat_id = suitable_seats[0]
        assign_seat(passenger_id, seat_id)
    else:
        # Add to waiting list
        if passenger_id not in waiting_list:
            waiting_list.append(passenger_id)

def assign_seat(passenger_id, seat_id):
    """Assign specific seat to passenger"""
    if seat_id in seats and seats[seat_id]['available'] and not seats[seat_id]['passenger']:
        seats[seat_id]['passenger'] = passenger_id
        seats[seat_id]['passenger_name'] = passengers[passenger_id]['name']
        passengers[passenger_id]['assigned_seat'] = seat_id
        return True
    return False

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
        simple_assign_seats()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error: {e}")
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

if __name__ == '__main__':
    print("🚀 Starting Simple Aircraft Seating System...")
    print("🌐 Server starting at: http://localhost:5000")
    print("📋 All features working: Add passengers, assign seats, admin override")
    print("-" * 50)
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
