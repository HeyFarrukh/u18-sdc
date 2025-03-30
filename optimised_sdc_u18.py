from guizero import App, Text, PushButton, TextBox, Window, info, Picture, Combo, Box, ListBox
import mysql.connector
from mysql.connector import errorcode
import re


# --- Database Configuration ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "sdc_farrukh_u18"



# --- Color Variables ---
BG_COLOR = "purple"
BUTTON_BG_COLOR = "white"
BUTTON_TEXT_COLOR = "black"
TEXT_COLOR = "white"

# --- Database Connection ---
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)


cursor = conn.cursor(dictionary=True)


# --- GUI Functions ---

def go_back(current_window, previous_window):
    """Hides the current window and shows the previous window."""
    current_window.hide()
    previous_window.show()

# --- Helper functions for back buttons ---
def go_back_to_admin_main():
    go_back(admin_main_window, app)
def go_back_to_admin_main_from_customers():
    go_back(customers_window, admin_main_window)

def go_back_to_admin_main_from_destinations():
        go_back(destinations_window, admin_main_window)

def go_back_to_admin_main_from_coaches():
        go_back(coaches_window, admin_main_window)

def go_back_to_admin_main_from_drivers():
        go_back(drivers_window, admin_main_window)

def go_back_to_staff_main_from_customers():
    go_back(staff_customers_window, staff_window)
def go_back_to_staff_main_from_bookings():
    go_back(staff_bookings_window, staff_window)

def go_back_to_staff_main_from_destinations():
    go_back(staff_destinations_window, staff_window)

def go_back_to_staff_main_from_trips():
    go_back(staff_trips_window, staff_window)

def go_back_to_staff_bookings_menu_from_data():
    go_back(bookings_data_window, staff_bookings_window)

def go_back_to_admin_customers_menu_from_data():
    go_back(customers_data_window, customers_window)

def go_back_to_admin_coaches_menu_from_data():
    go_back(coaches_data_window, coaches_window)

def go_back_to_admin_destinations_menu_from_data():
    go_back(destinations_data_window, destinations_window)

def go_back_to_admin_drivers_menu_from_data():
    go_back(drivers_data_window, drivers_window)

def go_back_to_admin_trips_menu_from_data():
    go_back(trips_data_window, staff_trips_window)

def go_back_to_main_menu():  # go back to the first screen
    go_back(staff_window, app)


# --- Data Fetching Functions ---
def get_all_bookings():
    """Fetches all bookings from the database."""
    try:
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()
        return bookings
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching bookings: {err}")
        return None

def get_all_customers():
    """Fetches all customers from the database."""
    try:
        cursor.execute("SELECT * FROM customers")
        customers = cursor.fetchall()
        return customers
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching customers: {err}")
        return None

def get_all_coaches():
    """Fetches all coaches from the database."""
    try:
        cursor.execute("SELECT * FROM coaches")
        coaches = cursor.fetchall()
        return coaches
    except mysql.connector.Error as err:
         info("Database Error", f"Error fetching coaches: {err}")
         return None

def get_all_destinations():
    """Fetches all destinations from the database"""
    try:
        cursor.execute("SELECT * FROM destinations")
        destinations = cursor.fetchall()
        return destinations
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching destinations: {err}")
        return None

def get_all_drivers():
    """Fetches all drivers from the database."""
    try:
        cursor.execute("SELECT * FROM drivers")
        drivers = cursor.fetchall()
        return drivers
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching drivers: {err}")
        return None

def get_all_trips():
    """Fetches all the trips from the database"""
    try:
        cursor.execute("SELECT * FROM trips")
        trips = cursor.fetchall()
        return trips
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching trips: {err}")


