import mysql.connector
from guizero import App, Text, Picture, PushButton, Box, TextBox, Combo, Window, ListBox, info
from mysql.connector import errorcode
import datetime  # Ensure datetime is imported
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
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)
except mysql.connector.Error as err:
    try:
        temp_app = App(title="DB Connection Error", visible=False)
        info("Database Connection Error", f"Failed to connect to database: {err}")
        temp_app.destroy()
    except Exception:
        print(f"CRITICAL DATABASE ERROR: {err}")
    exit()

# --- Pagination Globals ---
current_page = 0
records_per_page = 15

# --- Helper Functions for Table Display & Pagination ---

def clear_box(box):
    widgets_to_destroy = box.children[:]
    for widget in widgets_to_destroy:
        widget.destroy()

def create_search_box(parent_box, table_name, table_view_box, pagination_box):
    """Creates a search interface for tables"""
    search_container = Box(parent_box, align="top", width="fill", layout="grid")
    Text(search_container, text="Search:", grid=[0, 0], align="left", color=TEXT_COLOR)
    search_input = TextBox(search_container, width=25, grid=[1, 0], align="left")

    search_fields = {
        "trips": ["TripID", "CoachID", "DriverID", "DestinationID", "Date", "CoachReg", "DriverName", "DestinationName"], # Added aliases
        "destinations": ["DestinationID", "DestinationName", "Hotel", "CityName", "Days", "DestinationCost"],
        "coaches": ["CoachID", "Registration", "Seats"],
        "drivers": ["DriverID", "DriverName"],
        "customers": ["CustomerID", "FirstName", "Surname", "Email", "City", "Postcode", "PhoneNumber"],
        "bookings": ["BookingID", "CustomerID", "TripID", "BookingCost", "NumberOfPeople", "SpecialRequest", "BookingDate", "CustomerName", "DestinationName"] # Added aliases
    }

    if table_name not in search_fields:
        Text(search_container, text="Search not available.", grid=[2, 0], align="left", color="red")
        return

    Text(search_container, text=" by:", grid=[2, 0], align="left", color=TEXT_COLOR)
    # Filter options based on what's actually selectable in fetch_and_display_table
    available_options = search_fields.get(table_name, [])
    if not available_options:
         Text(search_container, text="No searchable fields.", grid=[3, 0], align="left", color="red")
         return

    field_dropdown = Combo(search_container, options=available_options, grid=[3, 0], align="left")
    if available_options:
        field_dropdown.value = available_options[0] # Default to first option

    search_button = PushButton(search_container, text="Search", grid=[4, 0], align="left",
                               command=lambda: fetch_and_display_table(table_name, table_view_box, pagination_box,
                                                                     search_term=search_input.value,
                                                                     search_field=field_dropdown.value))
    search_button.bg = BUTTON_BG_COLOR
    search_button.text_color = BUTTON_TEXT_COLOR


