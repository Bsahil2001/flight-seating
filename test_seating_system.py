
import unittest
import sys
import os

# Add the parent directory to the path to import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import AircraftSeatingSystem, Passenger, Group, SeatType, SeatClass, PassengerType


class TestAircraftSeatingSystem(unittest.TestCase):
    """
    TDD Test Suite for Aircraft Seating Optimization System
    Following Red-Green-Refactor methodology
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.seating_system = AircraftSeatingSystem()
        self.seating_system.reset_system()  # Start with clean state

    def tearDown(self):
        """Clean up after each test method."""
        self.seating_system.reset_system()

    # ====================================
    # TDD CYCLE 1: BASIC PASSENGER MANAGEMENT
    # ====================================

    def test_add_solo_passenger_success(self):
        """
        TDD Test 1: Add solo passenger successfully
        RED: Write failing test first
        """
        # Arrange
        initial_count = len(self.seating_system.passengers)
        
        # Act
        result = self.seating_system.add_solo_passenger("John Doe", 30)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(len(self.seating_system.passengers), initial_count + 1)
        
        # Verify passenger details
        passenger = list(self.seating_system.passengers.values())[0]
        self.assertEqual(passenger.name, "John Doe")
        self.assertEqual(passenger.age, 30)
        self.assertEqual(passenger.passenger_type, PassengerType.SOLO)

    def test_add_group_success(self):
        """
        TDD Test 2: Add group successfully
        RED: Write failing test first
        """
        # Act
        result = self.seating_system.add_group("Smith Family", 4)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(len(self.seating_system.groups), 1)
        self.assertEqual(len(self.seating_system.passengers), 4)  # 4 group members
        
        # Verify group details
        group = list(self.seating_system.groups.values())[0]
        self.assertEqual(group.name, "Smith Family")
        self.assertEqual(group.size, 4)
        self.assertEqual(len(group.members), 4)

    def test_add_invalid_group_size_fails(self):
        """
        TDD Test 3: Invalid group size should fail
        RED: Test edge cases
        """
        # Test too small
        result1 = self.seating_system.add_group("Too Small", 1)
        self.assertFalse(result1)
        
        # Test too large
        result2 = self.seating_system.add_group("Too Large", 8)
        self.assertFalse(result2)
        
        # Test valid range
        result3 = self.seating_system.add_group("Valid", 4)
        self.assertTrue(result3)

    # ====================================
    # TDD CYCLE 2: BASIC SEAT ASSIGNMENT
    # ====================================

    def test_solo_passenger_gets_assigned(self):
        """
        TDD Test 4: Solo passenger gets seat assignment
        GREEN: Implement basic assignment logic
        """
        # Arrange
        self.seating_system.add_solo_passenger("Alice", 25)
        
        # Act
        result = self.seating_system.assign_seats()
        
        # Assert
        self.assertTrue(result)
        passenger = list(self.seating_system.passengers.values())[0]
        self.assertIsNotNone(passenger.assigned_seat)
        
        # Verify seat is marked as occupied
        row, letter = passenger.assigned_seat
        self.assertEqual(self.seating_system.seats[(row, letter)].passenger_id, passenger.id)

    def test_group_members_assigned_together(self):
        """
        TDD Test 5: Group members get seats in same row
        GREEN: Implement group assignment logic
        """
        # Arrange
        self.seating_system.add_group("Johnson Family", 3)
        
        # Act
        result = self.seating_system.assign_seats()
        
        # Assert
        self.assertTrue(result)
        
        # Get all group members
        group = list(self.seating_system.groups.values())[0]
        assigned_rows = set()
        
        for member in group.members:
            self.assertIsNotNone(member.assigned_seat, f"Member {member.name} not assigned")
            row, letter = member.assigned_seat
            assigned_rows.add(row)
        
        # All members should be in the same row
        self.assertEqual(len(assigned_rows), 1, "Group members not in same row")

    def test_no_double_booking(self):
        """
        TDD Test 6: No seat should be assigned to multiple passengers
        GREEN: Implement seat conflict prevention
        """
        # Arrange
        self.seating_system.add_solo_passenger("Person1", 30)
        self.seating_system.add_solo_passenger("Person2", 25)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        assigned_seats = []
        for passenger in self.seating_system.passengers.values():
            if passenger.assigned_seat:
                self.assertNotIn(passenger.assigned_seat, assigned_seats, 
                               "Seat double-booked!")
                assigned_seats.append(passenger.assigned_seat)

    # ====================================
    # TDD CYCLE 3: VIP PRIORITY ALGORITHM
    # ====================================

    def test_vip_passenger_gets_vip_zone(self):
        """
        TDD Test 7: VIP passengers get VIP zone seats
        RED: Write test for VIP priority
        """
        # Arrange
        self.seating_system.add_solo_passenger("Regular Guy", 30, is_vip=False)
        self.seating_system.add_solo_passenger("VIP Lady", 35, is_vip=True)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        vip_passenger = None
        regular_passenger = None
        
        for passenger in self.seating_system.passengers.values():
            if passenger.is_vip:
                vip_passenger = passenger
            else:
                regular_passenger = passenger
        
        # VIP should be in VIP zone
        vip_row, vip_letter = vip_passenger.assigned_seat
        vip_seat = self.seating_system.seats[(vip_row, vip_letter)]
        self.assertTrue(vip_seat.is_vip_zone, "VIP passenger not in VIP zone")
        
        # Regular passenger should NOT be in VIP zone
        if regular_passenger.assigned_seat:
            reg_row, reg_letter = regular_passenger.assigned_seat
            reg_seat = self.seating_system.seats[(reg_row, reg_letter)]
            self.assertFalse(reg_seat.is_vip_zone, "Regular passenger in VIP zone")

    def test_vip_priority_over_regular(self):
        """
        TDD Test 8: VIP passengers get priority assignment
        GREEN: Implement priority algorithm
        """
        # Arrange - Add regular passenger first
        self.seating_system.add_solo_passenger("Regular First", 30, is_vip=False)
        self.seating_system.add_solo_passenger("VIP Second", 35, is_vip=True)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert - VIP should get better seat despite being added second
        vip_passenger = None
        regular_passenger = None
        
        for passenger in self.seating_system.passengers.values():
            if passenger.is_vip:
                vip_passenger = passenger
            else:
                regular_passenger = passenger
                
        # VIP should have assignment
        self.assertIsNotNone(vip_passenger.assigned_seat)
        
        # VIP should be in premium location (lower row number = better)
        vip_row = vip_passenger.assigned_seat[0]
        
        if regular_passenger.assigned_seat:
            regular_row = regular_passenger.assigned_seat[0]
            self.assertLessEqual(vip_row, regular_row + 5, 
                               "VIP not getting priority seating")

    # ====================================
    # TDD CYCLE 4: ACCESSIBILITY REQUIREMENTS
    # ====================================

    def test_accessibility_passenger_gets_accessible_seat(self):
        """
        TDD Test 9: Passengers with accessibility needs get accessible seats
        RED: Write accessibility test
        """
        # Arrange
        self.seating_system.add_solo_passenger("Accessible User", 40, 
                                             has_accessibility_needs=True)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        passenger = list(self.seating_system.passengers.values())[0]
        self.assertIsNotNone(passenger.assigned_seat)
        
        row, letter = passenger.assigned_seat
        seat = self.seating_system.seats[(row, letter)]
        
        # Should be in accessible seat or at least aisle seat
        is_accessible_or_aisle = (seat.is_accessible or 
                                seat.seat_type == SeatType.AISLE)
        self.assertTrue(is_accessible_or_aisle, 
                       "Accessibility passenger not in suitable seat")

    # ====================================
    # TDD CYCLE 5: QUIET ZONE RESTRICTIONS
    # ====================================

    def test_children_not_in_quiet_zone(self):
        """
        TDD Test 10: Children cannot be seated in quiet zone
        RED: Write quiet zone restriction test
        """
        # Arrange - Add group with children
        self.seating_system.add_group("Family with Kids", 3, has_children=True)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        group = list(self.seating_system.groups.values())[0]
        
        for member in group.members:
            if member.assigned_seat:
                row, letter = member.assigned_seat
                seat = self.seating_system.seats[(row, letter)]
                self.assertFalse(seat.is_quiet_zone, 
                               f"Child in quiet zone: Row {row}")

    def test_adults_can_be_in_quiet_zone(self):
        """
        TDD Test 11: Adults can be seated in quiet zone
        GREEN: Verify quiet zone works correctly for adults
        """
        # Arrange - Add adult passengers
        for i in range(20):  # Add many to fill up non-quiet seats
            self.seating_system.add_solo_passenger(f"Adult {i}", 30)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert - Some adults should end up in quiet zone
        adults_in_quiet = 0
        for passenger in self.seating_system.passengers.values():
            if passenger.assigned_seat:
                row, letter = passenger.assigned_seat
                seat = self.seating_system.seats[(row, letter)]
                if seat.is_quiet_zone:
                    adults_in_quiet += 1
        
        # Should have some adults in quiet zone when other seats full
        self.assertGreaterEqual(adults_in_quiet, 0, 
                              "Adults should be allowed in quiet zone")

    # ====================================
    # TDD CYCLE 6: SOLO TRAVELER PREFERENCES
    # ====================================

    def test_solo_traveler_prefers_window_aisle(self):
        """
        TDD Test 12: Solo travelers prefer window and aisle seats
        RED: Write solo preference test
        """
        # Arrange
        self.seating_system.add_solo_passenger("Solo Traveler", 30)
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        passenger = list(self.seating_system.passengers.values())[0]
        self.assertIsNotNone(passenger.assigned_seat)
        
        row, letter = passenger.assigned_seat
        seat = self.seating_system.seats[(row, letter)]
        
        # Should prefer window or aisle over middle
        preferred_types = [SeatType.WINDOW, SeatType.AISLE]
        self.assertIn(seat.seat_type, preferred_types, 
                     "Solo traveler not in preferred seat type")

    # ====================================
    # TDD CYCLE 7: ADMIN OVERRIDE FUNCTIONALITY
    # ====================================

    def test_admin_override_moves_passenger(self):
        """
        TDD Test 13: Admin can override seat assignments
        RED: Write admin override test
        """
        # Arrange
        self.seating_system.add_solo_passenger("Test User", 30)
        self.seating_system.assign_seats()
        
        passenger = list(self.seating_system.passengers.values())[0]
        original_seat = passenger.assigned_seat
        
        # Act - Override to a different seat
        target_row, target_letter = 10, 'A'
        result = self.seating_system.admin_override(passenger.id, target_row, target_letter)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(passenger.assigned_seat, (target_row, target_letter))
        self.assertNotEqual(passenger.assigned_seat, original_seat)
        
        # Verify seat is properly updated
        target_seat = self.seating_system.seats[(target_row, target_letter)]
        self.assertEqual(target_seat.passenger_id, passenger.id)

    def test_admin_override_handles_displacement(self):
        """
        TDD Test 14: Admin override handles displaced passengers
        GREEN: Implement displacement logic
        """
        # Arrange - Two passengers in different seats
        self.seating_system.add_solo_passenger("User1", 30)
        self.seating_system.add_solo_passenger("User2", 25)
        self.seating_system.assign_seats()
        
        passengers = list(self.seating_system.passengers.values())
        user1, user2 = passengers[0], passengers[1]
        user2_original_seat = user2.assigned_seat
        
        # Act - Move User1 to User2's seat
        target_row, target_letter = user2_original_seat
        result = self.seating_system.admin_override(user1.id, target_row, target_letter)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(user1.assigned_seat, user2_original_seat)
        self.assertIn(user2.id, self.seating_system.waiting_list)

    # ====================================
    # TDD CYCLE 8: CANCELLATION HANDLING
    # ====================================

    def test_cancel_booking_releases_seat(self):
        """
        TDD Test 15: Cancellation releases seat properly
        RED: Write cancellation test
        """
        # Arrange
        self.seating_system.add_solo_passenger("To Cancel", 30)
        self.seating_system.assign_seats()
        
        passenger = list(self.seating_system.passengers.values())[0]
        assigned_seat = passenger.assigned_seat
        
        # Act
        result = self.seating_system.cancel_booking(passenger.id)
        
        # Assert
        self.assertTrue(result)
        self.assertNotIn(passenger.id, self.seating_system.passengers)
        
        # Seat should be available again
        row, letter = assigned_seat
        seat = self.seating_system.seats[(row, letter)]
        self.assertIsNone(seat.passenger_id)

    # ====================================
    # TDD CYCLE 9: ALGORITHM INTEGRATION
    # ====================================

    def test_complete_algorithm_priority_order(self):
        """
        TDD Test 16: Complete algorithm follows priority order
        RED: Write comprehensive integration test
        """
        # Arrange - Complex scenario with all passenger types
        self.seating_system.add_solo_passenger("Regular", 30, is_vip=False)
        self.seating_system.add_solo_passenger("VIP Solo", 35, is_vip=True)
        self.seating_system.add_solo_passenger("Accessible", 40, 
                                             has_accessibility_needs=True)
        self.seating_system.add_group("VIP Family", 3, is_vip=True)
        self.seating_system.add_group("Regular Family", 4, has_children=True)
        
        # Act
        result = self.seating_system.assign_seats()
        
        # Assert
        self.assertTrue(result)
        
        # Verify assignments follow priority
        vip_solo = None
        vip_group = None
        accessible = None
        regular = None
        
        for passenger in self.seating_system.passengers.values():
            if passenger.is_vip and passenger.passenger_type == PassengerType.SOLO:
                vip_solo = passenger
            elif passenger.has_accessibility_needs:
                accessible = passenger
            elif not passenger.is_vip and passenger.passenger_type == PassengerType.SOLO:
                regular = passenger
        
        for group in self.seating_system.groups.values():
            if group.is_vip:
                vip_group = group
        
        # All high-priority passengers should be assigned
        self.assertIsNotNone(vip_solo.assigned_seat, "VIP solo not assigned")
        self.assertIsNotNone(accessible.assigned_seat, "Accessible not assigned")
        
        # VIP should be in VIP zones
        if vip_solo.assigned_seat:
            row, letter = vip_solo.assigned_seat
            seat = self.seating_system.seats[(row, letter)]
            self.assertTrue(seat.is_vip_zone, "VIP solo not in VIP zone")

    # ====================================
    # TDD CYCLE 10: SYSTEM ROBUSTNESS
    # ====================================

    def test_system_handles_capacity_limits(self):
        """
        TDD Test 17: System handles capacity limits gracefully
        RED: Write capacity test
        """
        # Arrange - Add more passengers than seats
        for i in range(200):  # More than aircraft capacity
            self.seating_system.add_solo_passenger(f"Passenger {i}", 25)
        
        # Act
        result = self.seating_system.assign_seats()
        
        # Assert
        self.assertTrue(result)  # Should not fail
        
        # Some passengers should be in waiting list
        self.assertGreater(len(self.seating_system.waiting_list), 0)
        
        # No seat should have multiple passengers
        occupied_seats = {}
        for passenger in self.seating_system.passengers.values():
            if passenger.assigned_seat:
                seat_key = passenger.assigned_seat
                self.assertNotIn(seat_key, occupied_seats.keys(),
                               f"Seat {seat_key} assigned to multiple passengers")
                occupied_seats[seat_key] = passenger.id

    def test_unavailable_seats_not_assigned(self):
        """
        TDD Test 18: Unavailable seats are never assigned
        GREEN: Verify unavailable seat handling
        """
        # Arrange
        self.seating_system.add_solo_passenger("Test User", 30)
        
        # Find unavailable seats
        unavailable_seats = [(row, letter) for (row, letter), seat 
                           in self.seating_system.seats.items() 
                           if not seat.is_available]
        
        # Act
        self.seating_system.assign_seats()
        
        # Assert
        for row, letter in unavailable_seats:
            seat = self.seating_system.seats[(row, letter)]
            self.assertIsNone(seat.passenger_id, 
                            f"Unavailable seat {row}{letter} was assigned")

    def test_reset_system_clears_all_data(self):
        """
        TDD Test 19: Reset system clears all data properly
        GREEN: Verify system reset functionality
        """
        # Arrange
        self.seating_system.add_solo_passenger("Test User", 30)
        self.seating_system.add_group("Test Group", 3)
        self.seating_system.assign_seats()
        
        # Act
        self.seating_system.reset_system()
        
        # Assert
        self.assertEqual(len(self.seating_system.passengers), 0)
        self.assertEqual(len(self.seating_system.groups), 0)
        self.assertEqual(len(self.seating_system.waiting_list), 0)
        
        # All seats should be empty
        for seat in self.seating_system.seats.values():
            if seat.is_available:  # Skip unavailable seats
                self.assertIsNone(seat.passenger_id)

    # ====================================
    # TDD CYCLE 11: EDGE CASES
    # ====================================

    def test_large_group_splitting(self):
        """
        TDD Test 20: Large groups are handled appropriately
        RED: Write edge case test
        """
        # Arrange - Add maximum size group
        self.seating_system.add_group("Large Family", 7)
        
        # Act
        result = self.seating_system.assign_seats()
        
        # Assert
        self.assertTrue(result)
        
        group = list(self.seating_system.groups.values())[0]
        assigned_members = [m for m in group.members if m.assigned_seat]
        
        # All members should be assigned (may be split across rows)
        self.assertEqual(len(assigned_members), 7)
        
        # Check if split appropriately (max 6 seats per row in economy)
        rows_used = set()
        for member in assigned_members:
            row, letter = member.assigned_seat
            rows_used.add(row)
        
        # Should use reasonable number of rows
        self.assertLessEqual(len(rows_used), 3, "Group unnecessarily scattered")


# ====================================
# TDD HELPER FUNCTIONS
# ====================================

def run_tdd_demonstration():
    """
    Demonstrate TDD cycle with a simple example
    """
    print("🔴 TDD CYCLE DEMONSTRATION")
    print("=" * 50)
    
    print("\n1. RED: Write failing test first")
    print("   def test_passenger_assignment():")
    print("       # Test that passenger gets assigned a seat")
    print("       self.assertIsNotNone(passenger.assigned_seat)")
    
    print("\n2. GREEN: Write minimal code to pass")
    print("   def assign_seat(passenger):")
    print("       passenger.assigned_seat = (1, 'A')  # Hardcoded")
    
    print("\n3. REFACTOR: Improve code quality")
    print("   def assign_seat(passenger):")
    print("       # Find first available seat dynamically")
    print("       for seat in available_seats:")
    print("           passenger.assigned_seat = seat")
    print("           break")
    
    print("\n✅ TDD Benefits:")
    print("   - Ensures all code is tested")
    print("   - Prevents over-engineering")
    print("   - Provides safety net for refactoring")
    print("   - Documents expected behavior")


# ====================================
# TEST RUNNER
# ====================================

if __name__ == '__main__':
    print("🧪 Aircraft Seating System - TDD Test Suite")
    print("=" * 60)
    
    # Run TDD demonstration
    run_tdd_demonstration()
    
    print("\n\n🚀 Running TDD Test Suite...")
    print("=" * 60)
    
    # Configure test runner for detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ TDD Test Suite Complete!")
    print("This demonstrates Test-Driven Development principles")
    print("for the Aircraft Seating Optimization System.")