# --- Function to open a new window and display data ---
def open_bookings_data_window():
    """Opens a new window to display booking data in a table."""
    staff_bookings_window.hide()
    global bookings_data_window
    bookings_data_window = Window(app, title="Booking Data", width=900, height=600, bg=BG_COLOR)
    Text(bookings_data_window, text="All Bookings", color=TEXT_COLOR, size=14, font="Arial")
    bookings_list = ListBox(bookings_data_window,  width="fill", height="fill", scrollbar=True) # ListBox in the new window

    back_button_box = Box(bookings_data_window, layout="auto", width="fill") # Box for back button in data window
    back_button = PushButton(back_button_box, text="Back to Bookings Menu", command=go_back_to_staff_bookings_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR


    bookings_data = get_all_bookings()
    if bookings_data:
        # Create a header string with appropriate spacing
        header = f"{'Booking ID':<10}{'Customer ID':<12}{'Trip ID':<8}{'Cost':<8}{'People':<8}{'Special Request':<30}{'Booking Date':<12}"  # Adjust spacing as needed
        bookings_list.append(header) # Add the header as the first item.
        bookings_list.append("-" * 80) #Separator

        for booking in bookings_data:
            bookings_list.append(f"Booking ID: {booking['BookingID']}, Customer ID: {booking['CustomerID']}, Trip ID: {booking['TripID']}, Cost: {booking['BookingCost']}, People: {booking['NumberofPeople']}, Date: {booking['BookingDate']}")
    else:
        bookings_list.append("Could not retrieve booking data.")

    back_button_box = Box(bookings_data_window, layout="auto", width="fill")
    back_button = PushButton(back_button_box, text="Back to Bookings Menu", command=go_back_to_staff_bookings_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR;
    bookings_data_window.show()


def open_customers_data_window():
    customers_window.hide()
    global customers_data_window
    customers_data_window = Window(app, title = "Customer Data", width = 1100, height = 600, bg = BG_COLOR)  # Adjusted width
    Text(customers_data_window, text="All Customers", color = TEXT_COLOR, size = 14, font="Arial")

    # Use a ListBox with built in scrollbar
    customers_list = ListBox(customers_data_window, width="fill", height="fill", scrollbar=True)

    customers_data = get_all_customers()
    if customers_data:
        # Header
        header = (f"{'Customer ID':<12}{'First Name':<15}{'Surname':<15}{'Email':<25}"
                  f"{'Address Line 1':<25}{'Address Line 2':<25}{'City':<15}{'Postcode':<10}"
                  f"{'Phone Number':<15}{'Notes':<20}")
        customers_list.append(header)
        customers_list.append("-" * 140)


        for customer in customers_data:
            # Corrected attribute names here
            customers_list.append(f"Customer ID: {customer['CustomerID']}, Name: {customer['FirstName']} {customer['Surname']}, Email: {customer['Email']}, Address: {customer['AddressLine1']} {customer['AddressLine2']} {customer['City']} {customer['Postcode']}, Phone: {customer['PhoneNumber']}, Notes: {customer['SpecialNotes']}")
    else:
        customers_list.append("Could not retrieve customer data.")

    back_button_box = Box(customers_data_window, layout="auto", width="fill")
    back_button = PushButton(back_button_box, text = "Back to Customers Menu", command=go_back_to_admin_customers_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    customers_data_window.show()


def open_coaches_data_window():
    coaches_window.hide()
    global coaches_data_window
    coaches_data_window = Window(app, title = "Coach Data", width = 800, height = 600, bg=BG_COLOR)
    Text(coaches_data_window, text="All Coaches", color=TEXT_COLOR, size = 14, font = "Arial")

    coaches_list = ListBox(coaches_data_window, width="fill", height="fill", scrollbar=True)


    # --- Header Row ---
    header = f"{'Coach ID':<8}{'Registration':<15}{'Seats':<6}"
    coaches_list.append(header)
    coaches_list.append("-" * 30) #separator

    coaches_data = get_all_coaches()
    if coaches_data:
        for coach in coaches_data:
            # Corrected attribute names here
            coaches_list.append(f"Coach ID: {coach['CoachID']}, Registration: {coach['Registration']}, Seats: {coach['Seats']}")
    else:
        coaches_list.append("Could not retrieve coach data.")


    back_button_box = Box(coaches_data_window, layout="auto", width="fill")
    back_button = PushButton(back_button_box, text="Back to Coaches Menu", command=go_back_to_admin_coaches_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    coaches_data_window.show()

def open_destinations_data_window():
    destinations_window.hide()
    global destinations_data_window
    destinations_data_window = Window(app, title="Destination Data", width = 800, height=600, bg=BG_COLOR)
    Text(destinations_data_window, text="All Destinations", color = TEXT_COLOR, size=14, font="Arial")

    destinations_list = ListBox(destinations_data_window, width="fill", height="fill", scrollbar=True)

    # --- Header Row ---
    header = (f"{'Destination ID':<15}{'Name':<25}{'Hotel':<25}{'Cost':<8}{'City':<15}{'Days':<6}")
    destinations_list.append(header)
    destinations_list.append("-" * 90)

    destinations_data = get_all_destinations()
    if destinations_data:

        for destination in destinations_data:
             # Corrected attribute names here
            destinations_list.append(f"Destination ID: {destination['DestinationID']}, Name: {destination['DestinationName']}, Hotel: {destination['Hotel']}, Cost: {destination['DestinationCost']}, City: {destination['CityName']}, Days: {destination['Days']}")
    else:
        destinations_list.append("Could not retrieve destination data.")


    back_button_box = Box(destinations_data_window, layout="auto", width="fill")
    back_button = PushButton(back_button_box, text="Back to Destinations Menu", command=go_back_to_admin_destinations_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR
    destinations_data_window.show()

def open_drivers_data_window():
    drivers_window.hide() #Correct Window
    global drivers_data_window
    drivers_data_window = Window(app, title="Driver Data", width=800, height=600, bg=BG_COLOR)
    Text(drivers_data_window, text="All Drivers", color = TEXT_COLOR, size=14, font="Arial")

    # Use ListBox with scrollbar
    drivers_list = ListBox(drivers_data_window, width = "fill", height = "fill", scrollbar=True)

    # --- Header row ---
    header = f"{'Driver ID':<10}{'Driver Name':<20}"
    drivers_list.append(header)
    drivers_list.append("-" * 30)

    drivers_data = get_all_drivers()
    if drivers_data:
        for driver in drivers_data:
            drivers_list.append(f"{driver['DriverID']:<10}{driver['DriverName']:<20}")
    else:
        drivers_list.append("Could not retrieve driver data.")


    back_button_box = Box(drivers_data_window, layout="auto", width = "fill")
    back_button = PushButton(back_button_box, text="Back to Drivers Menu", command=go_back_to_admin_drivers_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR
    drivers_data_window.show()

def open_trips_data_window():
    staff_trips_window.hide()
    global trips_data_window
    trips_data_window = Window(app, title = "Trip Data", width=800, height = 600, bg=BG_COLOR)
    Text(trips_data_window, text="All Trips", color=TEXT_COLOR, size=14, font="Arial")
    trips_list = ListBox(trips_data_window, width="fill", height = "fill", scrollbar=True)
    
    header = f"{'Trip ID':<8}{'Coach ID':<10}{'Driver ID':<10}{'Destination ID':<15}{'Date':<12}"
    trips_list.append(header)
    trips_list.append("-" * 60)


    trips_data = get_all_trips()
    if trips_data:

        for trip in trips_data:
            row_string = (f"{trip['TripID']:<8}"
                          f"{trip['CoachID']:<10}"
                          f"{trip['DriverID']:<10}"
                          f"{trip['DestinationID']:<15}"
                          f"{trip['Date']}")
            trips_list.append(row_string)

    else:
        trips_list.append("Could not retrieve trip data.")


    back_button_box = Box(trips_data_window, layout = "auto", width="fill")
    back_button = PushButton(back_button_box, text="Back to Trips Menu", command=go_back_to_staff_main_from_trips)
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR
    trips_data_window.show()


#region Admin Windows
# --- Admin Window Functions ---
def open_customers_window():
    admin_main_window.hide()
    global customers_window
    customers_window = Window(app, title="Admin Customers", width=800, height=600, bg=BG_COLOR)
    Text(customers_window, text="Customers", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(customers_window, layout="auto", width="fill")
    view_customers_button = PushButton(button_box, text="View Customers", width=20, command=open_customers_data_window)
    remove_customers_button = PushButton(button_box, text="Remove Customers", width=20, command=open_remove_customer_window)

    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_customers)
    view_customers_button.bg = BUTTON_BG_COLOR;  view_customers_button.text_color = BUTTON_TEXT_COLOR
    remove_customers_button.bg = BUTTON_BG_COLOR; remove_customers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    customers_window.show()

def open_destinations_window():
    admin_main_window.hide()
    global destinations_window
    destinations_window = Window(app, title="Admin Destinations", width=800, height=600, bg=BG_COLOR)
    Text(destinations_window, text="Destinations", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(destinations_window, layout="auto", width="fill")
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20, command=open_destinations_data_window)
    add_destinations_button = PushButton(button_box, text="Add Destinations", width=20, command=open_add_destination_window)

    remove_destinations_button = PushButton(button_box, text="Remove Destinations", width=20, command=open_remove_destination_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_destinations)
    view_destinations_button.bg = BUTTON_BG_COLOR
    add_destinations_button.bg = BUTTON_BG_COLOR
    remove_destinations_button.bg = BUTTON_BG_COLOR
    back_button.bg = BUTTON_BG_COLOR
    destinations_window.show()

def open_coaches_window():
    admin_main_window.hide()
    global coaches_window
    coaches_window = Window(app, title="Admin Coaches", width=800, height=600, bg=BG_COLOR)
    Text(coaches_window, text="Coaches", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(coaches_window, layout="auto", width="fill")
    view_coaches_button = PushButton(button_box, text="View Coaches", width=20, command=open_coaches_data_window)
    add_coaches_button = PushButton(button_box, text="Add Coaches", width=20, command=open_add_coach_window)
    remove_coaches_button = PushButton(button_box, text="Remove Coaches", width=20, command=open_remove_coach_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_coaches)

    view_coaches_button.bg = BUTTON_BG_COLOR; view_coaches_button.text_color = BUTTON_TEXT_COLOR
    add_coaches_button.bg = BUTTON_BG_COLOR; add_coaches_button.text_color = BUTTON_TEXT_COLOR
    remove_coaches_button.bg = BUTTON_BG_COLOR; remove_coaches_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    coaches_window.show()

def open_drivers_window():
    admin_main_window.hide()
    global drivers_window
    drivers_window = Window(app, title="Admin Drivers", width=800, height=600, bg=BG_COLOR)
    Text(drivers_window, text="Drivers", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(drivers_window, layout="auto", width="fill")
    view_drivers_button = PushButton(button_box, text="View Drivers", width=20, command=open_drivers_data_window)
    add_drivers_button = PushButton(button_box, text="Add Drivers", width=20, command=open_add_driver_window)
    remove_drivers_button = PushButton(button_box, text="Remove Drivers", width=20, command=open_remove_driver_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_drivers)
    view_drivers_button.bg = BUTTON_BG_COLOR; view_drivers_button.text_color = BUTTON_TEXT_COLOR
    add_drivers_button.bg = BUTTON_BG_COLOR; add_drivers_button.text_color = BUTTON_TEXT_COLOR
    remove_drivers_button.bg = BUTTON_BG_COLOR; remove_drivers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    drivers_window.show()


def open_admin_main_window():
    admin_login_window.hide()
    global admin_main_window
    admin_main_window = Window(app, title="Admin Main", width=800, height=600, bg=BG_COLOR)
    Text(admin_main_window, text="Main Menu", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(admin_main_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_customers_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_destinations_window)
    coaches_button = PushButton(button_box, text="COACHES", width=15, command=open_coaches_window)
    drivers_button = PushButton(button_box, text="DRIVERS", width=15, command=open_drivers_window)
    search_button = PushButton(button_box, text="SEARCH", width=15, command=open_query_window) # Added Search button
    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    coaches_button.bg = BUTTON_BG_COLOR; coaches_button.text_color = BUTTON_TEXT_COLOR
    drivers_button.bg = BUTTON_BG_COLOR; drivers_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR # Style for Search button
    admin_main_window.show()

#region Staff Windows
# --- Staff Window Functions ---
def open_staff_customers_window():
    staff_window.hide()
    global staff_customers_window
    staff_customers_window = Window(app, title="Staff Customers", width=800, height=600, bg=BG_COLOR)
    Text(staff_customers_window, text="Customers", color=TEXT_COLOR)
    button_box = Box(staff_customers_window, layout="auto", width="fill")
    add_customer_button = PushButton(button_box, text="Add Customer", width=20, command=open_add_customer_window)
    remove_customer_button = PushButton(button_box, text="Remove Customer", width=20, command=open_remove_customer_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_customers)
    add_customer_button.bg = BUTTON_BG_COLOR; add_customer_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_button.bg = BUTTON_BG_COLOR; remove_customer_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_customers_window.show()


def open_staff_bookings_window(): # New function for staff bookings window
    staff_window.hide()
    global staff_bookings_window # Made staff_bookings_window global so data window can go back
    staff_bookings_window = Window(app, title="Staff Bookings", width=800, height=600, bg=BG_COLOR)
    Text(staff_bookings_window, text="Bookings", color=TEXT_COLOR)
    button_box = Box(staff_bookings_window, layout="auto", width="fill")
    view_bookings_button = PushButton(button_box, text="View Bookings", width=20, command=open_bookings_data_window) # Call new window function
    add_booking_button = PushButton(button_box, text="Add Booking", width=20, command=open_add_booking_window)
    remove_booking_button = PushButton(button_box, text="Remove Booking", width=20, command=open_remove_booking_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_bookings)

    view_bookings_button.bg = BUTTON_BG_COLOR; view_bookings_button.text_color = BUTTON_TEXT_COLOR
    add_booking_button.bg = BUTTON_BG_COLOR; add_booking_button.text_color = BUTTON_TEXT_COLOR
    remove_booking_button.bg = BUTTON_BG_COLOR; remove_booking_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR

    staff_bookings_window.show()


def open_staff_destinations_window():
    staff_window.hide()
    global staff_destinations_window
    staff_destinations_window = Window(app, title="Staff Destinations", width=800, height=600, bg=BG_COLOR)
    Text(staff_destinations_window, text="Destinations", color=TEXT_COLOR)
    button_box = Box(staff_destinations_window, layout="auto", width="fill")
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20, command=open_destinations_data_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_destinations)
    view_destinations_button.bg = BUTTON_BG_COLOR; view_destinations_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_destinations_window.show()

def open_staff_trips_window():
    staff_window.hide()
    global staff_trips_window
    staff_trips_window = Window(app, title="Staff Trips", width=800, height=600, bg=BG_COLOR)
    Text(staff_trips_window, text="Trips", color=TEXT_COLOR)
    button_box = Box(staff_trips_window, layout="auto", width="fill")
    view_trips_button = PushButton(button_box, text="View Trips", width=20, command=open_trips_data_window)
    add_trips_button = PushButton(button_box, text="Add Trips", width=20, command=open_add_trip_window)
    remove_trips_button = PushButton(button_box, text="Remove Trips", width = 20)

    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_trips)
    view_trips_button.bg = BUTTON_BG_COLOR; view_trips_button.text_color = BUTTON_TEXT_COLOR

    add_trips_button.bg = BUTTON_BG_COLOR; add_trips_button.text_color = BUTTON_TEXT_COLOR
    remove_trips_button.bg = BUTTON_BG_COLOR; remove_trips_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_trips_window.show()

def open_staff_window():
    app.hide()
    global staff_window
    staff_window = Window(app, title="Staff Interface", width=800, height=600, bg=BG_COLOR)
    Text(staff_window, text="Main Menu", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_staff_customers_window)
    bookings_button = PushButton(button_box, text="BOOKINGS", width=15, command=open_staff_bookings_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_staff_destinations_window)
    trips_button = PushButton(button_box, text="TRIPS", width=15, command=open_staff_trips_window)
    search_button = PushButton(button_box, text="SEARCH", width=15, command=open_query_window)  # Added Search button here
    back_button = PushButton(button_box, text="Back", width=15, command=go_back_to_main_menu)
    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    bookings_button.bg = BUTTON_BG_COLOR; bookings_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR # Style for search button
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_window.show()


#region Add Windows
def open_add_booking_window():
    global add_booking_window, customer_id_entry, trip_id_entry, booking_cost_entry, num_people_entry, special_request_entry, date_of_booking_entry
    add_booking_window = Window(app, title="Add Booking", width=400, height = 400, bg = BG_COLOR)
    Text(add_booking_window, text = "Enter Booking Details:", color = TEXT_COLOR)

    Text(add_booking_window, text="Customer ID:", color=TEXT_COLOR)
    customer_id_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Trip ID:", color=TEXT_COLOR)
    trip_id_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Booking Cost:", color=TEXT_COLOR)
    booking_cost_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Number of People:", color=TEXT_COLOR)
    num_people_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Special Request:", color=TEXT_COLOR)
    special_request_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Date of Booking (YYYY-MM-DD):", color=TEXT_COLOR)
    date_of_booking_entry = TextBox(add_booking_window)

    # Function for adding booking.
    def add_booking():
        try:
            cursor.execute("""
            INSERT INTO bookings (CustomerID, TripID, BookingCost, NumberofPeople, SpecialRequest, BookingDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (customer_id_entry.value, trip_id_entry.value, booking_cost_entry.value,
             num_people_entry.value, special_request_entry.value, date_of_booking_entry.value))
            conn.commit()
            info("Booking Added", "The booking has been added.")
            add_booking_window.destroy()
            staff_bookings_window.show()

        except mysql.connector.Error as err:
             info("Database Error",f"Error Adding booking to the database. Check Your Input")
             print(f"Database Error: {err}")


    add_button = PushButton(add_booking_window, text="Add Booking", command=add_booking)
    back_button = PushButton(add_booking_window, text="Back", command=add_booking_window.destroy)
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_booking_window.show()

def open_add_coach_window():
    global add_coach_window, coach_reg_entry, seats_entry
    add_coach_window = Window(app, title = "Add Coach", width = 400, height = 400, bg = BG_COLOR)
    Text(add_coach_window, text="Enter Coach Details:", color = TEXT_COLOR)

    Text(add_coach_window, text = "Coach Registration:", color = TEXT_COLOR)
    coach_reg_entry = TextBox(add_coach_window)

    Text(add_coach_window, text="Seats in Coach", color = TEXT_COLOR)
    seats_entry = TextBox(add_coach_window)

    def add_coach():
        try:
            cursor.execute("""
            INSERT INTO coaches (Registration, Seats)
            VALUES (%s, %s)""",
            (coach_reg_entry.value, seats_entry.value))
            conn.commit()
            info("Coach Added", "The coach has been added to the database.")
            add_coach_window.destroy()
            coaches_window.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "There was an error when trying to add coach. Check Your Input")


    add_button = PushButton(add_coach_window, text="Add Coach", command=add_coach)
    back_button = PushButton(add_coach_window, text="Back", command=add_coach_window.destroy)
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_coach_window.show()


def open_add_customer_window():
    global add_customer_window
    global first_name_entry, surname_entry, email_entry, address1_entry, address2_entry
    global city_entry, postcode_entry, phone_entry, notes_entry

    add_customer_window = Window(app, title="Add Customer", width=400, height=600, bg=BG_COLOR)
    Text(add_customer_window, text="Enter Customer Details:", color=TEXT_COLOR)

    Text(add_customer_window, text="First Name:", color=TEXT_COLOR)
    first_name_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Surname:", color=TEXT_COLOR)
    surname_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Email:", color=TEXT_COLOR)
    email_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Address Line 1:", color=TEXT_COLOR)
    address1_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Address Line 2:", color=TEXT_COLOR)
    address2_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="City:", color=TEXT_COLOR)
    city_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Postcode:", color=TEXT_COLOR)
    postcode_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Phone Number:", color=TEXT_COLOR)
    phone_entry = TextBox(add_customer_window)
    Text(add_customer_window, text="Special Notes:", color=TEXT_COLOR)
    notes_entry = TextBox(add_customer_window)

    def add_customer():
        try:
            # Corrected SQL query with correct column names
            cursor.execute("""
                INSERT INTO customers (FirstName, Surname, Email, AddressLine1,
                                       AddressLine2, City, Postcode, PhoneNumber, SpecialNotes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name_entry.value, surname_entry.value, email_entry.value,
                  address1_entry.value, address2_entry.value, city_entry.value,
                  postcode_entry.value, phone_entry.value, notes_entry.value))
            conn.commit()
            info("Success", "Customer added successfully.")
            add_customer_window.destroy()
            staff_customers_window.show()  # or admin, depending on context
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            info("Database Error", "Failed to add customer. Check Your Input")

    add_button = PushButton(add_customer_window, text="Add Customer", command=add_customer)
    back_button = PushButton(add_customer_window, text="Back", command=add_customer_window.destroy)
    add_button.bg = BUTTON_BG_COLOR
    add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR
    add_customer_window.show()

def open_add_destination_window():
    global add_destination_window, destination_name_entry, hotel_name_entry
    global destination_cost_entry, city_name_entry, days_entry

    add_destination_window = Window(app, title = "Add Destination", width = 400, height = 400, bg = BG_COLOR)
    Text(add_destination_window, text = "Enter Destination Details:", color = TEXT_COLOR)

    Text(add_destination_window, text = "Destination Name:", color = TEXT_COLOR)
    destination_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Hotel Name:", color = TEXT_COLOR)
    hotel_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Destination Cost:", color = TEXT_COLOR)
    destination_cost_entry = TextBox(add_destination_window)

    Text(add_destination_window, text="City Name:", color=TEXT_COLOR)
    city_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Days", color = TEXT_COLOR)
    days_entry = TextBox(add_destination_window)

    def add_destination():
        try:
            # Corrected SQL statement with correct column names
            cursor.execute("""
            INSERT INTO destinations (DestinationName, Hotel, DestinationCost, CityName, Days)
            VALUES (%s, %s, %s, %s, %s)""",
            (destination_name_entry.value, hotel_name_entry.value, destination_cost_entry.value,
             city_name_entry.value, days_entry.value))
            conn.commit()
            info("Success", "Destination added successfully.")
            add_destination_window.destroy()
            destinations_window.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to add Destination. Check Your Input")

    add_button = PushButton(add_destination_window, text = "Add Destination", command=add_destination)
    back_button = PushButton(add_destination_window, text="Back", command = add_destination_window.destroy)
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_destination_window.show()


def open_add_driver_window():
    global add_driver_window, driver_name_entry

    add_driver_window = Window(app, title = "Add Driver", width = 400, height = 400, bg = BG_COLOR)
    Text(add_driver_window, text = "Enter the Drivers Details:", color = TEXT_COLOR)

    Text(add_driver_window, text="Driver Name:", color=TEXT_COLOR)
    driver_name_entry = TextBox(add_driver_window)

    def add_driver():
        try:
            cursor.execute("""
            INSERT INTO drivers (DriverName)
            VALUES (%s)""", (driver_name_entry.value,))
            conn.commit()
            info("Success", "Driver added successfully.")
            add_driver_window.destroy()
            drivers_window.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to add Driver. Check Your Input")

    add_button = PushButton(add_driver_window, text="Add Driver", command = add_driver)
    back_button = PushButton(add_driver_window, text="Back", command = add_driver_window.destroy)
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_driver_window.show()

def open_add_trip_window():
    global add_trip_window, coach_combo, driver_combo, destination_combo, date_entry

    add_trip_window = Window(app, title="Add Trip", width = 400, height = 400, bg = BG_COLOR)
    Text(add_trip_window, text = "Enter Trip Details: ", color = TEXT_COLOR)

    Text(add_trip_window, text = "Coach ID:", color = TEXT_COLOR)
    coach_id_entry = TextBox(add_trip_window)

    Text(add_trip_window, text = "Driver:", color = TEXT_COLOR)
    driver_combo = Combo(add_trip_window, options=[], width="fill")
    #Populate Driver Combo
    try:
        cursor.execute("SELECT DriverID, DriverName FROM drivers")
        drivers = cursor.fetchall()
        driver_combo.clear() #clear options
        for driver in drivers:
            driver_combo.append(f"{driver['DriverID']}: {driver['DriverName']}")
    except mysql.connector.Error as err:
        info("Database Error", "Could not load drivers")
        add_trip_window.destroy()
        return

    Text(add_trip_window, text="Destination:", color=TEXT_COLOR)
    destination_combo = Combo(add_trip_window, options=[], width="fill")
     #Populate Destination Combo
    try:
        cursor.execute("SELECT DestinationID, DestinationName FROM destinations")
        destinations = cursor.fetchall()
        destination_combo.clear()
        for destination in destinations:
            destination_combo.append(f"{destination['DestinationID']}: {destination['DestinationName']}")
    except mysql.connector.Error as err:
        info("Database Error", "Could not load destinations")
        add_trip_window.destroy()
        return
    

    Text(add_trip_window, text = "Date (YYYY-MM-DD):", color = TEXT_COLOR)
    date_entry = TextBox(add_trip_window)

    def add_trip():
        try:
            selected_coach = coach_combo.value
            if not selected_coach:
                info("Input Error", "Please select a coach.")
                return
            coach_id = int(selected_coach.split(":")[0])

            selected_driver = driver_combo.value
            if not selected_driver:
                info("Input Error", "Please select a driver.")
                return
            driver_id = int(selected_driver.split(":")[0])

            selected_destination = destination_combo.value
            if not selected_destination:
                info("Input Error", "Please select a destination")
                return
            destination_id = int(selected_destination.split(":")[0])
            # Basic date format check.  Could be more robust.
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"  # YYYY-MM-DD
            if not re.match(date_pattern, date_entry.value):
                 info("Input Error", "Invalid date format. Use YYYY-MM-DD.")
                 return

            cursor.execute("""
            INSERT INTO trips (CoachID, DriverID, DestinationID, Date)
            VALUES (%s, %s, %s, %s)""",
            (coach_id, driver_id, destination_id, date_entry.value))
            conn.commit()
            info("Success", "Trip has been added successfully.")
            add_trip_window.destroy()
            staff_trips_window.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to add Trip. Check Your Input")
        except ValueError:
            info("Input Error", "Invalid ID format selected.")
        except IndexError:
            info("Input Error", "Invalid selection.")

    add_button = PushButton(add_trip_window, text = "Add Trip", command = add_trip)
    back_button = PushButton(add_trip_window, text = "Back", command = add_trip_window.destroy)
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_trip_window.show()
#endregion

#region Remove Windows

def open_remove_booking_window():
    global remove_booking_window, remove_booking_entry

    remove_booking_window = Window(app, title="Remove Booking", width = 400, height = 400, bg = BG_COLOR)
    Text(remove_booking_window, text = "Enter Booking ID you want to remove:", color = TEXT_COLOR)

    remove_booking_entry = TextBox(remove_booking_window)

    def remove_booking():
        try:
            cursor.execute("""
            DELETE FROM bookings
            WHERE BookingID = %s""", (remove_booking_entry.value,))
            conn.commit()
            info("Success", "Booking removed successfully.")
            remove_booking_window.destroy()
            staff_bookings_window.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to remove Booking.  Check that the Booking ID exists.")

    remove_button = PushButton(remove_booking_window, text="Remove Booking", command=remove_booking)
    back_button = PushButton(remove_booking_window, text="Back", command=remove_booking_window.destroy)
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_booking_window.show()


def open_remove_coach_window():
    global remove_coach_window, remove_coach_entry

    remove_coach_window = Window(app, title="Remove Coach", width=400, height=400, bg=BG_COLOR)
    Text(remove_coach_window, text="Enter Coach ID to remove:", color=TEXT_COLOR)
    remove_coach_entry = TextBox(remove_coach_window)

    def remove_coach():
        try:
            cursor.execute("DELETE FROM coaches WHERE CoachID = %s", (remove_coach_entry.value,))
            conn.commit()
            info("Success", "Coach removed successfully.")
            remove_coach_window.destroy()
            coaches_window.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to remove coach. Check that the Coach ID exists.")

    remove_button = PushButton(remove_coach_window, text="Remove Coach", command=remove_coach)
    back_button = PushButton(remove_coach_window, text="Back", command=remove_coach_window.destroy)
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_coach_window.show()

def open_remove_customer_window():
    global remove_customer_window, remove_customer_entry

    remove_customer_window = Window(app, title="Remove Customer", width=400, height=400, bg=BG_COLOR)
    Text(remove_customer_window, text="Enter Customer ID to remove:", color=TEXT_COLOR)
    remove_customer_entry = TextBox(remove_customer_window)
    
    def remove_customer():
        try:
            cursor.execute("DELETE FROM customers WHERE CustomerID = %s", (remove_customer_entry.value,))
            conn.commit()
            info("Success", "Customer removed successfully.")
            remove_customer_window.destroy()
            staff_customers_window.show()
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            info("Database Error", "Failed to remove customer. Check that the Customer ID exists.")

    remove_button = PushButton(remove_customer_window, text="Remove Customer", command=remove_customer)
    back_button = PushButton(remove_customer_window, text="Back", command= remove_customer_window.destroy)
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR;  back_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_window.show()
    

def open_remove_destination_window():
    global remove_destination_window, remove_destination_entry

    remove_destination_window = Window(app, title = "Remove Destination", width = 400, height = 400, bg=BG_COLOR)
    Text(remove_destination_window, text = "Enter the DestinationID you want to remove:", color = TEXT_COLOR)
    remove_destination_entry = TextBox(remove_destination_window)

    def remove_destination():
        try:
            cursor.execute("""
            DELETE FROM destinations
            WHERE DestinationID = %s""", (remove_destination_entry.value,))
            conn.commit()
            info("Success", "Destination removed successfully.")
            remove_destination_window.destroy()
            destinations_window.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", "Failed to remove destination. Check Your Input")

    remove_button = PushButton(remove_destination_window, text="Remove Destination", command=remove_destination)
    back_button = PushButton(remove_destination_window, text="Back", command = remove_destination_window.destroy)
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_destination_window.show()

def open_remove_driver_window():
    global remove_driver_window, remove_driver_entry

    remove_driver_window = Window(app, title = "Remove Driver", width = 400, height = 400, bg = BG_COLOR)
    Text(remove_driver_window, text="Enter Driver ID to remove:", color = TEXT_COLOR)
    remove_driver_entry = TextBox(remove_driver_window)

    def remove_driver():
        try:
            cursor.execute("DELETE FROM drivers WHERE DriverID = %s", (remove_driver_entry.value,))
            conn.commit()
            info("Success", "Driver removed successfully.")
            remove_driver_window.destroy()
            drivers_window.show()
        except mysql.connector.Error as err:
             print(f"Database Error: {err}")
             info("Database Error", "Failed to remove driver. Check that the Driver ID exists.")

    remove_button = PushButton(remove_driver_window, text = "Remove Driver", command = remove_driver)
    back_button = PushButton(remove_driver_window, text="Back", command=remove_driver_window.destroy)
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_driver_window.show()

#endregion

# --- Login and Main App ---
def check_admin_login():
    if username_entry.value.lower() == "admin" and password_entry.value == "admin":
        open_admin_main_window()
    else:
        info("Login Failed", "Incorrect username or password.")


def open_query_window():
    """Opens a window for executing various database queries."""
    query_window = Window(app, title="Database Queries", width=800, height=600, bg=BG_COLOR)
    Text(query_window, text="Select a Query:", color=TEXT_COLOR)

    # --- Query 1: Passengers on a specific trip ---
    def lincoln_passengers():
        # 1.  Create a sub-window for destination and date selection.
        selection_window = Window(query_window, title="Select Trip", width=400, height=200, bg=BG_COLOR)
        Text(selection_window, text="Select Destination:", color=TEXT_COLOR)

        # Use a Combo box for destinations.
        destination_combo = Combo(selection_window, options=[], width="fill") 
        Text(selection_window, text="Enter Date (YYYY-MM-DD):", color=TEXT_COLOR)
        date_entry = TextBox(selection_window)

        # 2. Populate the destination Combo box.
        try:
            cursor.execute("SELECT DestinationID, DestinationName FROM destinations")
            destinations = cursor.fetchall()
            destination_options = [f"{dest['DestinationID']}: {dest['DestinationName']}" for dest in destinations]

            destination_combo.clear() 
            for option in destination_options:
                destination_combo.append(option)

        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching destinations: {err}")
            selection_window.destroy()  # Close if can't get destinations
            return

        # 3.   function that  the query (with parameters).
        def run_passenger_query():
            try:
                selected_destination = destination_combo.value
                trip_date = date_entry.value

                # Error handling for empty input.
                if not selected_destination or not trip_date:
                    info("Input Error", "Please select a destination and enter a date.")
                    return

                # Extract DestinationID from the Combo selection
                destination_id = int(selected_destination.split(":")[0])


                cursor.execute("""
                    SELECT c.FirstName, c.Surname
                    FROM customers c
                    JOIN bookings b ON c.CustomerID = b.CustomerID
                    JOIN trips t ON b.TripID = t.TripID
                    JOIN destinations d ON t.DestinationID = d.DestinationID
                    WHERE d.DestinationID = %s AND t.Date = %s
                """, (destination_id, trip_date))
                passengers = cursor.fetchall()

                result_window = Window(query_window, title="Passengers", width=400, height=300, bg=BG_COLOR)
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
                if passengers:
                    for passenger in passengers:
                        result_list.append(f"{passenger['FirstName']} {passenger['Surname']}")
                else:
                    result_list.append("No passengers found for this trip.")
                close_button = PushButton(result_window, text="Close", command=result_window.destroy)
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show()
                selection_window.destroy()  # Close selection window *after* showing results

            except mysql.connector.Error as err:
                info("Database Error", f"Error fetching passenger data: {err}")
            except ValueError:  # Handle errors if the date isn't valid.
                info("Input Error", "Invalid date format.  Please use YYYY-MM-DD.")
            except IndexError:
                info("Input Error", "Invalid destination selection")


        # 4. Buttons within the selection window
        ok_button = PushButton(selection_window, text="OK", command=run_passenger_query)
        cancel_button = PushButton(selection_window, text="Cancel", command=selection_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        selection_window.show()


    # --- Query 2: Available trips in chronological order ---
    def available_trips():
        try:
            cursor.execute("""
                SELECT t.Date, d.DestinationName, d.CityName
                FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                WHERE t.Date >= CURDATE()
                ORDER BY t.Date DESC
            """)
            trips = cursor.fetchall()

            result_window = Window(query_window, title="Available Trips", width=600, height=400, bg=BG_COLOR)
            result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
            if trips:
                for trip in trips:
                    result_list.append(f"Date: {trip['Date']}, Destination: {trip['DestinationName']}, City: {trip['CityName']}")
            else:
                result_list.append("No trips currently available.")
            close_button = PushButton(result_window, text = "Close", command = result_window.destroy)
            close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
            result_window.show()

        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trip data: {err}")

   # --- Query 3: Customers in a given postcode area ---
    def postcode_customers():
        # Create a sub-window to get postcode input
        postcode_window = Window(query_window, title="Enter Postcode", width=300, height=150, bg=BG_COLOR)
        Text(postcode_window, text="Enter Postcode:", color=TEXT_COLOR)
        postcode_entry = TextBox(postcode_window)

        def run_postcode_query():
            try:
                postcode = postcode_entry.value

                if not postcode:  # Check for empty input
                    info("Input Error", "Please enter a postcode.")
                    return

                # Using parameterised query for safety!
                cursor.execute("""
                    SELECT FirstName, Surname, AddressLine1, AddressLine2, City, Postcode
                    FROM customers
                    WHERE Postcode LIKE %s
                """, (postcode + '%',))  # Added % for wildcard matching
                customers = cursor.fetchall()

                result_window = Window(query_window, title=f"Customers in {postcode}", width=600, height=400, bg=BG_COLOR)
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)

                if customers:
                    for customer in customers:
                        result_list.append(f"{customer['FirstName']} {customer['Surname']}, {customer['AddressLine1']}, {customer['AddressLine2']}, {customer['City']}, {customer['Postcode']}")
                else:
                    result_list.append(f"No customers found in {postcode}.")

                close_button = PushButton(result_window, text="Close", command=result_window.destroy)
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show()
                postcode_window.destroy()  # Close input window

            except mysql.connector.Error as err:
                info("Database Error", f"Error fetching customer data: {err}")

        ok_button = PushButton(postcode_window, text="OK", command=run_postcode_query)
        cancel_button = PushButton(postcode_window, text="Cancel", command=postcode_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        postcode_window.show()


  # --- Query 4:  Current Income for a specific trip
    def trip_income_window():
      #Created a window prompting for the trip ID to run calculations for
        income_window = Window(query_window, title = "Calculate Trip Income", width = 400, height = 200, bg = BG_COLOR)
        Text(income_window, text="Enter Trip ID:", color=TEXT_COLOR)
        trip_id_entry = TextBox(income_window)

        #Function that takes the input value and runs the calculation.
        def calculate_income():
            try:
                trip_id = trip_id_entry.value
                #Checks if the entered ID is a number before going to cursor.
                if not trip_id.isdigit():
                    info("Input Error", "Trip ID must be a number.")
                    return


                cursor.execute("""
                    SELECT SUM(b.BookingCost) AS TotalIncome
                    FROM bookings b
                    WHERE b.TripID = %s
                """, (trip_id,))
                result = cursor.fetchone()  # Use fetchone() since we expect a single row

                if result and result['TotalIncome'] is not None:
                    info("Trip Income", f"Total income for Trip ID {trip_id}: £{result['TotalIncome']:.2f}")
                else:
                    info("Trip Income", f"No bookings found for Trip ID {trip_id}, or income is 0.")
            except mysql.connector.Error as err:
                info("Database Error", f"Error calculating income: {err}")
            finally: #Closes trip_income_window whether it runs the query or not.
                income_window.destroy()

        calculate_button = PushButton(income_window, text = "Calculate", command = calculate_income)
        cancel_button = PushButton(income_window, text = "Cancel", command = income_window.destroy)
        calculate_button.bg = BUTTON_BG_COLOR; calculate_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        income_window.show()


    # --- Buttons for each query ---
    passengers_button = PushButton(query_window, text="Passengers by Trip", command=lincoln_passengers) 
    trips_button = PushButton(query_window, text="Available Trips", command=available_trips)
    postcode_button = PushButton(query_window, text="Customers by Postcode", command=postcode_customers)  
    income_button = PushButton(query_window, text = "Calculate Trip Income", command = trip_income_window)
    back_button = PushButton(query_window, text="Back", command=query_window.destroy)

    passengers_button.bg = BUTTON_BG_COLOR; passengers_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    postcode_button.bg = BUTTON_BG_COLOR;  postcode_button.text_color = BUTTON_TEXT_COLOR 
    income_button.bg = BUTTON_BG_COLOR; income_button.text_color = BUTTON_TEXT_COLOR;
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    query_window.show()

def open_admin_login_window():
    app.hide()
    global admin_login_window, username_entry, password_entry, back_button
    admin_login_window = Window(app, title="Admin Login", width=300, height=200, bg=BG_COLOR)
    Text(admin_login_window, text="Username:", color=TEXT_COLOR)
    username_entry = TextBox(admin_login_window)
    Text(admin_login_window, text="Password:", color=TEXT_COLOR)
    password_entry = TextBox(admin_login_window, hide_text=True)
    login_button = PushButton(admin_login_window, text="Login", command=check_admin_login)
    back_button = PushButton(admin_login_window, text="Back", command=go_back_to_main_menu) 
    login_button.bg = BUTTON_BG_COLOR; login_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    admin_login_window.show()



# --- Main App Setup ---
app = App("Silver Dawn Coaches", layout="grid", bg=BG_COLOR, width=800, height=600)

# Logo
logo = Picture(app, image="silverDawnLogo.png", grid=[0, 0, 2, 1])

# Title
title = Text(app, text="SILVER DAWN COACHES\nBOOKING/DATA RETRIEVAL SYSTEM", size=16, font="Arial", grid=[0, 1, 2, 1])
title.text_color = TEXT_COLOR

# Role Selection
admin_button = PushButton(app, text="Admin", command=open_admin_login_window, grid=[0, 2], align="left")
staff_button = PushButton(app, text="Staff", command=open_staff_window, grid=[1, 2], align="left")
admin_button.bg = BUTTON_BG_COLOR; admin_button.text_color = BUTTON_TEXT_COLOR
staff_button.bg = BUTTON_BG_COLOR; staff_button.text_color = BUTTON_TEXT_COLOR



app.display()
conn.close()