def fetch_and_display_table(table_name, table_box, pagination_box, page=0, search_term=None, search_field=None):
    """Fetches and displays data in a paginated table."""
    global current_page
    current_page = page
    offset = page * records_per_page

    base_query = ""
    select_query = ""
    columns = []
    where_clause = ""
    query_params = [] # Use list for parameters

    try:
        search_value = None # Initialize search_value
        if search_term and search_field:
            search_value = f"%{search_term}%" # Prepare LIKE value

        # Define Queries, Columns, and Search Mapping
        if table_name == "bookings":
            select_query = """
                SELECT b.BookingID, b.CustomerID, CONCAT(c.FirstName, ' ', c.Surname) as CustomerName,
                       b.TripID, d.DestinationName, t.Date as TripDate,
                       b.NumberofPeople, CONCAT('£', FORMAT(b.BookingCost, 2)) as Cost,
                       b.SpecialRequest, b.BookingDate
            """
            base_query = """
                FROM bookings b
                LEFT JOIN customers c ON b.CustomerID = c.CustomerID
                LEFT JOIN trips t ON b.TripID = t.TripID
                LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
            """
            columns = ["ID", "Cust. ID", "Customer Name", "Trip ID", "Destination", "Trip Date", "# People", "Cost", "Request", "Booking Date"]
            field_map = { # Map display column name to DB field/alias for searching
                "BookingID": "b.BookingID", "CustomerID": "b.CustomerID", "TripID": "b.TripID",
                "BookingCost": "b.BookingCost", "NumberOfPeople": "b.NumberofPeople",
                "SpecialRequest": "b.SpecialRequest", "BookingDate": "b.BookingDate",
                "CustomerName": "CONCAT(c.FirstName, ' ', c.Surname)",
                "DestinationName": "d.DestinationName"
            }
            if search_value and search_field in field_map:
                where_clause = f" WHERE {field_map[search_field]} LIKE %s"
                query_params.append(search_value)

        elif table_name == "trips":
            select_query = """
                SELECT t.TripID, t.CoachID, c.Registration as CoachReg, t.DriverID, dr.DriverName,
                       t.DestinationID, d.DestinationName, t.Date
            """
            base_query = """
                FROM trips t
                LEFT JOIN coaches c ON t.CoachID = c.CoachID
                LEFT JOIN drivers dr ON t.DriverID = dr.DriverID
                LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
            """
            columns = ["ID", "Coach ID", "Coach Reg", "Driver ID", "Driver Name", "Dest. ID", "Destination", "Date"]
            field_map = {
                "TripID": "t.TripID", "CoachID": "t.CoachID", "DriverID": "t.DriverID",
                "DestinationID": "t.DestinationID", "Date": "t.Date", "CoachReg": "c.Registration",
                "DriverName": "dr.DriverName", "DestinationName": "d.DestinationName"
            }
            if search_value and search_field in field_map:
                where_clause = f" WHERE {field_map[search_field]} LIKE %s"
                query_params.append(search_value)

        elif table_name == "customers":
             select_query = "SELECT CustomerID, FirstName, Surname, Email, AddressLine1, AddressLine2, City, Postcode, PhoneNumber, SpecialNotes"
             base_query = f"FROM {table_name}"
             columns = ["ID", "First Name", "Surname", "Email", "Address 1", "Address 2", "City", "Postcode", "Phone", "Notes"]
             valid_columns = ["CustomerID", "FirstName", "Surname", "Email", "AddressLine1", "AddressLine2", "City", "Postcode", "PhoneNumber", "SpecialNotes"]
             if search_value and search_field in valid_columns:
                 where_clause = f" WHERE {search_field} LIKE %s"
                 query_params.append(search_value)

        elif table_name == "coaches":
             select_query = "SELECT CoachID, Registration, Seats"
             base_query = f"FROM {table_name}"
             columns = ["ID", "Registration", "Seats"]
             valid_columns = ["CoachID", "Registration", "Seats"]
             if search_value and search_field in valid_columns:
                 where_clause = f" WHERE {search_field} LIKE %s"
                 query_params.append(search_value)

        elif table_name == "destinations":
            select_query = "SELECT DestinationID, DestinationName, Hotel, DestinationCost, CityName, Days"
            base_query = f"FROM {table_name}"
            columns = ["ID", "Name", "Hotel", "Cost", "City", "Days"]
            valid_columns = ["DestinationID", "DestinationName", "Hotel", "DestinationCost", "CityName", "Days"]
            if search_value and search_field in valid_columns:
                 where_clause = f" WHERE {search_field} LIKE %s"
                 query_params.append(search_value)

        elif table_name == "drivers":
             select_query = "SELECT DriverID, DriverName"
             base_query = f"FROM {table_name}"
             columns = ["ID", "Driver Name"]
             valid_columns = ["DriverID", "DriverName"]
             if search_value and search_field in valid_columns:
                 where_clause = f" WHERE {search_field} LIKE %s"
                 query_params.append(search_value)
        else:
            Text(table_box, text=f"Table '{table_name}' display not configured.", color="red")
            return # Exit if table type is unknown

        # Map display columns back to data keys for fetching row data (handles aliases)
        data_key_map = {}
        if table_name == "bookings":
            data_key_map = {"ID": "BookingID", "Cust. ID": "CustomerID", "Customer Name": "CustomerName", "Trip ID": "TripID", "Destination": "DestinationName", "Trip Date": "TripDate", "# People": "NumberofPeople", "Cost": "Cost", "Request": "SpecialRequest", "Booking Date": "BookingDate"}
        elif table_name == "trips":
            data_key_map = {"ID": "TripID", "Coach ID": "CoachID", "Coach Reg": "CoachReg", "Driver ID": "DriverID", "Driver Name": "DriverName", "Dest. ID": "DestinationID", "Destination": "DestinationName", "Date": "Date"}
        elif table_name == "customers":
            data_key_map = {"ID": "CustomerID", "First Name": "FirstName", "Surname": "Surname", "Email": "Email", "Address 1": "AddressLine1", "Address 2": "AddressLine2", "City": "City", "Postcode": "Postcode", "Phone": "PhoneNumber", "Notes": "SpecialNotes"}
        elif table_name == "coaches":
            data_key_map = {"ID": "CoachID", "Registration": "Registration", "Seats": "Seats"}
        elif table_name == "destinations":
            data_key_map = {"ID": "DestinationID", "Name": "DestinationName", "Hotel": "Hotel", "Cost": "DestinationCost", "City": "CityName", "Days": "Days"}
        elif table_name == "drivers":
            data_key_map = {"ID": "DriverID", "Driver Name": "DriverName"}


        # --- Execute Queries ---
        count_query = f"SELECT COUNT(*) as total {base_query}{where_clause}"
        cursor.execute(count_query, tuple(query_params)) # Pass params even if empty for consistency
        total_records = cursor.fetchone()['total']

        data_query = f"{select_query} {base_query}{where_clause} LIMIT %s OFFSET %s"
        limit_params = query_params + [records_per_page, offset] # Add limit/offset params
        cursor.execute(data_query, tuple(limit_params))
        records = cursor.fetchall()

        total_pages = (total_records + records_per_page - 1) // records_per_page

        # --- Clear and Display ---
        clear_box(table_box)
        clear_box(pagination_box)

        if records or columns:
            table_grid = Box(table_box, layout="grid", width="fill", align="top")
            for col, header in enumerate(columns):
                Text(table_grid, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True)

            for row, record_dict in enumerate(records, start=1):
                for col, header in enumerate(columns):
                    data_key = data_key_map.get(header, header) # Use mapped key or header itself
                    data_to_display = str(record_dict.get(data_key, '')) # Get value, default to empty string
                    Text(table_grid, text=data_to_display, grid=[col, row], color=TEXT_COLOR, size=10)

        elif not columns:
            Text(table_box, text="Could not determine table columns.", color="red")
        else:
            Text(table_box, text="No records found.", color=TEXT_COLOR)

        # --- Pagination controls ---
        pagination_controls = Box(pagination_box, layout="grid", width="fill", align="bottom")
        if page > 0:
            prev_button = PushButton(pagination_controls, text="<< Previous",
                                     command=lambda p=page, st=search_term, sf=search_field: fetch_and_display_table(table_name, table_box, pagination_box, p - 1, st, sf),
                                     grid=[0, 0], align="left")
            prev_button.bg = BUTTON_BG_COLOR
            prev_button.text_color = BUTTON_TEXT_COLOR

        Text(pagination_controls, text=f"Page {page + 1} of {max(1, total_pages)}", grid=[1, 0], align="left", color=TEXT_COLOR)

        if page < total_pages - 1:
            next_button = PushButton(pagination_controls, text="Next >>",
                                     command=lambda p=page, st=search_term, sf=search_field: fetch_and_display_table(table_name, table_box, pagination_box, p + 1, st, sf),
                                     grid=[2, 0], align="left")
            next_button.bg = BUTTON_BG_COLOR
            next_button.text_color = BUTTON_TEXT_COLOR

    except mysql.connector.Error as err:
        clear_box(table_box)
        clear_box(pagination_box)
        Text(table_box, text=f"Database Error:\n{err}", color="red", size=12)
        print(f"Database Error in fetch_and_display_table: {err}")
    except Exception as e:
        clear_box(table_box)
        clear_box(pagination_box)
        Text(table_box, text=f"An unexpected error occurred:\n{e}", color="red", size=12)
        import traceback
        traceback.print_exc() # Print full traceback for debugging


# --- GUI Functions ---

def go_back(current_window, previous_window):
    """Hides the current window and shows the previous window."""
    current_window.hide()
    if previous_window:
        previous_window.show()
    else:
        app.show() # Fallback to main app window

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

# --- Back Button Functions for Data Windows (Used as parameters) ---
def go_back_to_staff_bookings_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_bookings_window)
def go_back_to_admin_customers_menu_from_data(window_to_hide):
    go_back(window_to_hide, customers_window) # Assumes customers_window is admin one
def go_back_to_staff_customers_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_customers_window)
def go_back_to_admin_coaches_menu_from_data(window_to_hide):
    go_back(window_to_hide, coaches_window)
def go_back_to_admin_destinations_menu_from_data(window_to_hide):
    go_back(window_to_hide, destinations_window)
def go_back_to_staff_destinations_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_destinations_window)
def go_back_to_admin_drivers_menu_from_data(window_to_hide):
    go_back(window_to_hide, drivers_window)
def go_back_to_staff_trips_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_trips_window)

def go_back_to_main_menu(window_to_hide):
    go_back(window_to_hide, app)

# --- Data Fetching Functions (Kept for potential use in Add/Remove logic) ---
# (Keep the get_all_* functions as they were)
def get_all_bookings():
    """Fetches all bookings from the database."""
    try:
        # Example: Join to get customer name for display IF needed elsewhere
        cursor.execute("""
            SELECT b.*, CONCAT(c.FirstName, ' ', c.Surname) as CustomerName
            FROM bookings b
            LEFT JOIN customers c ON b.CustomerID = c.CustomerID
        """)
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
        # Example: Join to get destination name if needed elsewhere
        cursor.execute("""
            SELECT t.*, d.DestinationName
            FROM trips t
            LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
        """)
        trips = cursor.fetchall()
        return trips
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching trips: {err}")
        return None


# --- Functions to open data windows (Passing back function directly) ---

