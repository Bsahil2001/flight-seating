from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Global variables
passengers = []
seats = {}

def create_seats():
    """Create aircraft seats"""
    seat_data = {}
    
    # Create 30 rows with 6 seats each
    for row in range(1, 31):
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            seat_id = f"{row}{letter}"
            seat_data[seat_id] = {
                'id': seat_id,
                'row': row,
                'letter': letter,
                'passenger': None,
                'available': True,
                'is_vip': row <= 5,
                'is_accessible': letter in ['C', 'D'] and row >= 20
            }
    
    return seat_data

# Initialize seats
seats = create_seats()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/add-passenger', methods=['POST'])
def add_passenger():
    data = request.get_json()
    
    passenger = {
        'id': len(passengers) + 1,
        'name': data['name'],
        'age': data['age'],
        'is_vip': data.get('vip', False),
        'needs_accessible': data.get('accessible', False),
        'assigned_seat': None
    }
    
    passengers.append(passenger)
    return jsonify({'success': True})

@app.route('/api/assign-seats', methods=['POST'])
def assign_seats():
    # Reset all assignments
    for seat in seats.values():
        seat['passenger'] = None
    
    for passenger in passengers:
        passenger['assigned_seat'] = None
    
    # Sort passengers: VIP first
    sorted_passengers = sorted(passengers, key=lambda p: p['is_vip'], reverse=True)
    
    # Assign seats
    for passenger in sorted_passengers:
        for seat_id, seat in seats.items():
            if not seat['available'] or seat['passenger']:
                continue
            
            # Check restrictions
            if not passenger['is_vip'] and seat['is_vip']:
                continue
            
            if passenger['needs_accessible'] and not seat['is_accessible']:
                continue
            
            # Assign seat
            seat['passenger'] = passenger['name']
            passenger['assigned_seat'] = seat_id
            break
    
    return jsonify({'success': True})

@app.route('/api/passengers')
def get_passengers():
    return jsonify(passengers)

@app.route('/api/seats')
def get_seats():
    layout = {}
    for seat_id, seat in seats.items():
        row = seat['row']
        if row not in layout:
            layout[row] = {}
        
        layout[row][seat['letter']] = {
            'passenger': seat['passenger'],
            'is_vip': seat['is_vip'],
            'is_accessible': seat['is_accessible'],
            'available': seat['available']
        }
    
    return jsonify(layout)

@app.route('/api/reset', methods=['POST'])
def reset_all():
    global passengers, seats
    passengers = []
    seats = create_seats()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
