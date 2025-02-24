from guizero import App, Text, PushButton, TextBox, Window, info, Picture, Combo, Box, ListBox
import mysql.connector
from mysql.connector import errorcode


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

def go_back_to_staff_bookings_menu_from_data(): # NEW - go back from data window
    go_back(bookings_data_window, staff_bookings_window)


def go_back_to_main_menu():  # go back to the first screen
    go_back(staff_window, app)


# --- Data Fetching Functions ---
def get_all_bookings():
    """Fetches all bookings from the database."""
    try:
        print("DEBUG: get_all_bookings() - Executing SQL query: SELECT * FROM bookings") # Debugging print
        cursor.execute("SELECT * FROM bookings") # No need to specify schema again if DB_NAME is set in connection
        bookings = cursor.fetchall()
        print(f"DEBUG: get_all_bookings() - Raw bookings data fetched from database: {bookings}") # Debugging print
        return bookings
    except mysql.connector.Error as err:
        print(f"DEBUG: get_all_bookings() - Database Error: {err}") # Debugging print
        info("Database Error", f"Error fetching bookings: {err}")
        return None

# --- Function to open a new window and display bookings ---
def open_bookings_data_window():
    """Opens a new window to display booking data."""
    staff_bookings_window.hide() # Hide the previous window
    global bookings_data_window # Make it global so back button can access it
    bookings_data_window = Window(app, title="Booking Data", width=800, height=600, bg=BG_COLOR)
    Text(bookings_data_window, text="All Bookings", color=TEXT_COLOR, size=14, font="Arial")
    bookings_list = ListBox(bookings_data_window,  width="fill", height="fill", scrollbar=True) # ListBox in the new window

    back_button_box = Box(bookings_data_window, layout="auto", width="fill") # Box for back button in data window
    back_button = PushButton(back_button_box, text="Back to Bookings Menu", command=go_back_to_staff_bookings_menu_from_data)
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR


    bookings_data = get_all_bookings()
    if bookings_data:
        for booking in bookings_data:
            bookings_list.append(f"Booking ID: {booking['BookingID']}, Customer ID: {booking['CustomerID']}, Trip ID: {booking['TripID']}, Cost: {booking['BookingCost']}, People: {booking['NumberofPeople']}, Date: {booking['BookingDate']}")
    else:
        bookings_list.append("Could not retrieve booking data.")
    bookings_data_window.show()


# --- Admin Window Functions ---
def open_customers_window():
    admin_main_window.hide()
    global customers_window
    customers_window = Window(app, title="Admin Customers", width=800, height=600, bg=BG_COLOR)
    Text(customers_window, text="Customers", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(customers_window, layout="auto", width="fill")
    view_customers_button = PushButton(button_box, text="View Customers", width=20)
    remove_customers_button = PushButton(button_box, text="Remove Customers", width=20)

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
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20)
    add_destinations_button = PushButton(button_box, text="Add Destinations", width=20)

    remove_destinations_button = PushButton(button_box, text="Remove Destinations", width=20)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_destinations) # Corrected
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
    view_coaches_button = PushButton(button_box, text="View Coaches", width=20)
    add_coaches_button = PushButton(button_box, text="Add Coaches", width=20)
    remove_coaches_button = PushButton(button_box, text="Remove Coaches", width=20)
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
    view_drivers_button = PushButton(button_box, text="View Drivers", width=20)
    add_drivers_button = PushButton(button_box, text="Add Drivers", width=20)
    remove_drivers_button = PushButton(button_box, text="Remove Drivers", width=20)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_drivers) # Corrected
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
    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    coaches_button.bg = BUTTON_BG_COLOR; coaches_button.text_color = BUTTON_TEXT_COLOR
    drivers_button.bg = BUTTON_BG_COLOR; drivers_button.text_color = BUTTON_TEXT_COLOR
    admin_main_window.show()

# --- Staff Window Functions ---
def open_staff_customers_window():
    staff_window.hide()
    global staff_customers_window
    staff_customers_window = Window(app, title="Staff Customers", width=800, height=600, bg=BG_COLOR)
    Text(staff_customers_window, text="Customers", color=TEXT_COLOR)
    button_box = Box(staff_customers_window, layout="auto", width="fill")
    add_customer_button = PushButton(button_box, text="Add Customer", width=20)
    remove_customer_button = PushButton(button_box, text="Remove Customer", width=20)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_customers) # Corrected
    add_customer_button.bg = BUTTON_BG_COLOR; add_customer_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_button.bg = BUTTON_BG_COLOR; remove_customer_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_customers_window.show()


def open_staff_bookings_window(): # New function for staff bookings window
    staff_window.hide()
    global staff_bookings_window # Make staff_bookings_window global so data window can go back
    staff_bookings_window = Window(app, title="Staff Bookings", width=800, height=600, bg=BG_COLOR)
    Text(staff_bookings_window, text="Bookings", color=TEXT_COLOR)
    button_box = Box(staff_bookings_window, layout="auto", width="fill")
    view_bookings_button = PushButton(button_box, text="View Bookings", width=20, command=open_bookings_data_window) # Call new window function
    add_booking_button = PushButton(button_box, text="Add Booking", width=20)
    remove_booking_button = PushButton(button_box, text="Remove Booking", width=20)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_bookings) # Corrected

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
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_destinations) # Corrected
    view_destinations_button.bg = BUTTON_BG_COLOR; view_destinations_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_destinations_window.show()

def open_staff_trips_window():
    staff_window.hide()
    global staff_trips_window
    staff_trips_window = Window(app, title="Staff Trips", width=800, height=600, bg=BG_COLOR)
    Text(staff_trips_window, text="Trips", color=TEXT_COLOR)
    button_box = Box(staff_trips_window, layout="auto", width="fill")
    view_trips_button = PushButton(button_box, text="View Trips", width=20)
    add_trips_button = PushButton(button_box, text="Add Trips", width=20)
    remove_trips_button = PushButton(button_box, text="Remove Trips", width = 20)

    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_trips) # Corrected
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
    bookings_button = PushButton(button_box, text="BOOKINGS", width=15, command=open_staff_bookings_window) # Added Bookings button here
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_staff_destinations_window)
    trips_button = PushButton(button_box, text="TRIPS", width=15, command=open_staff_trips_window)
    back_button = PushButton(button_box, text="Back", width=15, command=go_back_to_main_menu)  # Corrected
    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    bookings_button.bg = BUTTON_BG_COLOR; bookings_button.text_color = BUTTON_TEXT_COLOR # Style for new button
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_window.show()

# --- Login and Main App ---
def check_admin_login():
    if username_entry.value.lower() == "admin" and password_entry.value == "admin":
        open_admin_main_window()
    else:
        info("Login Failed", "Incorrect username or password.")

def open_admin_login_window():
    app.hide()
    global admin_login_window, username_entry, password_entry, back_button
    admin_login_window = Window(app, title="Admin Login", width=300, height=200, bg=BG_COLOR)
    Text(admin_login_window, text="Username:", color=TEXT_COLOR)
    username_entry = TextBox(admin_login_window)
    Text(admin_login_window, text="Password:", color=TEXT_COLOR)
    password_entry = TextBox(admin_login_window, hide_text=True)
    login_button = PushButton(admin_login_window, text="Login", command=check_admin_login)
    back_button = PushButton(admin_login_window, text="Back", command=go_back_to_main_menu) # Corrected
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