def open_bookings_data_window(parent_window, back_function_to_call):
    """Opens a new window to display booking data using the integrated table view."""
    parent_window.hide()
    bookings_data_win = Window(app, title="Booking Data", width=950, height=600, bg=BG_COLOR)
    Text(bookings_data_win, text="All Bookings", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(bookings_data_win, align="top", width="fill")
    table_view_box = Box(bookings_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(bookings_data_win, align="bottom", width="fill") # For Prev/Next/Page#
    back_button_box = Box(bookings_data_win, align="bottom", width="fill") # Dedicated box for back

    create_search_box(search_area_box, "bookings", table_view_box, pagination_box)
    fetch_and_display_table("bookings", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(bookings_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    bookings_data_win.show()


def open_customers_data_window(parent_window, back_function_to_call):
    """Opens customer data view using integrated table."""
    parent_window.hide()
    customers_data_win = Window(app, title="Customer Data", width=1100, height=600, bg=BG_COLOR)
    Text(customers_data_win, text="All Customers", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(customers_data_win, align="top", width="fill")
    table_view_box = Box(customers_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(customers_data_win, align="bottom", width="fill")
    back_button_box = Box(customers_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "customers", table_view_box, pagination_box)
    fetch_and_display_table("customers", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(customers_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    customers_data_win.show()


def open_coaches_data_window(parent_window, back_function_to_call):
    """Opens coach data view using integrated table."""
    parent_window.hide()
    coaches_data_win = Window(app, title="Coach Data", width=800, height=600, bg=BG_COLOR)
    Text(coaches_data_win, text="All Coaches", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(coaches_data_win, align="top", width="fill")
    table_view_box = Box(coaches_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(coaches_data_win, align="bottom", width="fill")
    back_button_box = Box(coaches_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "coaches", table_view_box, pagination_box)
    fetch_and_display_table("coaches", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(coaches_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    coaches_data_win.show()

def open_destinations_data_window(parent_window, back_function_to_call):
    """Opens destination data view using integrated table."""
    parent_window.hide()
    destinations_data_win = Window(app, title="Destination Data", width=800, height=600, bg=BG_COLOR)
    Text(destinations_data_win, text="All Destinations", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(destinations_data_win, align="top", width="fill")
    table_view_box = Box(destinations_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(destinations_data_win, align="bottom", width="fill")
    back_button_box = Box(destinations_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "destinations", table_view_box, pagination_box)
    fetch_and_display_table("destinations", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(destinations_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    destinations_data_win.show()


def open_drivers_data_window(parent_window, back_function_to_call):
    """Opens driver data view using integrated table."""
    parent_window.hide()
    drivers_data_win = Window(app, title="Driver Data", width=800, height=600, bg=BG_COLOR)
    Text(drivers_data_win, text="All Drivers", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(drivers_data_win, align="top", width="fill")
    table_view_box = Box(drivers_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(drivers_data_win, align="bottom", width="fill")
    back_button_box = Box(drivers_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "drivers", table_view_box, pagination_box)
    fetch_and_display_table("drivers", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(drivers_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    drivers_data_win.show()


def open_trips_data_window(parent_window, back_function_to_call):
    """Opens trip data view using integrated table."""
    parent_window.hide()
    trips_data_win = Window(app, title="Trip Data", width=900, height=600, bg=BG_COLOR)
    Text(trips_data_win, text="All Trips", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(trips_data_win, align="top", width="fill")
    table_view_box = Box(trips_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(trips_data_win, align="bottom", width="fill")
    back_button_box = Box(trips_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "trips", table_view_box, pagination_box)
    fetch_and_display_table("trips", table_view_box, pagination_box, page=0)

    if back_function_to_call:
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(trips_data_win),
                                 align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
        Text(back_button_box, text="Back function error", color="red", align="right")

    trips_data_win.show()


#region Admin Windows
# --- Admin Window Functions ---
def open_customers_window():
    admin_main_window.hide()
    global customers_window
    customers_window = Window(app, title="Admin Customers", width=800, height=600, bg=BG_COLOR)
    Text(customers_window, text="Customers Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(customers_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_customers_button = PushButton(button_box, text="View Customers", width=20,
                                       command=lambda: open_customers_data_window(customers_window, go_back_to_admin_customers_menu_from_data))
    remove_customers_button = PushButton(button_box, text="Remove Customers", width=20, command=open_remove_customer_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_customers)
    view_customers_button.bg = BUTTON_BG_COLOR; view_customers_button.text_color = BUTTON_TEXT_COLOR
    remove_customers_button.bg = BUTTON_BG_COLOR; remove_customers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    customers_window.show()

def open_destinations_window():
    admin_main_window.hide()
    global destinations_window
    destinations_window = Window(app, title="Admin Destinations", width=800, height=600, bg=BG_COLOR)
    Text(destinations_window, text="Destinations Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(destinations_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20,
                                          command=lambda: open_destinations_data_window(destinations_window, go_back_to_admin_destinations_menu_from_data))
    add_destinations_button = PushButton(button_box, text="Add Destinations", width=20, command=open_add_destination_window)
    remove_destinations_button = PushButton(button_box, text="Remove Destinations", width=20, command=open_remove_destination_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_destinations)
    view_destinations_button.bg = BUTTON_BG_COLOR; view_destinations_button.text_color = BUTTON_TEXT_COLOR
    add_destinations_button.bg = BUTTON_BG_COLOR; add_destinations_button.text_color = BUTTON_TEXT_COLOR
    remove_destinations_button.bg = BUTTON_BG_COLOR; remove_destinations_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    destinations_window.show()

def open_coaches_window():
    admin_main_window.hide()
    global coaches_window
    coaches_window = Window(app, title="Admin Coaches", width=800, height=600, bg=BG_COLOR)
    Text(coaches_window, text="Coaches Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(coaches_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_coaches_button = PushButton(button_box, text="View Coaches", width=20,
                                     command=lambda: open_coaches_data_window(coaches_window, go_back_to_admin_coaches_menu_from_data))
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
    Text(drivers_window, text="Drivers Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(drivers_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_drivers_button = PushButton(button_box, text="View Drivers", width=20,
                                     command=lambda: open_drivers_data_window(drivers_window, go_back_to_admin_drivers_menu_from_data))
    add_drivers_button = PushButton(button_box, text="Add Drivers", width=20, command=open_add_driver_window)
    remove_drivers_button = PushButton(button_box, text="Remove Drivers", width=20, command=open_remove_driver_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_drivers)
    view_drivers_button.bg = BUTTON_BG_COLOR; view_drivers_button.text_color = BUTTON_TEXT_COLOR
    add_drivers_button.bg = BUTTON_BG_COLOR; add_drivers_button.text_color = BUTTON_TEXT_COLOR
    remove_drivers_button.bg = BUTTON_BG_COLOR; remove_drivers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    drivers_window.show()


def open_admin_main_window():
    global admin_login_window
    try:
        if admin_login_window and admin_login_window.visible:
             admin_login_window.hide()
    except NameError: pass
    except AttributeError: pass

    global admin_main_window
    admin_main_window = Window(app, title="Admin Main", width=800, height=600, bg=BG_COLOR)
    Text(admin_main_window, text="Admin Main Menu", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(admin_main_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_customers_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_destinations_window)
    coaches_button = PushButton(button_box, text="COACHES", width=15, command=open_coaches_window)
    drivers_button = PushButton(button_box, text="DRIVERS", width=15, command=open_drivers_window)
    search_button = PushButton(button_box, text="QUERIES", width=15, command=open_query_window)
    back_button = PushButton(button_box, text="Logout", width=15, command=lambda: go_back_to_main_menu(admin_main_window))

    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    coaches_button.bg = BUTTON_BG_COLOR; coaches_button.text_color = BUTTON_TEXT_COLOR
    drivers_button.bg = BUTTON_BG_COLOR; drivers_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR

    admin_main_window.show()

#endregion Admin Windows


#region Staff Windows
# --- Staff Window Functions ---
def open_staff_customers_window():
    staff_window.hide()
    global staff_customers_window
    staff_customers_window = Window(app, title="Staff Customers", width=800, height=600, bg=BG_COLOR)
    Text(staff_customers_window, text="Customers (Staff)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_customers_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_customer_button = PushButton(button_box, text="View Customers", width=20,
                                      command=lambda: open_customers_data_window(staff_customers_window, go_back_to_staff_customers_menu_from_data))
    add_customer_button = PushButton(button_box, text="Add Customer", width=20, command=open_add_customer_window)
    remove_customer_button = PushButton(button_box, text="Remove Customer", width=20, command=open_remove_customer_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_customers)

    view_customer_button.bg = BUTTON_BG_COLOR; view_customer_button.text_color = BUTTON_TEXT_COLOR
    add_customer_button.bg = BUTTON_BG_COLOR; add_customer_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_button.bg = BUTTON_BG_COLOR; remove_customer_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_customers_window.show()


def open_staff_bookings_window():
    staff_window.hide()
    global staff_bookings_window
    staff_bookings_window = Window(app, title="Staff Bookings", width=800, height=600, bg=BG_COLOR)
    Text(staff_bookings_window, text="Bookings (Staff)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_bookings_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_bookings_button = PushButton(button_box, text="View Bookings", width=20,
                                      command=lambda: open_bookings_data_window(staff_bookings_window, go_back_to_staff_bookings_menu_from_data))
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
    Text(staff_destinations_window, text="View Destinations (Staff)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_destinations_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20,
                                          command=lambda: open_destinations_data_window(staff_destinations_window, go_back_to_staff_destinations_menu_from_data))
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_destinations)
    view_destinations_button.bg = BUTTON_BG_COLOR; view_destinations_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_destinations_window.show()

def open_staff_trips_window():
    staff_window.hide()
    global staff_trips_window
    staff_trips_window = Window(app, title="Staff Trips", width=800, height=600, bg=BG_COLOR)
    Text(staff_trips_window, text="Trips (Staff)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_trips_window, layout="auto", width="fill")
    # Pass the current window AND the correct back function
    view_trips_button = PushButton(button_box, text="View Trips", width=20,
                                   command=lambda: open_trips_data_window(staff_trips_window, go_back_to_staff_trips_menu_from_data))
    add_trips_button = PushButton(button_box, text="Add Trips", width=20, command=open_add_trip_window)
    remove_trips_button = PushButton(button_box, text="Remove Trips", width = 20) # Add command later if needed

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
    Text(staff_window, text="Staff Main Menu", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(staff_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_staff_customers_window)
    bookings_button = PushButton(button_box, text="BOOKINGS", width=15, command=open_staff_bookings_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_staff_destinations_window)
    trips_button = PushButton(button_box, text="TRIPS", width=15, command=open_staff_trips_window)
    search_button = PushButton(button_box, text="QUERIES", width=15, command=open_query_window)
    back_button = PushButton(button_box, text="Logout", width=15, command=lambda: go_back_to_main_menu(staff_window))

    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    bookings_button.bg = BUTTON_BG_COLOR; bookings_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_window.show()

#endregion Staff Windows


#region Add Windows
def open_add_customer_window():
    # Default parent assumption (might need adjustment if called from Admin too)
    parent = staff_customers_window

    global add_customer_window
    global first_name_entry, surname_entry, email_entry, address1_entry, address2_entry
    global city_entry, postcode_entry, phone_entry, notes_entry

    add_customer_window = Window(app, title="Add Customer", width=400, height=600, bg=BG_COLOR)
    Text(add_customer_window, text="Enter Customer Details:", color=TEXT_COLOR)

    Text(add_customer_window, text="First Name:", color=TEXT_COLOR)
    first_name_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Surname:", color=TEXT_COLOR)
    surname_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Email:", color=TEXT_COLOR)
    email_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Address Line 1:", color=TEXT_COLOR)
    address1_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Address Line 2:", color=TEXT_COLOR)
    address2_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="City:", color=TEXT_COLOR)
    city_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Postcode:", color=TEXT_COLOR)
    postcode_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Phone Number:", color=TEXT_COLOR)
    phone_entry = TextBox(add_customer_window, width='fill')
    Text(add_customer_window, text="Special Notes:", color=TEXT_COLOR)
    notes_entry = TextBox(add_customer_window, width='fill')

    def add_customer():
        try:
            # Input Validation
            if not all([first_name_entry.value, surname_entry.value, email_entry.value,
                        address1_entry.value, city_entry.value, postcode_entry.value, phone_entry.value]):
                info("Input Error", "Please fill in all required fields (except Address Line 2 and Notes).")
                return
            email = email_entry.value
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_regex, email):
                info("Input Error", "Invalid email format.")
                return

            cursor.execute("""
                INSERT INTO customers (FirstName, Surname, Email, AddressLine1,
                                       AddressLine2, City, Postcode, PhoneNumber, SpecialNotes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name_entry.value, surname_entry.value, email_entry.value,
                  address1_entry.value, address2_entry.value or None, city_entry.value, # Use None if empty
                  postcode_entry.value, phone_entry.value, notes_entry.value or None)) # Use None if empty
            conn.commit()
            info("Success", "Customer added successfully.")
            add_customer_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            info("Database Error", f"Failed to add customer. Error: {err.msg}")

    button_box = Box(add_customer_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text="Add Customer", grid=[0,0], command=add_customer)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (add_customer_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_customer_window.show()


def open_add_booking_window():
    parent = staff_bookings_window # Assume called from staff context

    global add_booking_window, customer_combo, trip_combo, num_people_entry, special_request_entry

    add_booking_window = Window(app, title="Add Booking", width=450, height=450, bg=BG_COLOR)
    Text(add_booking_window, text = "Enter Booking Details:", color = TEXT_COLOR)

    Text(add_booking_window, text="Customer:", color=TEXT_COLOR)
    customer_combo = Combo(add_booking_window, options=[], width="fill")
    try:
        cursor.execute("SELECT CustomerID, FirstName, Surname FROM customers ORDER BY Surname, FirstName")
        customers = cursor.fetchall()
        customer_combo.clear()
        customer_combo.append("")
        for customer in customers:
             customer_combo.append(f"{customer['CustomerID']}: {customer['FirstName']} {customer['Surname']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load customers: {err}")
        add_booking_window.destroy(); parent.show(); return

    Text(add_booking_window, text="Trip:", color=TEXT_COLOR)
    trip_combo = Combo(add_booking_window, options=[], width="fill")
    try:
        cursor.execute("""
            SELECT t.TripID, t.Date, d.DestinationName
            FROM trips t JOIN destinations d ON t.DestinationID = d.DestinationID
            WHERE t.Date >= CURDATE() ORDER BY t.Date
        """)
        trips = cursor.fetchall()
        trip_combo.clear()
        trip_combo.append("")
        for trip in trips:
            trip_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load trips: {err}")
        add_booking_window.destroy(); parent.show(); return

    Text(add_booking_window, text="Number of People:", color=TEXT_COLOR)
    num_people_entry = TextBox(add_booking_window, width='fill')
    Text(add_booking_window, text="Special Request:", color=TEXT_COLOR)
    special_request_entry = TextBox(add_booking_window, width='fill')
    Text(add_booking_window, text="Date of Booking:", color=TEXT_COLOR)
    date_of_booking_display = Text(add_booking_window, text = "")
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    date_of_booking_display.value = current_date

    def add_booking():
        calculated_cost = 0
        try:
            # Input Validation
            selected_customer = customer_combo.value
            selected_trip = trip_combo.value
            if not selected_customer or not selected_trip:
                info("Input Error", "Please select both a customer and a trip.")
                return
            customer_id = int(selected_customer.split(":")[0])
            trip_id = int(selected_trip.split(":")[0])

            if not num_people_entry.value.isdigit() or int(num_people_entry.value) <= 0:
                info("Input Error", "Number of People must be a positive integer.")
                return
            num_people = int(num_people_entry.value)

            # Calculate Cost
            cursor.execute("SELECT d.DestinationCost FROM trips t JOIN destinations d ON t.DestinationID = d.DestinationID WHERE t.TripID = %s", (trip_id,))
            cost_result = cursor.fetchone()
            if cost_result and cost_result['DestinationCost'] is not None:
                 calculated_cost = float(cost_result['DestinationCost']) * num_people
            else: info("Error", "Could not retrieve destination cost."); return

            # Check Capacity
            cursor.execute("SELECT c.Seats FROM trips t JOIN coaches c ON t.CoachID = c.CoachID WHERE t.TripID = %s", (trip_id,))
            seat_result = cursor.fetchone()
            if seat_result:
                available_seats = seat_result['Seats']
                cursor.execute("SELECT SUM(NumberofPeople) as booked FROM bookings WHERE TripID = %s", (trip_id,))
                booked_result = cursor.fetchone()
                booked_seats = booked_result['booked'] or 0
                if num_people > (available_seats - booked_seats):
                    info("Input Error", f"Not enough seats available ({available_seats - booked_seats} left).")
                    return
            else: info("Database Error", "Could not retrieve coach capacity."); return

            # Insert Booking
            cursor.execute("""
            INSERT INTO bookings (CustomerID, TripID, BookingCost, NumberofPeople, SpecialRequest, BookingDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer_id, trip_id, calculated_cost, num_people, special_request_entry.value or None, current_date))
            conn.commit()
            info("Booking Added", f"Booking added. Cost: £{calculated_cost:.2f}")
            add_booking_window.destroy(); parent.show()

        except (ValueError, IndexError): info("Input Error", "Invalid selection or number format.")
        except TypeError: info("Error", "Cost calculation error.")
        except mysql.connector.Error as err: info("Database Error",f"Error Adding booking: {err.msg}")


    button_box = Box(add_booking_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text="Add Booking", grid=[0,0], command=add_booking)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (add_booking_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_booking_window.show()


def open_add_coach_window():
    parent = coaches_window # Assume called from admin context

    global add_coach_window, coach_reg_entry, seats_entry
    add_coach_window = Window(app, title = "Add Coach", width = 400, height = 200, bg = BG_COLOR) # Reduced height
    Text(add_coach_window, text="Enter Coach Details:", color = TEXT_COLOR)

    Text(add_coach_window, text = "Coach Registration:", color = TEXT_COLOR)
    coach_reg_entry = TextBox(add_coach_window, width='fill')
    Text(add_coach_window, text="Seats in Coach", color = TEXT_COLOR)
    seats_entry = TextBox(add_coach_window, width='fill')

    def add_coach():
        try:
            if not coach_reg_entry.value: info("Input Error", "Coach Registration Required"); return
            if not seats_entry.value.isdigit() or int(seats_entry.value) <= 0:
                info("Input Error", "Number of seats must be a positive number"); return
            cursor.execute("INSERT INTO coaches (Registration, Seats) VALUES (%s, %s)",
                           (coach_reg_entry.value, seats_entry.value))
            conn.commit()
            info("Coach Added", "Coach added to the database.")
            add_coach_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Registration already exists.")
            else: info("Database Error", f"Failed to add coach: {err.msg}")

    button_box = Box(add_coach_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text="Add Coach", grid=[0,0], command=add_coach)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (add_coach_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_coach_window.show()

def open_add_destination_window():
    parent = destinations_window # Assume called from admin context

    global add_destination_window, destination_name_entry, hotel_name_entry
    global destination_cost_entry, city_name_entry, days_entry

    add_destination_window = Window(app, title = "Add Destination", width = 400, height = 350, bg = BG_COLOR) # Adjusted height
    Text(add_destination_window, text = "Enter Destination Details:", color = TEXT_COLOR)

    Text(add_destination_window, text = "Destination Name:", color = TEXT_COLOR)
    destination_name_entry = TextBox(add_destination_window, width='fill')
    Text(add_destination_window, text = "Hotel Name:", color = TEXT_COLOR)
    hotel_name_entry = TextBox(add_destination_window, width='fill')
    Text(add_destination_window, text = "Destination Cost (£):", color = TEXT_COLOR)
    destination_cost_entry = TextBox(add_destination_window, width='fill')
    Text(add_destination_window, text="City Name:", color=TEXT_COLOR)
    city_name_entry = TextBox(add_destination_window, width='fill')
    Text(add_destination_window, text = "Days:", color = TEXT_COLOR)
    days_entry = TextBox(add_destination_window, width='fill')

    def add_destination():
        try:
            # Validation
            if not all([destination_name_entry.value, hotel_name_entry.value, destination_cost_entry.value, city_name_entry.value, days_entry.value]):
                info("Input Error", "Please fill all fields."); return
            try: cost = float(destination_cost_entry.value); assert cost >= 0
            except (ValueError, AssertionError): info("Input Error", "Cost must be a non-negative number."); return
            if not days_entry.value.isdigit() or int(days_entry.value) <= 0:
                info("Input Error", "Days must be a positive number."); return

            cursor.execute("""
            INSERT INTO destinations (DestinationName, Hotel, DestinationCost, CityName, Days)
            VALUES (%s, %s, %s, %s, %s)""",
            (destination_name_entry.value, hotel_name_entry.value, cost, city_name_entry.value, days_entry.value))
            conn.commit()
            info("Success", "Destination added successfully.")
            add_destination_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Destination name might already exist.")
            else: info("Database Error", f"Failed to add Destination: {err.msg}")

    button_box = Box(add_destination_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text = "Add Destination", grid=[0,0], command=add_destination)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command = lambda: (add_destination_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_destination_window.show()


def open_add_driver_window():
    parent = drivers_window # Assume called from admin context

    global add_driver_window, driver_name_entry

    add_driver_window = Window(app, title = "Add Driver", width = 400, height = 150, bg = BG_COLOR) # Reduced height
    Text(add_driver_window, text = "Enter the Driver's Name:", color = TEXT_COLOR) # Clarified
    driver_name_entry = TextBox(add_driver_window, width='fill')

    def add_driver():
        try:
            if not driver_name_entry.value: info("Input Error", "Driver name is required."); return
            cursor.execute("INSERT INTO drivers (DriverName) VALUES (%s)", (driver_name_entry.value,))
            conn.commit()
            info("Success", "Driver added successfully.")
            add_driver_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Driver name might already exist.")
            else: info("Database Error", f"Failed to add Driver: {err.msg}")

    button_box = Box(add_driver_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text="Add Driver", grid=[0,0], command = add_driver)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command = lambda: (add_driver_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_driver_window.show()

def open_add_trip_window():
    parent = staff_trips_window # Assume called from staff context

    global add_trip_window, coach_combo, driver_combo, destination_combo, date_entry

    add_trip_window = Window(app, title="Add Trip", width = 400, height = 300, bg = BG_COLOR) # Adjusted height
    Text(add_trip_window, text = "Enter Trip Details: ", color = TEXT_COLOR)

    Text(add_trip_window, text = "Coach:", color = TEXT_COLOR)
    coach_combo = Combo(add_trip_window, options=[], width="fill")
    try:
        cursor.execute("SELECT CoachID, Registration FROM coaches ORDER BY Registration")
        coaches = cursor.fetchall(); coach_combo.clear(); coach_combo.append("")
        for coach in coaches: coach_combo.append(f"{coach['CoachID']}: {coach['Registration']}")
    except mysql.connector.Error as err: info("Database Error", f"Could not load coaches: {err}"); add_trip_window.destroy(); parent.show(); return

    Text(add_trip_window, text = "Driver:", color = TEXT_COLOR)
    driver_combo = Combo(add_trip_window, options=[], width="fill")
    try:
        cursor.execute("SELECT DriverID, DriverName FROM drivers ORDER BY DriverName")
        drivers = cursor.fetchall(); driver_combo.clear(); driver_combo.append("")
        for driver in drivers: driver_combo.append(f"{driver['DriverID']}: {driver['DriverName']}")
    except mysql.connector.Error as err: info("Database Error", f"Could not load drivers: {err}"); add_trip_window.destroy(); parent.show(); return

    Text(add_trip_window, text="Destination:", color=TEXT_COLOR)
    destination_combo = Combo(add_trip_window, options=[], width="fill")
    try:
        cursor.execute("SELECT DestinationID, DestinationName FROM destinations ORDER BY DestinationName")
        destinations = cursor.fetchall(); destination_combo.clear(); destination_combo.append("")
        for destination in destinations: destination_combo.append(f"{destination['DestinationID']}: {destination['DestinationName']}")
    except mysql.connector.Error as err: info("Database Error", f"Could not load destinations: {err}"); add_trip_window.destroy(); parent.show(); return

    Text(add_trip_window, text = "Date (YYYY-MM-DD):", color = TEXT_COLOR)
    date_entry = TextBox(add_trip_window, width='fill')

    def add_trip():
        try:
            # Validation
            selected_coach = coach_combo.value
            selected_driver = driver_combo.value
            selected_destination = destination_combo.value
            trip_date_str = date_entry.value
            if not all([selected_coach, selected_driver, selected_destination, trip_date_str]):
                info("Input Error", "Please select all options and enter a date."); return
            coach_id = int(selected_coach.split(":")[0])
            driver_id = int(selected_driver.split(":")[0])
            destination_id = int(selected_destination.split(":")[0])

            date_pattern = r"^\d{4}-\d{2}-\d{2}$"
            if not re.match(date_pattern, trip_date_str): info("Input Error", "Invalid date format. Use YYYY-MM-DD."); return
            try:
                trip_date = datetime.datetime.strptime(trip_date_str, "%Y-%m-%d").date()
                if trip_date < datetime.date.today():
                    if not app.yesno("Past Date", "Selected date is in the past. Continue?"): return
            except ValueError: info("Input Error", "Invalid date value."); return

            cursor.execute("INSERT INTO trips (CoachID, DriverID, DestinationID, Date) VALUES (%s, %s, %s, %s)",
                           (coach_id, driver_id, destination_id, trip_date_str))
            conn.commit()
            info("Success", "Trip added successfully.")
            add_trip_window.destroy(); parent.show()

        except (ValueError, IndexError): info("Input Error", "Invalid selection or ID format.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Trip details might already exist.")
            elif err.errno == 1452: info("Database Error", "Invalid Coach, Driver, or Destination ID.")
            else: info("Database Error", f"Failed to add Trip: {err.msg}")

    button_box = Box(add_trip_window, layout="grid", width="fill")
    add_button = PushButton(button_box, text = "Add Trip", grid=[0,0], command = add_trip)
    back_button = PushButton(button_box, text = "Back", grid=[1,0], command = lambda: (add_trip_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_trip_window.show()
#endregion

#region Remove Windows
def open_remove_booking_window():
    parent = staff_bookings_window # Assume called from staff

    global remove_booking_window, remove_booking_entry
    remove_booking_window = Window(app, title="Remove Booking", width = 400, height = 150, bg = BG_COLOR) # Adjusted height
    Text(remove_booking_window, text = "Enter Booking ID to remove:", color = TEXT_COLOR)
    remove_booking_entry = TextBox(remove_booking_window, width='fill')

    def remove_booking():
        booking_id = remove_booking_entry.value
        if not booking_id.isdigit(): info("Input Error", "Booking ID must be a number."); return
        if not app.yesno("Confirm Deletion", f"Delete Booking ID {booking_id}?"): return

        try:
            cursor.execute("DELETE FROM bookings WHERE BookingID = %s", (booking_id,))
            conn.commit()
            if cursor.rowcount > 0: info("Success", f"Booking ID {booking_id} removed.")
            else: info("Not Found", f"Booking ID {booking_id} not found.")
            remove_booking_window.destroy(); parent.show()
        except mysql.connector.Error as err: info("Database Error", f"Failed to remove Booking: {err.msg}")

    button_box = Box(remove_booking_window, layout="grid", width="fill")
    remove_button = PushButton(button_box, text="Remove Booking", grid=[0,0], command=remove_booking)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (remove_booking_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_booking_window.show()


def open_remove_coach_window():
    parent = coaches_window # Assume called from admin

    global remove_coach_window, remove_coach_entry
    remove_coach_window = Window(app, title="Remove Coach", width=400, height=150, bg=BG_COLOR) # Adjusted height
    Text(remove_coach_window, text="Enter Coach ID to remove:", color=TEXT_COLOR)
    remove_coach_entry = TextBox(remove_coach_window, width='fill')

    def remove_coach():
        coach_id = remove_coach_entry.value
        if not coach_id.isdigit(): info("Input Error", "Coach ID must be a number."); return
        if not app.yesno("Confirm Deletion", f"Delete Coach ID {coach_id}?"): return

        try:
            # Optional check for related trips
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE CoachID = %s", (coach_id,))
            if cursor.fetchone()['trip_count'] > 0:
                if not app.yesno("Warning", "Coach used in trips. Continue deletion?"): return

            cursor.execute("DELETE FROM coaches WHERE CoachID = %s", (coach_id,))
            conn.commit()
            if cursor.rowcount > 0: info("Success", f"Coach ID {coach_id} removed.")
            else: info("Not Found", f"Coach ID {coach_id} not found.")
            remove_coach_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == 1451: info("Database Error", "Cannot delete: Coach referenced by trips.")
            else: info("Database Error", f"Failed to remove coach: {err.msg}")

    button_box = Box(remove_coach_window, layout="grid", width="fill")
    remove_button = PushButton(button_box, text="Remove Coach", grid=[0,0], command=remove_coach)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (remove_coach_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_coach_window.show()

def open_remove_customer_window():
    parent = staff_customers_window # Assume staff context

    global remove_customer_window, remove_customer_entry
    remove_customer_window = Window(app, title="Remove Customer", width=400, height=150, bg=BG_COLOR) # Adjusted height
    Text(remove_customer_window, text="Enter Customer ID to remove:", color=TEXT_COLOR)
    remove_customer_entry = TextBox(remove_customer_window, width='fill')

    def remove_customer():
        customer_id = remove_customer_entry.value
        if not customer_id.isdigit(): info("Input Error", "Customer ID must be a number."); return
        if not app.yesno("Confirm Deletion", f"Delete Customer ID {customer_id} and related bookings?"): return

        try:
            # Optional check for bookings
            cursor.execute("SELECT COUNT(*) as booking_count FROM bookings WHERE CustomerID = %s", (customer_id,))
            if cursor.fetchone()['booking_count'] > 0:
                 if not app.yesno("Warning", "Customer has bookings. Deleting will remove them. Continue?"): return
                 # Delete bookings first (if DB doesn't cascade)
                 # cursor.execute("DELETE FROM bookings WHERE CustomerID = %s", (customer_id,))

            cursor.execute("DELETE FROM customers WHERE CustomerID = %s", (customer_id,))
            conn.commit()
            if cursor.rowcount > 0: info("Success", f"Customer ID {customer_id} removed.")
            else: info("Not Found", f"Customer ID {customer_id} not found.")
            remove_customer_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == 1451: info("Database Error", "Cannot delete customer due to related bookings.")
            else: info("Database Error", f"Failed to remove customer: {err.msg}")

    button_box = Box(remove_customer_window, layout="grid", width="fill")
    remove_button = PushButton(button_box, text="Remove Customer", grid=[0,0], command=remove_customer)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command= lambda: (remove_customer_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR;  back_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_window.show()


def open_remove_destination_window():
    parent = destinations_window # Assume admin context

    global remove_destination_window, remove_destination_entry
    remove_destination_window = Window(app, title = "Remove Destination", width = 400, height = 150, bg=BG_COLOR) # Adjusted height
    Text(remove_destination_window, text = "Enter Destination ID to remove:", color = TEXT_COLOR) # Corrected text
    remove_destination_entry = TextBox(remove_destination_window, width='fill')

    def remove_destination():
        destination_id = remove_destination_entry.value
        if not destination_id.isdigit(): info("Input Error", "Destination ID must be a number."); return
        if not app.yesno("Confirm Deletion", f"Delete Destination ID {destination_id}?"): return

        try:
            # Optional check for related trips
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DestinationID = %s", (destination_id,))
            if cursor.fetchone()['trip_count'] > 0:
                if not app.yesno("Warning", "Destination used in trips. Continue deletion?"): return

            cursor.execute("DELETE FROM destinations WHERE DestinationID = %s", (destination_id,))
            conn.commit()
            if cursor.rowcount > 0: info("Success", f"Destination ID {destination_id} removed.")
            else: info("Not Found", f"Destination ID {destination_id} not found.")
            remove_destination_window.destroy(); parent.show()
        except mysql.connector.Error as err:
            if err.errno == 1451: info("Database Error", "Cannot delete: Destination referenced by trips.")
            else: info("Database Error", f"Failed to remove destination: {err.msg}")

    button_box = Box(remove_destination_window, layout="grid", width="fill")
    remove_button = PushButton(button_box, text="Remove Destination", grid=[0,0], command=remove_destination)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command = lambda: (remove_destination_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_destination_window.show()

def open_remove_driver_window():
    parent = drivers_window # Assume admin context

    global remove_driver_window, remove_driver_entry
    remove_driver_window = Window(app, title = "Remove Driver", width = 400, height = 150, bg = BG_COLOR) # Adjusted height
    Text(remove_driver_window, text="Enter Driver ID to remove:", color = TEXT_COLOR)
    remove_driver_entry = TextBox(remove_driver_window, width='fill')

    def remove_driver():
        driver_id = remove_driver_entry.value
        if not driver_id.isdigit(): info("Input Error", "Driver ID must be a number."); return
        if not app.yesno("Confirm Deletion", f"Delete Driver ID {driver_id}?"): return

        try:
            # Optional check for related trips
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DriverID = %s", (driver_id,))
            if cursor.fetchone()['trip_count'] > 0:
                 if not app.yesno("Warning", "Driver assigned to trips. Continue deletion?"): return

            cursor.execute("DELETE FROM drivers WHERE DriverID = %s", (driver_id,))
            conn.commit()
            if cursor.rowcount > 0: info("Success", f"Driver ID {driver_id} removed.")
            else: info("Not Found", f"Driver ID {driver_id} not found.")
            remove_driver_window.destroy(); parent.show()
        except mysql.connector.Error as err:
             if err.errno == 1451: info("Database Error", "Cannot delete: Driver referenced by trips.")
             else: info("Database Error", f"Failed to remove driver: {err.msg}")

    button_box = Box(remove_driver_window, layout="grid", width="fill")
    remove_button = PushButton(button_box, text = "Remove Driver", grid=[0,0], command = remove_driver)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: (remove_driver_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_driver_window.show()

#endregion Remove Windows


# --- Query Window ---
def open_query_window():
    """Opens a window for executing various database queries."""
    global query_window
    query_window = Window(app, title="Database Queries", width=800, height=600, bg=BG_COLOR)
    Text(query_window, text="Select a Query:", color=TEXT_COLOR)

    # --- Query 1: Passengers by Trip ---
    def lincoln_passengers():
        selection_window = Window(query_window, title="Select Trip for Passenger List", width=400, height=200, bg=BG_COLOR)
        Text(selection_window, text="Select Trip:", color=TEXT_COLOR)
        trip_query_combo = Combo(selection_window, options=[], width="fill")

        try: # Populate Trip ComboBox
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY t.Date DESC, d.DestinationName
            """)
            trips_for_combo = cursor.fetchall()
            trip_query_combo.clear(); trip_query_combo.append("")
            for trip in trips_for_combo: trip_query_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trips: {err}"); selection_window.destroy(); return

        def run_passenger_query():
            selected_trip = trip_query_combo.value
            if not selected_trip: info("Input Error", "Please select a trip."); return
            try:
                trip_id = int(selected_trip.split(":")[0])
                cursor.execute("""
                    SELECT c.CustomerID, c.FirstName, c.Surname FROM customers c
                    JOIN bookings b ON c.CustomerID = b.CustomerID WHERE b.TripID = %s
                    ORDER BY c.Surname, c.FirstName
                """, (trip_id,))
                passengers = cursor.fetchall()

                result_window = Window(query_window, title=f"Passengers on Trip {trip_id}", width=400, height=300, bg=BG_COLOR)
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
                if passengers:
                    result_list.append(f"{'ID':<5}{'Name':<25}"); result_list.append("-" * 30)
                    for p in passengers: result_list.append(f"{p['CustomerID']:<5}{p['FirstName']} {p['Surname']}")
                else: result_list.append("No passengers booked on this trip.")
                close_button = PushButton(result_window, text="Close", command=result_window.destroy, align="bottom")
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show(); selection_window.destroy()
            except (ValueError, IndexError): info("Input Error", "Invalid trip selection.")
            except mysql.connector.Error as err: info("Database Error", f"Error fetching passenger data: {err}")

        btn_box = Box(selection_window, layout="grid", width="fill")
        ok_button = PushButton(btn_box, text="Show Passengers", grid=[0,0], command=run_passenger_query)
        cancel_button = PushButton(btn_box, text="Cancel", grid=[1,0], command=selection_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        selection_window.show()


    # --- Query 2: Available trips ---
    def available_trips():
        try:
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName, d.CityName, c.Seats,
                       COALESCE((SELECT SUM(b.NumberofPeople) FROM bookings b WHERE b.TripID = t.TripID), 0) AS BookedSeats
                FROM trips t JOIN destinations d ON t.DestinationID = d.DestinationID JOIN coaches c ON t.CoachID = c.CoachID
                WHERE t.Date >= CURDATE() ORDER BY t.Date ASC
            """)
            trips = cursor.fetchall()
            result_window = Window(query_window, title="Available Trips (Upcoming)", width=650, height=400, bg=BG_COLOR)
            result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
            if trips:
                result_list.append(f"{'ID':<5}{'Date':<12}{'Destination':<25}{'City':<15}{'Seats Avail.':<12}")
                result_list.append("-" * 70)
                for trip in trips:
                     available = trip['Seats'] - trip['BookedSeats']
                     result_list.append(f"{trip['TripID']:<5}{trip['Date']!s:<12}{trip['DestinationName']:<25}{trip['CityName']:<15}{available:<12}")
            else: result_list.append("No upcoming trips currently available.")
            close_button = PushButton(result_window, text = "Close", command = result_window.destroy, align="bottom")
            close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
            result_window.show()
        except mysql.connector.Error as err: info("Database Error", f"Error fetching trip data: {err}")

    # --- Query 3: Customers by Postcode ---
    def postcode_customers():
        postcode_window = Window(query_window, title="Enter Postcode Area", width=300, height=150, bg=BG_COLOR)
        Text(postcode_window, text="Enter Postcode (e.g., 'SW1A'):", color=TEXT_COLOR)
        postcode_entry = TextBox(postcode_window, width='fill')

        def run_postcode_query():
            postcode = postcode_entry.value.strip().upper()
            if not postcode: info("Input Error", "Please enter a postcode area."); return
            try:
                cursor.execute("""
                    SELECT CustomerID, FirstName, Surname, AddressLine1, Postcode FROM customers
                    WHERE UPPER(Postcode) LIKE %s ORDER BY Postcode, Surname
                """, (postcode + '%',))
                customers = cursor.fetchall()
                result_window = Window(query_window, title=f"Customers in {postcode}*", width=600, height=400, bg=BG_COLOR)
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
                if customers:
                     result_list.append(f"{'ID':<5}{'Name':<30}{'Address':<35}{'Postcode':<10}"); result_list.append("-" * 80)
                     for c in customers: result_list.append(f"{c['CustomerID']:<5}{c['FirstName']} {c['Surname']:<28}{c['AddressLine1']:<35}{c['Postcode']:<10}")
                else: result_list.append(f"No customers found starting with postcode {postcode}.")
                close_button = PushButton(result_window, text="Close", command=result_window.destroy, align="bottom")
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show(); postcode_window.destroy()
            except mysql.connector.Error as err: info("Database Error", f"Error fetching customer data: {err}")

        btn_box = Box(postcode_window, layout="grid", width="fill")
        ok_button = PushButton(btn_box, text="Find Customers", grid=[0,0], command=run_postcode_query)
        cancel_button = PushButton(btn_box, text="Cancel", grid=[1,0], command=postcode_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        postcode_window.show()

    # --- Query 4: Trip Income ---
    def trip_income_window():
        income_window = Window(query_window, title = "Calculate Trip Income", width = 400, height = 200, bg = BG_COLOR)
        Text(income_window, text="Select Trip:", color=TEXT_COLOR) # Changed to Combo
        trip_income_combo = Combo(income_window, options=[], width='fill')

        try: # Populate Trip ComboBox
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY t.Date DESC, d.DestinationName
            """)
            trips_for_income = cursor.fetchall()
            trip_income_combo.clear(); trip_income_combo.append("")
            for trip in trips_for_income: trip_income_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trips: {err}"); income_window.destroy(); return

        def calculate_income():
            selected_trip_income = trip_income_combo.value
            if not selected_trip_income: info("Input Error", "Please select a trip."); return
            try:
                trip_id = int(selected_trip_income.split(":")[0])
                cursor.execute("SELECT SUM(b.BookingCost) AS TotalIncome FROM bookings b WHERE b.TripID = %s", (trip_id,))
                result = cursor.fetchone()
                income = result['TotalIncome'] if result and result['TotalIncome'] is not None else 0
                info(f"Income for Trip {trip_id}", f"Total Booking Income: £{income:.2f}")
            except (ValueError, IndexError): info("Input Error", "Invalid trip selection.")
            except mysql.connector.Error as err: info("Database Error", f"Error calculating income: {err}")

        btn_box = Box(income_window, layout="grid", width="fill")
        calculate_button = PushButton(btn_box, text = "Calculate Income", grid=[0,0], command = calculate_income)
        cancel_button = PushButton(btn_box, text = "Close", grid=[1,0], command = income_window.destroy)
        calculate_button.bg = BUTTON_BG_COLOR; calculate_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        income_window.show()

    # --- Buttons for each query ---
    query_button_box = Box(query_window, layout="grid", width="fill")
    passengers_button = PushButton(query_button_box, text="Passengers by Trip", grid=[0,0], width=20, command=lincoln_passengers)
    trips_button = PushButton(query_button_box, text="Available Trips", grid=[1,0], width=20, command=available_trips)
    postcode_button = PushButton(query_button_box, text="Customers by Postcode", grid=[0,1], width=20, command=postcode_customers)
    income_button = PushButton(query_button_box, text = "Calculate Trip Income", grid=[1,1], width=20, command = trip_income_window)
    for button in query_button_box.children:
         if isinstance(button, PushButton): button.bg = BUTTON_BG_COLOR; button.text_color = BUTTON_TEXT_COLOR

    back_button = PushButton(query_window, text="Back to Menu", command=query_window.destroy, align="bottom")
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    query_window.show()

# --- Login and Main App ---
def check_admin_login():
    if username_entry.value.lower() == "admin" and password_entry.value == "admin":
        open_admin_main_window()
    else:
        info("Login Failed", "Incorrect username or password.")
        password_entry.value = "" # Clear password field on failure


def open_admin_login_window():
    app.hide()
    global admin_login_window, username_entry, password_entry
    admin_login_window = Window(app, title="Admin Login", width=300, height=200, bg=BG_COLOR)
    Text(admin_login_window, text="Username:", color=TEXT_COLOR)
    username_entry = TextBox(admin_login_window, width="fill")
    Text(admin_login_window, text="Password:", color=TEXT_COLOR)
    password_entry = TextBox(admin_login_window, hide_text=True, width="fill")
    username_entry.focus() # Set focus to username field

    button_box = Box(admin_login_window, layout="grid", width="fill")
    login_button = PushButton(button_box, text="Login", grid=[0,0], command=check_admin_login)
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: go_back(admin_login_window, app))

    login_button.bg = BUTTON_BG_COLOR; login_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    admin_login_window.show()



# --- Main App Setup ---
app = App("Silver Dawn Coaches", layout="grid", bg=BG_COLOR, width=800, height=600)

logo = Picture(app, image="silverDawnLogo.png", grid=[0, 0, 2, 1])
if not logo.image: Text(app, text="[Logo Image Not Found]", color="yellow", grid=[0, 0, 2, 1])

title = Text(app, text="SILVER DAWN COACHES\nBOOKING & DATA SYSTEM", size=16, font="Arial", grid=[0, 1, 2, 1], color=TEXT_COLOR)

button_container = Box(app, grid=[0, 2, 2, 1], layout="grid")
admin_button = PushButton(button_container, text="Admin Login", grid=[0,0], command=open_admin_login_window, align="left", width=15)
staff_button = PushButton(button_container, text="Staff Menu", grid=[1,0], command=open_staff_window, align="left", width=15)
admin_button.bg = BUTTON_BG_COLOR; admin_button.text_color = BUTTON_TEXT_COLOR
staff_button.bg = BUTTON_BG_COLOR; staff_button.text_color = BUTTON_TEXT_COLOR

app.tk.grid_columnconfigure(0, weight=1)
app.tk.grid_columnconfigure(1, weight=1)
app.tk.grid_rowconfigure(0, weight=1) # Logo area gets more space
app.tk.grid_rowconfigure(1, weight=0)
app.tk.grid_rowconfigure(2, weight=0)

# Define window variables globally *before* they might be used in lambdas/comparisons
# (Even though we switched to passing functions, this can prevent NameErrors if windows are opened out of order somehow)
admin_login_window = None
admin_main_window = None
customers_window = None
destinations_window = None
coaches_window = None
drivers_window = None
staff_window = None
staff_customers_window = None
staff_bookings_window = None
staff_destinations_window = None
staff_trips_window = None
query_window = None
# Add/Remove windows are usually temporary and don't need global refs unless reused heavily
# add_customer_window = None etc...

app.display()

# --- Close Connection ---
if conn and conn.is_connected():
    cursor.close()
    conn.close()
    print("Database connection closed.")