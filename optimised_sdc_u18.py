import mysql.connector
from guizero import App, Text, Picture, PushButton, Box, TextBox, Combo, Window, ListBox, info
from mysql.connector import errorcode
import datetime
import re
import math # Needed for ceil - actually not needed anymore, but leave it for now

# --- Database Configuration ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root" # Replace with your actual password if different
DB_NAME = "sdc_farrukh_u18"

# --- Color Variables ---
BG_COLOR = "purple"
BUTTON_BG_COLOR = "white"
BUTTON_TEXT_COLOR = "black"
TEXT_COLOR = "white"
# Removed seat selection colors


# --- Database Connection ---
try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    # Use dictionary=True for easier data access by column name
    # Using dictionary=True allows accessing results by column name (e.g., row['FirstName'])
    # instead of by index (e.g., row[0]), improving code readability.
    cursor = conn.cursor(dictionary=True)
except mysql.connector.Error as err:
    # Graceful exit if DB connection fails
    # Gracefully handles database connection errors during startup.
    try:
        # Attempt to show a Guizero popup before exiting
        # Attempts to show a user-friendly error message using a temporary Guizero window.
        temp_app = App(title="DB Connection Error", visible=False) # Create hidden temp app # Creates a hidden temporary app instance.
        info("Database Connection Error", f"Failed to connect to database: {err}")
        temp_app.destroy() # Close the temp app # Closes the temporary app window.
    except Exception:
        # Fallback to console if GUI fails
        # If the GUI fails (e.g., display not available), fallback to printing the error to the console.
        print(f"CRITICAL DATABASE ERROR: {err}")
    # Exits the script immediately as the application cannot function without a database connection.
    exit() # Stop the script

# --- Pagination Globals ---
# Variables to manage the display of large datasets in tables across multiple pages.
current_page = 0 # General current page for main table views
records_per_page = 15 # How many records to show per page in main table views
query_records_per_page = 10 # Specific pagination for query results

# --- Helper Functions for Table Display & Pagination ---

def clear_box(box):
    """Removes all widgets from a given Box."""
    # Iterate over a copy of the children list because destroying modifies the list
    # Creates a copy of the children list because destroying a widget modifies the original list
    # while iterating over it, which can lead to skipped widgets or errors.
    widgets_to_destroy = box.children[:]
    for widget in widgets_to_destroy:
        widget.destroy()

def create_search_box(parent_box, table_name, table_view_box, pagination_box):
    """Creates a search interface (TextBox, Dropdown, Button) for tables"""
    search_container = Box(parent_box, align="top", width="fill", layout="grid")
    Text(search_container, text="Search:", grid=[0, 0], align="left", color=TEXT_COLOR)
    search_input = TextBox(search_container, width=25, grid=[1, 0], align="left")

    # Define which fields are searchable for each table
    search_fields = {
        "trips": ["TripID", "CoachID", "DriverID", "DestinationID", "Date", "CoachReg", "DriverName", "DestinationName"],
        "destinations": ["DestinationID", "DestinationName", "Hotel", "CityName", "Days", "DestinationCost"],
        "coaches": ["CoachID", "Registration", "Seats"],
        "drivers": ["DriverID", "DriverName"],
        "customers": ["CustomerID", "FirstName", "Surname", "Email", "City", "Postcode", "PhoneNumber"],
        "bookings": ["BookingID", "CustomerID", "TripID", "BookingCost", "NumberOfPeople", "SpecialRequest", "BookingDate", "CustomerName", "DestinationName"] # Added CustomerName & DestinationName
    }

    if table_name not in search_fields:
        Text(search_container, text="Search not available for this table.", grid=[2, 0], align="left", color="red")
        return

    Text(search_container, text=" by:", grid=[2, 0], align="left", color=TEXT_COLOR)
    available_options = search_fields.get(table_name, [])
    if not available_options:
         Text(search_container, text="No searchable fields configured.", grid=[3, 0], align="left", color="red")
         return

    field_dropdown = Combo(search_container, options=available_options, grid=[3, 0], align="left")
    if available_options: # Set default selection
        field_dropdown.value = available_options[0]

    # Search button triggers the fetch function with search parameters
    search_button = PushButton(search_container, text="Search", grid=[4, 0], align="left",
                               command=lambda: fetch_and_display_table(table_name, table_view_box, pagination_box,
                                                                     search_term=search_input.value,
                                                                     search_field=field_dropdown.value))
    search_button.bg = BUTTON_BG_COLOR
    search_button.text_color = BUTTON_TEXT_COLOR


def fetch_and_display_table(table_name, table_box, pagination_box, page=0, search_term=None, search_field=None):
    """
    Fetches data based on table name, search criteria, and page, then displays it.
    Fetches data for a specified table and page, then displays it in a grid layout
    within the provided `table_box`. Also sets up pagination controls in `pagination_box`.

    Args:
        table_name (str): The name of the database table to fetch data from (e.g., "bookings", "customers").
        table_box (Box): The Guizero Box widget where the data grid will be displayed.
        pagination_box (Box): The Guizero Box widget where pagination buttons will be placed.
        page (int): The page number to fetch (0-indexed).
    """
    global current_page
    current_page = page
    offset = page * records_per_page

    base_query = "" # The FROM and JOIN clauses
    select_query = "" # The SELECT part
    columns = [] # User-friendly headers for the table
    where_clause = "" # SQL WHERE clause for searching
    query_params = [] # Parameters for the SQL query to prevent injection

    try:
        search_value = None
        if search_term and search_field:
            search_value = f"%{search_term}%" 

        # --- Configure Query, Columns, and Search Logic for Each Table ---
        # --- Dynamically configure Query and Columns based on the requested table_name ---
        # Uses LEFT JOINs to ensure records are shown even if related data is missing.
        if table_name == "bookings":
            # Fetch booking details along with customer name, destination, and trip date.
            # Format cost as currency.
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
            field_map = { # Map display search field name to DB field/alias
                "BookingID": "b.BookingID", "CustomerID": "b.CustomerID", "TripID": "b.TripID",
                "BookingCost": "b.BookingCost", "NumberOfPeople": "b.NumberofPeople",
                "SpecialRequest": "b.SpecialRequest", "BookingDate": "b.BookingDate",
                "CustomerName": "CONCAT(c.FirstName, ' ', c.Surname)",
                "DestinationName": "d.DestinationName"
            }
            if search_value and search_field in field_map:
                if search_field in ["BookingID", "CustomerID", "TripID", "NumberOfPeople", "BookingCost"]:
                    exact_search_value = search_term.lstrip('£')
                    if exact_search_value.isdigit():
                         where_clause = f" WHERE {field_map[search_field]} = %s"
                         query_params.append(exact_search_value)
                         search_value = None
                    else: search_term = None
                if search_value:
                    where_clause = f" WHERE {field_map[search_field]} LIKE %s"
                    query_params.append(search_value)

        elif table_name == "trips":
            # Fetch trip details along with destination name, driver name, and coach registration.
            select_query = """
                SELECT t.TripID, d.DestinationName, dr.DriverName, c.Registration as CoachReg, t.Date
            """
            base_query = """
                FROM trips t
                LEFT JOIN coaches c ON t.CoachID = c.CoachID
                LEFT JOIN drivers dr ON t.DriverID = dr.DriverID
                LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
            """
            columns = ["ID", "Destination", "Driver Name", "Coach Reg", "Date"]
            field_map = {
                "TripID": "t.TripID", "DestinationName": "d.DestinationName", "DriverName": "dr.DriverName",
                "CoachReg": "c.Registration", "Date": "t.Date", "CoachID": "t.CoachID",
                "DriverID": "t.DriverID", "DestinationID": "t.DestinationID"
            }
            if search_value and search_field in field_map:
                if search_field in ["TripID", "CoachID", "DriverID", "DestinationID"]:
                    if search_term.isdigit():
                         where_clause = f" WHERE {field_map[search_field]} = %s"
                         query_params.append(search_term)
                         search_value = None
                    else: search_term = None
                if search_value:
                    where_clause = f" WHERE {field_map[search_field]} LIKE %s"
                    query_params.append(search_value)

        elif table_name == "customers":
             select_query = "SELECT CustomerID, FirstName, Surname, Email, AddressLine1, AddressLine2, City, Postcode, PhoneNumber, SpecialNotes"
             base_query = f"FROM {table_name}"
             columns = ["ID", "First Name", "Surname", "Email", "Address 1", "Address 2", "City", "Postcode", "Phone", "Notes"]
             valid_columns = ["CustomerID", "FirstName", "Surname", "Email", "AddressLine1", "AddressLine2", "City", "Postcode", "PhoneNumber", "SpecialNotes"]
             if search_value and search_field in valid_columns:
                if search_field == "CustomerID":
                     if search_term.isdigit():
                          where_clause = f" WHERE {search_field} = %s"
                          query_params.append(search_term)
                          search_value = None
                     else: search_term = None
                if search_value:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     query_params.append(search_value)

        elif table_name == "coaches":
             select_query = "SELECT CoachID, Registration, Seats"
             base_query = f"FROM {table_name}"
             columns = ["ID", "Registration", "Seats"]
             valid_columns = ["CoachID", "Registration", "Seats"]
             if search_value and search_field in valid_columns:
                 if search_field in ["CoachID", "Seats"]:
                      if search_term.isdigit():
                           where_clause = f" WHERE {search_field} = %s"
                           query_params.append(search_term)
                           search_value = None
                      else: search_term = None
                 if search_value:
                      where_clause = f" WHERE {search_field} LIKE %s"
                      query_params.append(search_value)

        elif table_name == "destinations":
            select_query = "SELECT DestinationID, DestinationName, Hotel, DestinationCost, CityName, Days"
            base_query = f"FROM {table_name}"
            columns = ["ID", "Name", "Hotel", "Cost", "City", "Days"]
            valid_columns = ["DestinationID", "DestinationName", "Hotel", "DestinationCost", "CityName", "Days"]
            if search_value and search_field in valid_columns:
                if search_field in ["DestinationID", "DestinationCost", "Days"]:
                    exact_search_value = search_term.lstrip('£')
                    is_valid_num = False
                    try:
                        if search_field == "DestinationCost": float(exact_search_value); is_valid_num = True
                        else: int(exact_search_value); is_valid_num = True
                    except ValueError: pass
                    if is_valid_num:
                           where_clause = f" WHERE {search_field} = %s"
                           query_params.append(exact_search_value)
                           search_value = None
                    else: search_term = None
                if search_value:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     query_params.append(search_value)

        elif table_name == "drivers":
             select_query = "SELECT DriverID, DriverName"
             base_query = f"FROM {table_name}"
             columns = ["ID", "Driver Name"]
             valid_columns = ["DriverID", "DriverName"]
             if search_value and search_field in valid_columns:
                 if search_field == "DriverID":
                      if search_term.isdigit():
                           where_clause = f" WHERE {search_field} = %s"
                           query_params.append(search_term)
                           search_value = None
                      else: search_term = None
                 if search_value:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     query_params.append(search_value)
        else:
            Text(table_box, text=f"Table '{table_name}' display not configured.", color="red")
            return

        # --- Data Key Mapping ---
        # Maps the display column headers 
        # keys/aliases used in the SELECT query result dictionary 
        # Necessary because some display headers differ from the database column names or aliases.
        data_key_map = {}
        if table_name == "bookings": data_key_map = {"ID": "BookingID", "Cust. ID": "CustomerID", "Customer Name": "CustomerName", "Trip ID": "TripID", "Destination": "DestinationName", "Trip Date": "TripDate", "# People": "NumberofPeople", "Cost": "Cost", "Request": "SpecialRequest", "Booking Date": "BookingDate"}
        elif table_name == "trips": data_key_map = {"ID": "TripID", "Destination": "DestinationName", "Driver Name": "DriverName", "Coach Reg": "CoachReg", "Date": "Date"}
        elif table_name == "customers": data_key_map = {"ID": "CustomerID", "First Name": "FirstName", "Surname": "Surname", "Email": "Email", "Address 1": "AddressLine1", "Address 2": "AddressLine2", "City": "City", "Postcode": "Postcode", "Phone": "PhoneNumber", "Notes": "SpecialNotes"}
        elif table_name == "coaches": data_key_map = {"ID": "CoachID", "Registration": "Registration", "Seats": "Seats"}
        elif table_name == "destinations": data_key_map = {"ID": "DestinationID", "Name": "DestinationName", "Hotel": "Hotel", "Cost": "DestinationCost", "City": "CityName", "Days": "Days"}
        elif table_name == "drivers": data_key_map = {"ID": "DriverID", "Driver Name": "DriverName"}

        # Fetch total record count for pagination
        count_query = f"SELECT COUNT(*) as total {base_query}{where_clause}"
        cursor.execute(count_query, tuple(query_params))
        total_records = cursor.fetchone()['total']

        # Fetch records for the current page using LIMIT and OFFSET
        data_query = f"{select_query} {base_query}{where_clause} LIMIT %s OFFSET %s"
        limit_params = query_params + [records_per_page, offset]
        cursor.execute(data_query, tuple(limit_params))
        records = cursor.fetchall()
        # Calculate total pages needed (ceiling division)
        total_pages = (total_records + records_per_page - 1) // records_per_page

        clear_box(table_box)
        clear_box(pagination_box)

        if records or columns:
            table_grid = Box(table_box, layout="grid", width="fill", align="top")
            # Create header row
            for col, header in enumerate(columns):
                Text(table_grid, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True)
            # Populate data rows
            for row, record_dict in enumerate(records, start=1):
                for col, header in enumerate(columns):
                    data_key = data_key_map.get(header, header) # Get DB key for this header
                    raw_value = record_dict.get(data_key, '') # Get value from record dict
                    # Format data for display based on type
                    if isinstance(raw_value, datetime.date):
                        data_to_display = raw_value.strftime('%Y-%m-%d') # Format dates
                    elif isinstance(raw_value, (int, float)): # Format numbers (already formatted in query for cost)
                         data_to_display = str(raw_value) # Convert numbers
                    elif raw_value is None:
                        data_to_display = "" # Handle NULLs
                    else:
                        data_to_display = str(raw_value) # Convert others
                    Text(table_grid, text=data_to_display, grid=[col, row], color=TEXT_COLOR, size=10) # Display data
        elif not columns: Text(table_box, text="Columns not defined.", color="red")
        else: Text(table_box, text="No records found.", color=TEXT_COLOR)

        # Create Pagination Controls
        pagination_controls = Box(pagination_box, layout="grid", width="fill", align="bottom")
        if page > 0:
            prev_button = PushButton(pagination_controls, text="<< Previous",
                                     # Lambda captures current page `p` and calls fetch for previous page (p-1)
                                     command=lambda p=page, st=search_term, sf=search_field: fetch_and_display_table(table_name, table_box, pagination_box, p - 1, st, sf),
                                     grid=[0, 0], align="left")
            prev_button.bg = BUTTON_BG_COLOR; prev_button.text_color = BUTTON_TEXT_COLOR
        Text(pagination_controls, text=f"Page {page + 1} of {max(1, total_pages)}", grid=[1, 0], align="left", color=TEXT_COLOR)
        if page < total_pages - 1:
            next_button = PushButton(pagination_controls, text="Next >>",
                                     # Lambda calls fetch for next page (p+1)
                                     command=lambda p=page, st=search_term, sf=search_field: fetch_and_display_table(table_name, table_box, pagination_box, p + 1, st, sf),
                                     grid=[2, 0], align="left")
            next_button.bg = BUTTON_BG_COLOR; next_button.text_color = BUTTON_TEXT_COLOR

    except mysql.connector.Error as err:
        # Handle database errors during fetch/count
        clear_box(table_box); clear_box(pagination_box)
        Text(table_box, text=f"Database Error:\n{err}", color="red", size=12)
        print(f"DB Error in fetch_and_display for table '{table_name}': {err}")
    except Exception as e:
        # Handle other unexpected errors
        clear_box(table_box); clear_box(pagination_box)
        Text(table_box, text=f"An unexpected error occurred:\n{e}", color="red", size=12)
        import traceback; traceback.print_exc()


# --- GUI Functions ---
def go_back(current_window, previous_window):
    """Hides the current window and shows the previous one (or the main app)."""
    # Destroys the current window to free resources. If no previous window is specified,
    # shows the main application window (`app`).
    current_window.destroy()
    if previous_window:
        previous_window.show()
    else:
        app.show() # Fallback to main app if previous is None

# --- Back Button Functions (Specific Wrappers for Clarity) ---
def go_back_to_admin_main(): go_back(admin_main_window, app)
def go_back_to_admin_main_from_customers(): go_back(customers_window, admin_main_window)
def go_back_to_admin_main_from_destinations(): go_back(destinations_window, admin_main_window)
def go_back_to_admin_main_from_coaches(): go_back(coaches_window, admin_main_window)
def go_back_to_admin_main_from_drivers(): go_back(drivers_window, admin_main_window)
def go_back_to_staff_main_from_customers(): go_back(staff_customers_window, staff_window)
def go_back_to_staff_main_from_bookings(): go_back(staff_bookings_window, staff_window)
def go_back_to_staff_main_from_destinations(): go_back(staff_destinations_window, staff_window)
def go_back_to_staff_main_from_trips(): go_back(staff_trips_window, staff_window)

# --- Back Functions for Data Windows (Navigating from Data View -> Specific Menu) ---
def go_back_to_staff_bookings_menu_from_data(window_to_hide): go_back(window_to_hide, staff_bookings_window)
def go_back_to_admin_customers_menu_from_data(window_to_hide): go_back(window_to_hide, customers_window)
def go_back_to_staff_customers_menu_from_data(window_to_hide): go_back(window_to_hide, staff_customers_window)
def go_back_to_admin_coaches_menu_from_data(window_to_hide): go_back(window_to_hide, coaches_window)
def go_back_to_admin_destinations_menu_from_data(window_to_hide): go_back(window_to_hide, destinations_window)
def go_back_to_staff_destinations_menu_from_data(window_to_hide): go_back(window_to_hide, staff_destinations_window)
def go_back_to_admin_drivers_menu_from_data(window_to_hide): go_back(window_to_hide, drivers_window)
def go_back_to_staff_trips_menu_from_data(window_to_hide): go_back(window_to_hide, staff_trips_window)

# Back function specifically for logging out (returns to main app screen)
def go_back_to_main_menu(window_to_hide): go_back(window_to_hide, app) # Generic back to main app screen

# --- Data Fetching Functions (Fetch All - Used for Populating Combos etc.) ---
def get_all_bookings():
    """Fetches all bookings from the database."""
    """Fetches ALL booking records, joining customer name."""
    try:
        cursor.execute("""
            SELECT b.*, CONCAT(c.FirstName, ' ', c.Surname) as CustomerName
            FROM bookings b
            LEFT JOIN customers c ON b.CustomerID = c.CustomerID
        """)
        bookings = cursor.fetchall()
        return bookings
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching bookings: {err}")
        return None # Indicatesfailure

def get_all_customers():
    """Fetches all customers from the database, ordered by CustomerID."""
    """Fetches ALL customer records, ordered by CustomerID."""
    try:
        cursor.execute("SELECT * FROM customers ORDER BY CustomerID ASC")
        customers = cursor.fetchall()
        return customers
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching customers: {err}")
        return None

def get_all_coaches():
    """Fetches all coaches from the database."""
    """Fetches ALL coach records."""
    try:
        cursor.execute("SELECT * FROM coaches")
        coaches = cursor.fetchall()
        return coaches
    except mysql.connector.Error as err:
         info("Database Error", f"Error fetching coaches: {err}")
         return None

def get_all_destinations():
    """Fetches all destinations from the database"""
    """Fetches ALL destination records."""
    try:
        cursor.execute("SELECT * FROM destinations")
        destinations = cursor.fetchall()
        return destinations
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching destinations: {err}")
        return None

def get_all_drivers():
    """Fetches all drivers from the database."""
    """Fetches ALL driver records."""
    try:
        cursor.execute("SELECT * FROM drivers")
        drivers = cursor.fetchall()
        return drivers
    except mysql.connector.Error as err:
        info("Database Error", f"Error fetching drivers: {err}")
        return None

def get_all_trips():
    """Fetches all the trips from the database"""
    """Fetches ALL trip records, joining destination name."""
    try:
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


# --- Functions to open data windows (Using integrated fetch_and_display_table) ---
# No changes needed in these window opening functions
def open_bookings_data_window(parent_window, back_function_to_call):
    parent_window.hide()
    bookings_data_win = Window(app, title="Booking Data", width=950, height=600, bg=BG_COLOR)
    Text(bookings_data_win, text="All Bookings", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(bookings_data_win, align="top", width="fill")
    table_view_box = Box(bookings_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(bookings_data_win, align="bottom", width="fill")
    back_button_box = Box(bookings_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "bookings", table_view_box, pagination_box)
    fetch_and_display_table("bookings", table_view_box, pagination_box, page=0)

    # Adds back button using the specific back function passed in, ensuring correct navigation flow.
    if back_function_to_call:
        # Pass the bookings_data_win to be destroyed by go_back
        # Lambda calls the provided back function, passing the window to be closed.
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(bookings_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    bookings_data_win.show()

def open_customers_data_window(parent_window, back_function_to_call):
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
        # Pass the customers_data_win to be destroyed by go_back
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(customers_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    customers_data_win.show()

def open_coaches_data_window(parent_window, back_function_to_call):
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
        # Pass the coaches_data_win to be destroyed by go_back
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(coaches_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    coaches_data_win.show()

def open_destinations_data_window(parent_window, back_function_to_call):
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
        # Pass the destinations_data_win to be destroyed by go_back
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(destinations_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    destinations_data_win.show()

def open_drivers_data_window(parent_window, back_function_to_call):
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
        # Pass the drivers_data_win to be destroyed by go_back
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(drivers_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    drivers_data_win.show()

def open_trips_data_window(parent_window, back_function_to_call):
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
        # Pass the trips_data_win to be destroyed by go_back
        back_button = PushButton(back_button_box, text="Back to Menu",
                                 command=lambda: back_function_to_call(trips_data_win), align="right")
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    else: Text(back_button_box, text="Back function error", color="red", align="right")
    trips_data_win.show()


#region Admin Windows
# --- Admin Window Functions ---
# --- MODIFIED CALLS to pass parent window ---
def open_customers_window():
    admin_main_window.hide()
    global customers_window
    customers_window = Window(app, title="Admin Customers", width=800, height=600, bg=BG_COLOR)
    Text(customers_window, text="Customers Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(customers_window, layout="auto", width="fill")
    view_customers_button = PushButton(button_box, text="View Customers", width=20,
                                       command=lambda: open_customers_data_window(customers_window, go_back_to_admin_customers_menu_from_data))
    # Pass customers_window as the parent to return to
    remove_customers_button = PushButton(button_box, text="Remove Customers", width=20,
                                         command=lambda: open_remove_customer_window(customers_window)) # MODIFIED
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
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20,
                                          command=lambda: open_destinations_data_window(destinations_window, go_back_to_admin_destinations_menu_from_data))
    # Pass destinations_window as the parent to return to
    add_destinations_button = PushButton(button_box, text="Add Destinations", width=20,
                                         command=lambda: open_add_destination_window(destinations_window)) # MODIFIED
    remove_destinations_button = PushButton(button_box, text="Remove Destinations", width=20,
                                            command=lambda: open_remove_destination_window(destinations_window)) # MODIFIED
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
    view_coaches_button = PushButton(button_box, text="View Coaches", width=20,
                                     command=lambda: open_coaches_data_window(coaches_window, go_back_to_admin_coaches_menu_from_data))
    # Pass coaches_window as the parent to return to
    add_coaches_button = PushButton(button_box, text="Add Coaches", width=20,
                                    command=lambda: open_add_coach_window(coaches_window)) # MODIFIED
    remove_coaches_button = PushButton(button_box, text="Remove Coaches", width=20,
                                       command=lambda: open_remove_coach_window(coaches_window)) # MODIFIED
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
    view_drivers_button = PushButton(button_box, text="View Drivers", width=20,
                                     command=lambda: open_drivers_data_window(drivers_window, go_back_to_admin_drivers_menu_from_data))
    # Pass drivers_window as the parent to return to
    add_drivers_button = PushButton(button_box, text="Add Drivers", width=20,
                                    command=lambda: open_add_driver_window(drivers_window)) # MODIFIED
    remove_drivers_button = PushButton(button_box, text="Remove Drivers", width=20,
                                       command=lambda: open_remove_driver_window(drivers_window)) # MODIFIED
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_drivers)
    view_drivers_button.bg = BUTTON_BG_COLOR; view_drivers_button.text_color = BUTTON_TEXT_COLOR
    add_drivers_button.bg = BUTTON_BG_COLOR; add_drivers_button.text_color = BUTTON_TEXT_COLOR
    remove_drivers_button.bg = BUTTON_BG_COLOR; remove_drivers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    drivers_window.show()


def open_admin_main_window():
    global admin_login_window
    # Attempt to hide the login window if it exists and is visible.
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
    # Pass admin_main_window as the parent to return to
    search_button = PushButton(button_box, text="QUERIES", width=15,
                               command=lambda: open_query_window(admin_main_window)) 
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
    view_customer_button = PushButton(button_box, text="View Customers", width=20,
                                      command=lambda: open_customers_data_window(staff_customers_window, go_back_to_staff_customers_menu_from_data))
    # Pass staff_customers_window as the parent to return to
    add_customer_button = PushButton(button_box, text="Add Customer", width=20,
                                     command=lambda: open_add_customer_window(staff_customers_window)) # MODIFIED
    remove_customer_button = PushButton(button_box, text="Remove Customer", width=20,
                                        command=lambda: open_remove_customer_window(staff_customers_window)) # MODIFIED
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
    view_bookings_button = PushButton(button_box, text="View Bookings", width=20,
                                      command=lambda: open_bookings_data_window(staff_bookings_window, go_back_to_staff_bookings_menu_from_data))
    # Pass staff_bookings_window as the parent to return to
    add_booking_button = PushButton(button_box, text="Add Booking", width=20,
                                    command=lambda: open_add_booking_window(staff_bookings_window)) # MODIFIED
    remove_booking_button = PushButton(button_box, text="Remove Booking", width=20,
                                       command=lambda: open_remove_booking_window(staff_bookings_window)) # MODIFIED
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
    view_trips_button = PushButton(button_box, text="View Trips", width=20,
                                   command=lambda: open_trips_data_window(staff_trips_window, go_back_to_staff_trips_menu_from_data))
    # Pass staff_trips_window as the parent to return to
    add_trips_button = PushButton(button_box, text="Add Trips", width=20,
                                  command=lambda: open_add_trip_window(staff_trips_window)) # MODIFIED
    remove_trips_button = PushButton(button_box, text="Remove Trips", width = 20,
                                     command=lambda: open_remove_trip_window(staff_trips_window)) # MODIFIED

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
    back_button = PushButton(button_box, text="Logout", width=15, command=lambda: go_back_to_main_menu(staff_window))

    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    bookings_button.bg = BUTTON_BG_COLOR; bookings_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_window.show()

#endregion Staff Windows


#region Add Windows

# Modified: Added parent_window parameter
def open_add_customer_window(parent_window):
    parent_window.hide() # Hide the menu while adding

    # Use local variables for widgets in this window instance
    add_customer_win = None
    first_name_entry = None
    surname_entry = None
    email_entry = None
    address1_entry = None
    address2_entry = None
    city_entry = None
    postcode_entry = None
    phone_entry = None
    notes_entry = None
    add_button = None
    back_button = None

    # Define required fields and error message for validation feedback.
    CUSTOMER_REQUIRED_FIELDS = ("First Name", "Surname", "Email", "Address Line 1", "City", "Postcode", "Phone Number")
    STATIC_ERROR_MESSAGE = f"Please ensure all required fields are entered correctly: [{', '.join(CUSTOMER_REQUIRED_FIELDS)}]"

    try:
        add_customer_win = Window(app, title="Add Customer", width=450, height=600, bg=BG_COLOR) # Use app as master
        add_customer_win.tk.resizable(False, False)

        # Main form container using grid layout
        form_box = Box(add_customer_win, layout="grid", width="fill", align="top")

        # Row 0: Title
        Text(form_box, text="Enter Customer Details:", color=TEXT_COLOR, size=12, grid=[0, 0, 2, 1], align="top")

        # Row 1: First Name
        Text(form_box, text="First Name:", color=TEXT_COLOR, grid=[0, 1], align="left")
        first_name_entry = TextBox(form_box, width=25, grid=[1, 1], align="left")

        # Row 2: Surname
        Text(form_box, text="Surname:", color=TEXT_COLOR, grid=[0, 2], align="left")
        surname_entry = TextBox(form_box, width=25, grid=[1, 2], align="left")

        # Row 3: Email
        Text(form_box, text="Email:", color=TEXT_COLOR, grid=[0, 3], align="left")
        email_entry = TextBox(form_box, width=25, grid=[1, 3], align="left")

        # Row 4: Address 1
        Text(form_box, text="Address Line 1:", color=TEXT_COLOR, grid=[0, 4], align="left")
        address1_entry = TextBox(form_box, width=25, grid=[1, 4], align="left")

        # Row 5: Address 2
        Text(form_box, text="Address Line 2:", color=TEXT_COLOR, grid=[0, 5], align="left")
        address2_entry = TextBox(form_box, width=25, grid=[1, 5], align="left") # Optional

        # Row 6: City
        Text(form_box, text="City:", color=TEXT_COLOR, grid=[0, 6], align="left")
        city_entry = TextBox(form_box, width=25, grid=[1, 6], align="left")

        # Row 7: Postcode
        Text(form_box, text="Postcode:", color=TEXT_COLOR, grid=[0, 7], align="left")
        postcode_entry = TextBox(form_box, width=15, grid=[1, 7], align="left") # Shorter width

        # Row 8: Phone
        Text(form_box, text="Phone Number:", color=TEXT_COLOR, grid=[0, 8], align="left")
        phone_entry = TextBox(form_box, width=25, grid=[1, 8], align="left")

        # Row 9: Notes
        Text(form_box, text="Special Notes:", color=TEXT_COLOR, grid=[0, 9], align="left")
        notes_entry = TextBox(form_box, width=25, grid=[1, 9], align="left", multiline=True, height=4) # Multiline

        def add_customer():
            try:
                # Get values from local widget variables
                first_name = first_name_entry.value.strip()
                surname = surname_entry.value.strip()
                email = email_entry.value.strip()
                address1 = address1_entry.value.strip()
                city = city_entry.value.strip()
                postcode = postcode_entry.value.strip()
                phone = phone_entry.value.strip()
                address2 = address2_entry.value.strip()
                notes = notes_entry.value.strip()

                # --- Improved Validation ---
                # --- Input Validation ---
                is_missing = not first_name or not surname or not email or not address1 or not city or not postcode or not phone
                email_valid = True
                if email:
                    # Basic email format validation using regex.
                    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if not re.match(email_regex, email):
                        email_valid = False

                if is_missing or not email_valid:
                    info("Input Error", STATIC_ERROR_MESSAGE + ("\nInvalid email format." if not email_valid and email else ""))
                    return
                # --- End Improved Validation ---


                # --- Database Insertion ---
                cursor.execute("""
                    INSERT INTO customers (FirstName, Surname, Email, AddressLine1,
                                           AddressLine2, City, Postcode, PhoneNumber, SpecialNotes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (first_name, surname, email, address1,
                      address2 or None, city, postcode, phone, notes or None)) # Use None for optional fields if empty
                conn.commit()
                info("Success", "Customer added successfully.")
                # Use go_back to destroy current and show parent
                go_back(add_customer_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                print(f"Database error adding customer: {err}")
                # More specific DB errors
                # Provide specific feedback for duplicate entry errors (e.g., unique email constraint).
                if err.errno == errorcode.ER_DUP_ENTRY:
                     info("Database Error", f"Failed to add customer.\nPossible duplicate entry (e.g., email): {err.msg}")
                else:
                     info("Database Error", f"Failed to add customer.\nError: {err.msg}")
            except Exception as e:
                print(f"Unexpected error adding customer: {e}")
                info("Error", f"An unexpected error occurred: {e}")

        # Buttons Box
        button_box = Box(add_customer_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text="Add Customer", grid=[0, 0], command=add_customer)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1, 0],
                                 command=lambda: go_back(add_customer_win, parent_window)) # MODIFIED
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR

        add_customer_win.show()

    except Exception as e: # Catch errors during window creation
        info("Error", f"Failed to open Add Customer window: {e}")
        if add_customer_win: add_customer_win.destroy()
        parent_window.show() # Ensure parent is shown again


# --- Reverted: Add Booking Window (Simpler Version) ---
def open_add_booking_window(parent_window):
    parent_window.hide() # Hide the menu while adding

    # Use local variables within this function scope for widgets
    add_booking_win = None
    customer_combo_widget = None
    trip_combo_widget = None
    # -- Add the message widget here --
    no_trips_message = None
    available_seats_text_widget = None
    num_people_entry_widget = None # Re-added
    special_request_entry_widget = None
    booking_date_entry_widget = None # Displays trip date, not for input
    add_button = None
    back_button = None

    # Store current available seats for validation
    current_available_seats = 0

    BOOKING_REQUIRED_FIELDS = ("Customer", "Trip", "Number of People")
    STATIC_BOOKING_ERROR_MESSAGE = f"Please ensure all required fields are selected/entered correctly: [{', '.join(BOOKING_REQUIRED_FIELDS)}]"

    try:
        # Reverted size and resizable property
        add_booking_win = Window(app, title="Add Booking", width=450, height=520, bg=BG_COLOR)
        add_booking_win.tk.resizable(False, False)

        # Use a Box with grid layout for the main form elements
        form_box = Box(add_booking_win, layout="grid", width="fill", align="top")

        # Row 0: Title (spans 2 columns)
        Text(form_box, text="Enter Booking Details:", color=TEXT_COLOR, size=12, grid=[0, 0, 2, 1], align="top")

        # Row 1: Customer Label and Combo
        Text(form_box, text="Customer:", color=TEXT_COLOR, grid=[0, 1], align="left")
        customer_combo_widget = Combo(form_box, options=[""], width=25, grid=[1, 1], align="left") # Use grid position

        # Row 2: Trip Label and Combo
        Text(form_box, text="Trip:", color=TEXT_COLOR, grid=[0, 2], align="left")
        trip_combo_widget = Combo(form_box, options=[""], width=25, grid=[1, 2], align="left") # Use grid position

        # --- ADDED: Row 2a: Message for no trips ---
        no_trips_message = Text(form_box, text="", color="yellow", size=10, grid=[0, 3, 2, 1], align="left", visible=False) # Initially hidden

        # Row 3 (now 4): Available Seats Display
        available_seats_text_widget = Text(form_box, text="Seats Available: -", color=TEXT_COLOR, grid=[0, 4, 2, 1], align="left")

        # Row 4 (now 5): Number of People Label and Entry (Re-added)
        Text(form_box, text="Number of People:", color=TEXT_COLOR, grid=[0, 5], align="left")
        num_people_entry_widget = TextBox(form_box, width=10, grid=[1, 5], align="left")

        # Row 5 (now 6): Special Request Label and Entry
        Text(form_box, text="Special Request:", color=TEXT_COLOR, grid=[0, 6], align="left")
        special_request_entry_widget = TextBox(form_box, width=25, grid=[1, 6], align="left", multiline=True, height=3)

        # Row 6 (now 7): Booking Date Label and Entry
        Text(form_box, text="Booking Date:", color=TEXT_COLOR, grid=[0, 7], align="left") # Label changed for clarity
        # Text(form_box, text="Trip Date:", color=TEXT_COLOR, grid=[0, 6], align="left") # Original label
        booking_date_entry_widget = TextBox(form_box, width=15, grid=[1, 7], align="left", enabled=False) # Disabled for user input.

        # --- Reverted: Function to update trip details (simpler) ---
        # --- Function to Update Details When Trip Changes ---
        def update_trip_details():
            """Called when trip combo changes. Updates date display & checks seat availability."""
            nonlocal current_available_seats # Allow modification of the outer scope variable # Modify the outer scope variable.
            selected_trip_str = trip_combo_widget.value
            trip_date = None
            trip_id = None
            current_available_seats = 0 

            # Try to extract ID and date
            # Extract TripID and Date from the combo string (e.g., "123: 2024-12-25 - London")
            match_id = re.match(r"^(\d+):.*", selected_trip_str)
            match_date = re.match(r"^\d+: (\d{4}-\d{2}-\d{2}) - .+$", selected_trip_str)

            if match_id:
                trip_id = int(match_id.group(1))
            if match_date:
                trip_date = match_date.group(1)

            booking_date_entry_widget.value = trip_date if trip_date else ""
            booking_date_entry_widget.enabled = False # Ensure stays disabled

            # Fetch and display available seats if a valid trip ID is found
            # If a valid trip ID extracted, query database for seat capacity.
            if trip_id:
                try:
                    # Get Total Seats
                    # Get total seats for the coach on this trip.
                    cursor.execute("SELECT c.Seats FROM trips t JOIN coaches c ON t.CoachID = c.CoachID WHERE t.TripID = %s", (trip_id,))
                    seat_result = cursor.fetchone()
                    total_seats = seat_result['Seats'] if seat_result else 0

                    # Get Booked Seats
                    # Get sum of people already booked.
                    cursor.execute("SELECT SUM(NumberofPeople) as booked FROM bookings WHERE TripID = %s", (trip_id,))
                    booked_result = cursor.fetchone()
                    booked_seats = booked_result['booked'] or 0 # Use 0 if SUM is NULL.

                    current_available_seats = total_seats - booked_seats
                    available_seats_text_widget.value = f"Seats Available: {current_available_seats}"

                except mysql.connector.Error as err:
                    available_seats_text_widget.value = "Error checking seats"
                    print(f"DB Error checking seats: {err}")
                except Exception as e:
                    available_seats_text_widget.value = "Error checking seats"
                    print(f"Error checking seats: {e}")
            else:
                # If no valid trip selected (e.g., blank option), clear info
                available_seats_text_widget.value = "Seats Available: -"
                current_available_seats = 0 # No trip selected or invalid format.

        # Assign the update function to the trip combo command
        # Assign the update function to the trip combo box's command.
        trip_combo_widget.update_command(update_trip_details)

        # --- Populate Customer Combo Box ---
        try:
            customers_data = get_all_customers() # This function now returns ordered data
            customer_combo_widget.clear()
            customer_combo_widget.append("")
            if customers_data:
                for customer in customers_data:
                     customer_combo_widget.append(f"{customer['CustomerID']}: {customer['FirstName']} {customer['Surname']}")
            else:
                customer_combo_widget.append("No customers found")
                customer_combo_widget.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Could not load customers: {err}")
            customer_combo_widget.append("Error loading customers")
            customer_combo_widget.disable()
        except Exception as e: # Catch other potential errors during customer load
            info("Error", f"Unexpected error loading customers: {e}"); customer_combo_widget.append("Error"); customer_combo_widget.disable()


        # --- Populate Trip Combo Box (Only Future Trips) ---
        # Populate Trip Combo and handle "No Trips" message
        try:
            # Fetch trips on or after today's date.
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName
                FROM trips t JOIN destinations d ON t.DestinationID = d.DestinationID
                WHERE t.Date >= CURDATE() ORDER BY t.Date
            """)
            trips_data = cursor.fetchall()
            trip_combo_widget.clear()
            trip_combo_widget.append("")
            if trips_data:
                for trip in trips_data:
                    trip_combo_widget.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
                no_trips_message.visible = False # Hide message if there are trips
                trip_combo_widget.enabled = True
                num_people_entry_widget.enabled = True # Ensure enabled
            else:
                 #trip_combo_widget.append("No upcoming trips available") # Optional: keep this in combo
                 trip_combo_widget.disable(); num_people_entry_widget.disable() # Disable number entry if no trips
                 no_trips_message.value = "No future trips available." # Set message text
                 no_trips_message.visible = True # Show the message
                 available_seats_text_widget.value = "Seats Available: -" # Clear seat info

        except mysql.connector.Error as err:
            info("Database Error", f"Could not load trips: {err}")
            trip_combo_widget.append("Error loading trips")
            trip_combo_widget.disable(); num_people_entry_widget.disable()
            no_trips_message.value = "Error loading trips."
            no_trips_message.visible = True
            available_seats_text_widget.value = "Seats Available: -"
        except Exception as e: # Catch other potential errors during trip load
            info("Error", f"Unexpected error loading trips: {e}"); trip_combo_widget.append("Error"); trip_combo_widget.disable(); num_people_entry_widget.disable()

        # --- Reverted: Inner function to handle adding the booking ---
        # --- Inner Function to Add the Booking ---
        def add_booking():
            # Use the 'current_available_seats' calculated when trip was selected
            nonlocal current_available_seats # Access seat count from outer scope
            calculated_cost = 0
            selected_customer = customer_combo_widget.value
            selected_trip = trip_combo_widget.value
            num_people_str = num_people_entry_widget.value.strip() # Read from TextBox
            special_request = special_request_entry_widget.value.strip()
            booking_date_str = booking_date_entry_widget.value # Get automatically set value # Trip date (read-only)

            try:
                # --- Input Validation ---
                is_invalid = False
                num_people = 0

                if not selected_customer or ":" not in selected_customer: is_invalid = True
                # Check if combo disabled OR no trip selected
                if trip_combo_widget.enabled == False or not selected_trip or ":" not in selected_trip: is_invalid = True
                if not num_people_str: is_invalid = True

                if num_people_str:
                    # Validate number of people format (positive integer).
                    if not num_people_str.isdigit() or int(num_people_str) <= 0:
                        is_invalid = True
                    else:
                        num_people = int(num_people_str)

                if not booking_date_str: is_invalid = True
                else:
                    # Validate trip date format again (should be set by trip selection).
                    try: datetime.datetime.strptime(booking_date_str, "%Y-%m-%d").date()
                    except ValueError: is_invalid = True

                if is_invalid:
                     info("Input Error", STATIC_BOOKING_ERROR_MESSAGE)
                     return

                customer_id = int(selected_customer.split(":")[0])
                trip_id = int(selected_trip.split(":")[0]) # Get trip_id from selection

                # --- Check Capacity AGAIN (as a final confirmation) ---
                # --- Re-check Seat Availability (Crucial Check Before Insert) ---
                # Fetch current available seats just before booking to be absolutely sure
                try:
                    cursor.execute("SELECT c.Seats FROM trips t JOIN coaches c ON t.CoachID = c.CoachID WHERE t.TripID = %s", (trip_id,))
                    seat_result = cursor.fetchone(); total_seats = seat_result['Seats'] if seat_result else 0
                    cursor.execute("SELECT SUM(NumberofPeople) as booked FROM bookings WHERE TripID = %s", (trip_id,))
                    booked_result = cursor.fetchone(); booked_seats = booked_result['booked'] or 0
                    final_available_seats = total_seats - booked_seats
                except mysql.connector.Error as db_err:
                    info("Database Error", f"Could not re-verify seat capacity: {db_err}"); return

                # Final check if requested number exceeds available seats.
                if num_people > final_available_seats:
                    info("Input Error", f"Not enough seats available ({final_available_seats} left). Cannot book {num_people}.")
                    # Refresh the display just in case
                    available_seats_text_widget.value = f"Seats Available: {final_available_seats}"
                    current_available_seats = final_available_seats # Update local cache
                    return

                # --- Calculate Booking Cost ---
                cursor.execute("SELECT d.DestinationCost FROM trips t JOIN destinations d ON t.DestinationID = d.DestinationID WHERE t.TripID = %s", (trip_id,))
                cost_result = cursor.fetchone()
                if cost_result and cost_result['DestinationCost'] is not None:
                     calculated_cost = float(cost_result['DestinationCost']) * num_people
                else:
                    info("Error", f"Could not retrieve destination cost for Trip ID {trip_id}."); return

                # --- Insert Booking ---
                # --- Database Insertion ---
                # Inserting trip date into BookingDate column.
                cursor.execute("""
                INSERT INTO bookings (CustomerID, TripID, BookingCost, NumberofPeople, SpecialRequest, BookingDate)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (customer_id, trip_id, calculated_cost, num_people, special_request or None, booking_date_str))
                conn.commit()
                info("Booking Added", f"Booking added. Cost: £{calculated_cost:.2f}")
                go_back(add_booking_win, parent_window)

            except (ValueError, IndexError): info("Input Error", "Invalid selection or number format.")
            except TypeError: info("Error", "Cost calculation error or invalid data.")
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle foreign key constraint violation (invalid Customer/Trip ID).
                if err.errno == 1452: # Foreign key constraint fails
                     info("Database Error", "Invalid Customer or Trip ID selected. Please ensure they exist.")
                else:
                     info("Database Error",f"Error adding booking: {err.msg}")
            except Exception as e: # Catch other potential errors
                info("Error", f"An unexpected error occurred: {e}"); import traceback; traceback.print_exc()

        # Buttons Box (Separate Box at the bottom)
        button_box = Box(add_booking_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text="Add Booking", grid=[0, 0], command=add_booking)
        back_button = PushButton(button_box, text="Back", grid=[1, 0],
                                 command=lambda: go_back(add_booking_win, parent_window))
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR

        # Call update_trip_details initially to set date and seats if a default trip is selected
        # Call initially to set date field if a default trip is selected.
        update_trip_details()
        add_booking_win.show()

    except Exception as e: # Catch errors during window creation itself
        info("Error", f"Failed to open Add Booking window: {e}")
        if add_booking_win: add_booking_win.destroy()
        parent_window.show() # Ensure parent is shown again
# END OF open_add_booking_window

# Modified: Added parent_window parameter
def open_add_coach_window(parent_window):
    parent_window.hide()

    # Local variables for widgets
    add_coach_win = None
    coach_reg_entry = None
    seats_entry = None
    add_button = None
    back_button = None

    COACH_REQUIRED_FIELDS = ("Coach Registration", "Number of Seats")
    STATIC_COACH_ERROR_MESSAGE = f"Please ensure all required fields are entered correctly: [{', '.join(COACH_REQUIRED_FIELDS)}]"

    try:
        add_coach_win = Window(app, title = "Add Coach", width = 400, height = 220, bg = BG_COLOR) # Use app as master
        add_coach_win.tk.resizable(False, False)

        form_box = Box(add_coach_win, layout="grid", width="fill", align="top")

        Text(form_box, text="Enter Coach Details:", color = TEXT_COLOR, size=12, grid=[0,0,2,1], align="top")

        Text(form_box, text = "Coach Registration:", color = TEXT_COLOR, grid=[0,1], align="left")
        coach_reg_entry = TextBox(form_box, width=25, grid=[1,1], align="left")

        Text(form_box, text="Number of Seats:", color = TEXT_COLOR, grid=[0,2], align="left")
        seats_entry = TextBox(form_box, width=10, grid=[1,2], align="left")

        def add_coach():
            try:
                registration = coach_reg_entry.value.strip()
                seats_str = seats_entry.value.strip()

                # --- Improved Validation ---
                is_invalid = False
                if not registration: is_invalid = True
                if not seats_str: is_invalid = True

                # Validate seats is a positive integer
                if seats_str:
                    if not seats_str.isdigit() or int(seats_str) <= 0:
                        is_invalid = True

                if is_invalid:
                    info("Input Error", STATIC_COACH_ERROR_MESSAGE)
                    return
                # --- End Improved Validation ---

                cursor.execute("INSERT INTO coaches (Registration, Seats) VALUES (%s, %s)",
                               (registration, int(seats_str)))
                conn.commit()
                info("Coach Added", "Coach added to the database.")
                # Use go_back to destroy current and show parent
                go_back(add_coach_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle potential duplicate registration
                if err.errno == errorcode.ER_DUP_ENTRY:
                     info("Database Error", "Coach Registration already exists.")
                else:
                     info("Database Error", f"Failed to add coach: {err.msg}")
            except Exception as e:
                info("Error", f"An unexpected error occurred: {e}")


        button_box = Box(add_coach_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text="Add Coach", grid=[0,0], command=add_coach)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command=lambda: go_back(add_coach_win, parent_window)) # MODIFIED
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        add_coach_win.show()

    except Exception as e:
        info("Error", f"Failed to open Add Coach window: {e}")
        if add_coach_win: add_coach_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_add_destination_window(parent_window):
    parent_window.hide()

    # Local variables for widgets
    add_destination_win = None
    destination_name_entry = None
    hotel_name_entry = None
    destination_cost_entry = None
    city_name_entry = None
    days_entry = None
    add_button = None
    back_button = None

    DEST_REQUIRED_FIELDS = ("Destination Name", "Hotel Name", "Destination Cost", "City Name", "Days")
    STATIC_DEST_ERROR_MESSAGE = f"Please ensure all required fields are entered correctly and are valid numbers (Cost >= 0, Days > 0): [{', '.join(DEST_REQUIRED_FIELDS)}]"

    try:
        add_destination_win = Window(app, title = "Add Destination", width = 400, height = 350, bg = BG_COLOR) # Use app as master
        add_destination_win.tk.resizable(False, False)

        form_box = Box(add_destination_win, layout="grid", width="fill", align="top")

        Text(form_box, text = "Enter Destination Details:", color = TEXT_COLOR, size=12, grid=[0,0,2,1], align="top")

        Text(form_box, text = "Destination Name:", color = TEXT_COLOR, grid=[0,1], align="left")
        destination_name_entry = TextBox(form_box, width=25, grid=[1,1], align="left")

        Text(form_box, text = "Hotel Name:", color = TEXT_COLOR, grid=[0,2], align="left")
        hotel_name_entry = TextBox(form_box, width=25, grid=[1,2], align="left")

        Text(form_box, text = "Destination Cost (£):", color = TEXT_COLOR, grid=[0,3], align="left")
        destination_cost_entry = TextBox(form_box, width=15, grid=[1,3], align="left")

        Text(form_box, text="City Name:", color=TEXT_COLOR, grid=[0,4], align="left")
        city_name_entry = TextBox(form_box, width=25, grid=[1,4], align="left")

        Text(form_box, text = "Days:", color = TEXT_COLOR, grid=[0,5], align="left")
        days_entry = TextBox(form_box, width=10, grid=[1,5], align="left")

        def add_destination():
            try:
                name = destination_name_entry.value.strip()
                hotel = hotel_name_entry.value.strip()
                cost_str = destination_cost_entry.value.strip().lstrip('£')
                city = city_name_entry.value.strip()
                days_str = days_entry.value.strip()

                # --- Improved Validation ---
                is_invalid = False
                if not name: is_invalid = True
                if not cost_str: is_invalid = True
                if not city: is_invalid = True
                if not days_str: is_invalid = True

                cost = 0.0
                days = 0
                # Validate cost is a non-negative number
                if cost_str:
                    try:
                        cost = float(cost_str)
                        if cost < 0: is_invalid = True
                    except ValueError: is_invalid = True
                # Validate days is a positive integer
                if days_str:
                    try:
                        days = int(days_str)
                        if days <= 0: is_invalid = True
                    except ValueError: is_invalid = True

                if is_invalid:
                    info("Input Error", STATIC_DEST_ERROR_MESSAGE)
                    return
                # --- End Improved Validation ---

                cursor.execute("""
                INSERT INTO destinations (DestinationName, Hotel, DestinationCost, CityName, Days)
                VALUES (%s, %s, %s, %s, %s)""",
                (name, hotel or None, cost, city, days)) # Use hotel or None
                conn.commit()
                info("Success", "Destination added successfully.")
                # Use go_back to destroy current and show parent
                go_back(add_destination_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle potential duplicate destination name
                if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Destination name might already exist.")
                else: info("Database Error", f"Failed to add Destination: {err.msg}")
            except Exception as e:
                 info("Error", f"An unexpected error occurred: {e}")

        button_box = Box(add_destination_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text = "Add Destination", grid=[0,0], command=add_destination)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command = lambda: go_back(add_destination_win, parent_window)) # MODIFIED
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        add_destination_win.show()

    except Exception as e:
        info("Error", f"Failed to open Add Destination window: {e}")
        if add_destination_win: add_destination_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_add_driver_window(parent_window):
    parent_window.hide()

    # Local variables for widgets
    add_driver_win = None
    driver_name_entry = None
    add_button = None
    back_button = None

    DRIVER_REQUIRED_FIELDS = ("Driver's Full Name",)
    STATIC_DRIVER_ERROR_MESSAGE = f"Please ensure all required fields are entered correctly: [{', '.join(DRIVER_REQUIRED_FIELDS)}]"

    try:
        add_driver_win = Window(app, title = "Add Driver", width = 400, height = 180, bg = BG_COLOR) # Use app as master
        add_driver_win.tk.resizable(False, False)

        form_box = Box(add_driver_win, layout="grid", width="fill", align="top")

        Text(form_box, text = "Enter Driver Details:", color = TEXT_COLOR, size=12, grid=[0,0,2,1], align="top")

        Text(form_box, text = "Driver's Full Name:", color = TEXT_COLOR, grid=[0,1], align="left")
        driver_name_entry = TextBox(form_box, width=25, grid=[1,1], align="left")

        def add_driver():
            try:
                name = driver_name_entry.value.strip()
                # --- Improved Validation ---
                if not name:
                    info("Input Error", STATIC_DRIVER_ERROR_MESSAGE)
                    return
                # --- End Improved Validation ---

                cursor.execute("INSERT INTO drivers (DriverName) VALUES (%s)", (name,))
                conn.commit()
                info("Success", "Driver added successfully.")
                # Use go_back to destroy current and show parent
                go_back(add_driver_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle potential duplicate driver name
                if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Driver name might already exist.")
                else: info("Database Error", f"Failed to add Driver: {err.msg}")
            except Exception as e:
                 info("Error", f"An unexpected error occurred: {e}")

        button_box = Box(add_driver_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text="Add Driver", grid=[0,0], command = add_driver)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command = lambda: go_back(add_driver_win, parent_window)) # MODIFIED
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        add_driver_win.show()

    except Exception as e:
        info("Error", f"Failed to open Add Driver window: {e}")
        if add_driver_win: add_driver_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_add_trip_window(parent_window):
    parent_window.hide()

    # Local variables for widgets
    add_trip_win = None
    coach_combo = None
    driver_combo = None
    destination_combo = None
    date_entry = None
    add_button = None
    back_button = None

    TRIP_REQUIRED_FIELDS = ("Coach", "Driver", "Destination", "Date")
    STATIC_TRIP_ERROR_MESSAGE = f"Please ensure all required fields are selected/entered correctly.\nDate must be YYYY-MM-DD and not in the past: [{', '.join(TRIP_REQUIRED_FIELDS)}]"

    try:
        add_trip_win = Window(app, title="Add Trip", width = 400, height = 320, bg = BG_COLOR) # Use app as master
        add_trip_win.tk.resizable(False, False)

        form_box = Box(add_trip_win, layout="grid", width="fill", align="top")

        Text(form_box, text = "Enter Trip Details: ", color = TEXT_COLOR, size=12, grid=[0,0,2,1], align="top")

        Text(form_box, text = "Coach:", color = TEXT_COLOR, grid=[0,1], align="left")
        coach_combo = Combo(form_box, options=[], width=25, grid=[1,1], align="left")
        try:
            cursor.execute("SELECT CoachID, Registration FROM coaches ORDER BY Registration")
            coaches = cursor.fetchall(); coach_combo.clear(); coach_combo.append("")
            if coaches:
                for coach in coaches: coach_combo.append(f"{coach['CoachID']}: {coach['Registration']}")
            else: coach_combo.append("No coaches available"); coach_combo.disable()
        except mysql.connector.Error as err: info("Database Error", f"Could not load coaches: {err}"); coach_combo.append("Error"); coach_combo.disable()

        Text(form_box, text = "Driver:", color = TEXT_COLOR, grid=[0,2], align="left")
        driver_combo = Combo(form_box, options=[], width=25, grid=[1,2], align="left")
        try:
            cursor.execute("SELECT DriverID, DriverName FROM drivers ORDER BY DriverName")
            drivers = cursor.fetchall(); driver_combo.clear(); driver_combo.append("")
            if drivers:
                for driver in drivers: driver_combo.append(f"{driver['DriverID']}: {driver['DriverName']}")
            else: driver_combo.append("No drivers available"); driver_combo.disable()
        except mysql.connector.Error as err: info("Database Error", f"Could not load drivers: {err}"); driver_combo.append("Error"); driver_combo.disable()

        Text(form_box, text="Destination:", color=TEXT_COLOR, grid=[0,3], align="left")
        destination_combo = Combo(form_box, options=[], width=25, grid=[1,3], align="left")
        try:
            cursor.execute("SELECT DestinationID, DestinationName FROM destinations ORDER BY DestinationName")
            destinations = cursor.fetchall(); destination_combo.clear(); destination_combo.append("")
            if destinations:
                for destination in destinations: destination_combo.append(f"{destination['DestinationID']}: {destination['DestinationName']}")
            else: destination_combo.append("No destinations available"); destination_combo.disable()
        except mysql.connector.Error as err: info("Database Error", f"Could not load destinations: {err}"); destination_combo.append("Error"); destination_combo.disable()

        Text(form_box, text = "Date (YYYY-MM-DD):", color = TEXT_COLOR, grid=[0,4], align="left")
        date_entry = TextBox(form_box, width=15, grid=[1,4], align="left")

        def add_trip():
            try:
                # Get values from local variables
                selected_coach = coach_combo.value
                selected_driver = driver_combo.value
                selected_destination = destination_combo.value
                trip_date_str = date_entry.value.strip() # Use strip()

                # --- Improved Validation ---
                # --- Input Validation ---
                is_invalid = False
                # Check combo selections are valid
                if not selected_coach or ":" not in selected_coach or "available" in selected_coach or "Error" in selected_coach: is_invalid = True
                if not selected_driver or ":" not in selected_driver or "available" in selected_driver or "Error" in selected_driver: is_invalid = True
                if not selected_destination or ":" not in selected_destination or "available" in selected_destination or "Error" in selected_destination: is_invalid = True
                if not trip_date_str: is_invalid = True

                # Validate date format and ensure it's not in the past
                trip_date = None
                if trip_date_str:
                    date_pattern = r"^\d{4}-\d{2}-\d{2}$" # Regex for YYYY-MM-DD
                    if not re.match(date_pattern, trip_date_str):
                        is_invalid = True
                    else:
                        try:
                            trip_date = datetime.datetime.strptime(trip_date_str, "%Y-%m-%d").date()
                            if trip_date < datetime.date.today(): # Check if date is in the past
                                 is_invalid = True
                        except ValueError: # Handles invalid dates like 2023-02-30
                            is_invalid = True

                if is_invalid:
                    info("Input Error", STATIC_TRIP_ERROR_MESSAGE)
                    return

                coach_id = int(selected_coach.split(":")[0])
                driver_id = int(selected_driver.split(":")[0])
                destination_id = int(selected_destination.split(":")[0])
                # --- End Improved Validation ---


                cursor.execute("INSERT INTO trips (CoachID, DriverID, DestinationID, Date) VALUES (%s, %s, %s, %s)",
                               (coach_id, driver_id, destination_id, trip_date_str))
                conn.commit()
                info("Success", "Trip added successfully.")
                # Use go_back to destroy current and show parent
                go_back(add_trip_win, parent_window) # MODIFIED

            except (ValueError, IndexError): info("Input Error", "Invalid selection or ID format.")
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle specific DB errors
                if err.errno == errorcode.ER_DUP_ENTRY: info("Database Error", "Trip details might already exist (e.g., same coach/driver/date).")
                elif err.errno == 1452: info("Database Error", "Invalid Coach, Driver, or Destination ID.") # Foreign key violation
                else: info("Database Error", f"Failed to add Trip: {err.msg}")
            except Exception as e:
                 info("Error", f"An unexpected error occurred: {e}")


        button_box = Box(add_trip_win, layout="grid", width="fill", align="bottom")
        add_button = PushButton(button_box, text = "Add Trip", grid=[0,0], command = add_trip)
        # Modified Back Button Command
        back_button = PushButton(button_box, text = "Back", grid=[1,0],
                                 command = lambda: go_back(add_trip_win, parent_window)) # MODIFIED
        add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        add_trip_win.show()

    except Exception as e:
        info("Error", f"Failed to open Add Trip window: {e}")
        if add_trip_win: add_trip_win.destroy()
        parent_window.show()

#endregion

#region Remove Windows (Using Combo)
# --- MODIFIED FUNCTIONS: Add parent_window argument and use it for Back button ---

# Modified: Added parent_window parameter
def open_remove_booking_window(parent_window):
    parent_window.hide()

    remove_booking_win = None
    remove_booking_combo = None
    remove_button = None
    back_button = None

    try:
        remove_booking_win = Window(app, title="Remove Booking", width=550, height=200, bg=BG_COLOR) # Use app as master
        remove_booking_win.tk.resizable(False, False)
        Text(remove_booking_win, text="Select Booking to remove:", color=TEXT_COLOR)

        remove_booking_combo = Combo(remove_booking_win, options=[""], width='fill')

        # Populate combo with bookings for selection
        try:
            cursor.execute("""
                SELECT b.BookingID, c.FirstName, c.Surname, t.Date, d.DestinationName
                FROM bookings b
                LEFT JOIN customers c ON b.CustomerID = c.CustomerID
                LEFT JOIN trips t ON b.TripID = t.TripID
                LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY b.BookingDate DESC, b.BookingID DESC
            """)
            bookings_list = cursor.fetchall()
            remove_booking_combo.clear()
            remove_booking_combo.append("")
            for bk in bookings_list:
                # Format display string for clarity
                customer_name = f"{bk['FirstName']} {bk['Surname']}" if bk['FirstName'] else "Unknown Customer"
                trip_info = f"{bk['Date']} - {bk['DestinationName']}" if bk['Date'] else "Unknown Trip"
                combo_text = f"{bk['BookingID']}: {customer_name} ({trip_info})"
                remove_booking_combo.append(combo_text)
            if not bookings_list:
                 remove_booking_combo.append("No bookings found")
                 remove_booking_combo.disable()

        except mysql.connector.Error as err:
            info("Database Error", f"Failed to load bookings: {err.msg}")
            remove_booking_combo.append("Error loading data")
            remove_booking_combo.disable()


        def remove_booking():
            selected_booking_text = remove_booking_combo.value
            if not selected_booking_text or ":" not in selected_booking_text:
                info("Input Error", "Please select a valid booking to remove.")
                return

            try:
                # Extract ID from selection
                booking_id = int(selected_booking_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid booking selection format.")
                return

            # Confirm deletion with user
            if not app.yesno("Confirm Deletion", f"Are you sure you want to delete this booking?\n{selected_booking_text}"):
                 return

            try:
                cursor.execute("DELETE FROM bookings WHERE BookingID = %s", (booking_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Booking ID {booking_id} removed.")
                else: info("Error", f"Booking ID {booking_id} could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_booking_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                info("Database Error", f"Failed to remove Booking: {err.msg}")

        button_box = Box(remove_booking_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text="Remove Selected Booking", grid=[0,0], command=remove_booking)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command=lambda: go_back(remove_booking_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        remove_booking_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Booking window: {e}")
        if remove_booking_win: remove_booking_win.destroy()
        parent_window.show()


# Modified: Added parent_window parameter
def open_remove_coach_window(parent_window):
    parent_window.hide()

    remove_coach_win = None
    remove_coach_combo = None
    remove_button = None
    back_button = None

    try:
        remove_coach_win = Window(app, title="Remove Coach", width=400, height=150, bg=BG_COLOR) # Use app as master
        Text(remove_coach_win, text="Select Coach to remove:", color=TEXT_COLOR)

        remove_coach_combo = Combo(remove_coach_win, options=[""], width='fill')

        try:
            cursor.execute("SELECT CoachID, Registration FROM coaches ORDER BY Registration")
            coaches_list = cursor.fetchall()
            remove_coach_combo.clear()
            remove_coach_combo.append("")
            for coach in coaches_list:
                remove_coach_combo.append(f"{coach['CoachID']}: {coach['Registration']}")
            if not coaches_list:
                remove_coach_combo.append("No coaches found")
                remove_coach_combo.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Failed to load coaches: {err.msg}")
            remove_coach_combo.append("Error loading data")
            remove_coach_combo.disable()

        def remove_coach():
            selected_coach_text = remove_coach_combo.value
            if not selected_coach_text or ":" not in selected_coach_text:
                info("Input Error", "Please select a valid coach to remove.")
                return

            try:
                coach_id = int(selected_coach_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid coach selection format.")
                return

            if not app.yesno("Confirm Deletion", f"Delete Coach?\n{selected_coach_text}"): return

            try:
                # Check if coach is assigned to trips before deleting
                cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE CoachID = %s", (coach_id,))
                trip_count_result = cursor.fetchone()
                if trip_count_result and trip_count_result['trip_count'] > 0:
                    # Warn user if coach is in use and ask for confirmation again
                    if not app.yesno("Warning: Coach in Use",
                                     f"This coach is assigned to {trip_count_result['trip_count']} trip(s).\n"
                                     f"Deleting it may cause issues or fail if trips reference it.\n\n"
                                     f"Continue deletion?"):
                        return # Stop if user cancels

                cursor.execute("DELETE FROM coaches WHERE CoachID = %s", (coach_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Coach removed:\n{selected_coach_text}")
                else: info("Error", "Coach could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_coach_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle foreign key constraint violation
                if err.errno == 1451: info("Database Error", "Cannot delete coach: It is currently assigned to one or more trips.\nPlease remove or reassign the trips first.")
                else: info("Database Error", f"Failed to remove coach: {err.msg}")

        button_box = Box(remove_coach_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text="Remove Selected Coach", grid=[0,0], command=remove_coach)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command=lambda: go_back(remove_coach_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        remove_coach_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Coach window: {e}")
        if remove_coach_win: remove_coach_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_remove_customer_window(parent_window):
    parent_window.hide()

    remove_customer_win = None
    remove_customer_combo = None
    remove_button = None
    back_button = None

    try:
        remove_customer_win = Window(app, title="Remove Customer", width=400, height=150, bg=BG_COLOR) # Use app as master
        Text(remove_customer_win, text="Select Customer to remove:", color=TEXT_COLOR)

        remove_customer_combo = Combo(remove_customer_win, options=[""], width='fill')

        try:
            # Use get_all_customers which is already ordered by ID
            customers_list = get_all_customers() # Use helper function
            remove_customer_combo.clear()
            remove_customer_combo.append("")
            if customers_list:
                for cust in customers_list:
                    remove_customer_combo.append(f"{cust['CustomerID']}: {cust['FirstName']} {cust['Surname']}")
            else:
                remove_customer_combo.append("No customers found")
                remove_customer_combo.disable()
        except Exception as err: # Catch potential errors loading data
            info("Error", f"Failed to load customers: {err}")
            remove_customer_combo.append("Error loading data")
            remove_customer_combo.disable()

        def remove_customer():
            selected_customer_text = remove_customer_combo.value
            if not selected_customer_text or ":" not in selected_customer_text:
                info("Input Error", "Please select a valid customer to remove.")
                return

            try:
                customer_id = int(selected_customer_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid customer selection format.")
                return

            if not app.yesno("Confirm Deletion", f"Delete Customer?\n{selected_customer_text}"): return

            try:
                # Check for related bookings before deleting customer
                cursor.execute("SELECT COUNT(*) as booking_count FROM bookings WHERE CustomerID = %s", (customer_id,))
                booking_count_result = cursor.fetchone()
                if booking_count_result and booking_count_result['booking_count'] > 0:
                     # Warn that deleting customer might delete bookings
                     if not app.yesno("Warning: Customer Has Bookings",
                                      f"This customer has {booking_count_result['booking_count']} booking(s).\n"
                                      f"Deleting the customer will likely delete their bookings too (if cascading deletes are enabled).\n\n"
                                      f"Continue?"):
                         return # Stop if user cancels

                cursor.execute("DELETE FROM customers WHERE CustomerID = %s", (customer_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Customer removed:\n{selected_customer_text}")
                else: info("Error", "Customer could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_customer_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle FK error
                if err.errno == 1451: info("Database Error", "Cannot delete customer: They have existing bookings.\nPlease remove their bookings first.")
                else: info("Database Error", f"Failed to remove customer: {err.msg}")

        button_box = Box(remove_customer_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text="Remove Selected Customer", grid=[0,0], command=remove_customer)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command= lambda: go_back(remove_customer_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR;  back_button.text_color = BUTTON_TEXT_COLOR
        remove_customer_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Customer window: {e}")
        if remove_customer_win: remove_customer_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_remove_destination_window(parent_window):
    parent_window.hide()

    remove_destination_win = None
    remove_destination_combo = None
    remove_button = None
    back_button = None

    try:
        remove_destination_win = Window(app, title = "Remove Destination", width = 400, height = 150, bg=BG_COLOR) # Use app as master
        Text(remove_destination_win, text = "Select Destination to remove:", color = TEXT_COLOR)

        remove_destination_combo = Combo(remove_destination_win, options=[""], width='fill')

        try:
            cursor.execute("SELECT DestinationID, DestinationName FROM destinations ORDER BY DestinationName")
            destinations_list = cursor.fetchall()
            remove_destination_combo.clear()
            remove_destination_combo.append("")
            for dest in destinations_list:
                remove_destination_combo.append(f"{dest['DestinationID']}: {dest['DestinationName']}")
            if not destinations_list:
                remove_destination_combo.append("No destinations found")
                remove_destination_combo.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Failed to load destinations: {err.msg}")
            remove_destination_combo.append("Error loading data")
            remove_destination_combo.disable()


        def remove_destination():
            selected_destination_text = remove_destination_combo.value
            if not selected_destination_text or ":" not in selected_destination_text:
                info("Input Error", "Please select a valid destination to remove.")
                return

            try:
                destination_id = int(selected_destination_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid destination selection format.")
                return

            if not app.yesno("Confirm Deletion", f"Delete Destination?\n{selected_destination_text}"): return

            try:
                # Check for related trips before deleting
                cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DestinationID = %s", (destination_id,))
                trip_count_result = cursor.fetchone()
                if trip_count_result and trip_count_result['trip_count'] > 0:
                    # Warn user if destination is in use
                    if not app.yesno("Warning: Destination in Use",
                                     f"This destination is used in {trip_count_result['trip_count']} trip(s).\n"
                                     f"Deleting it may cause issues or fail if trips reference it.\n\n"
                                     f"Continue deletion?"):
                        return

                cursor.execute("DELETE FROM destinations WHERE DestinationID = %s", (destination_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Destination removed:\n{selected_destination_text}")
                else: info("Error", "Destination could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_destination_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle FK constraint violation
                if err.errno == 1451: info("Database Error", "Cannot delete destination: It is currently used in one or more trips.\nPlease remove or reassign the trips first.")
                else: info("Database Error", f"Failed to remove destination: {err.msg}")

        button_box = Box(remove_destination_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text="Remove Selected Destination", grid=[0,0], command=remove_destination)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command = lambda: go_back(remove_destination_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        remove_destination_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Destination window: {e}")
        if remove_destination_win: remove_destination_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_remove_driver_window(parent_window):
    parent_window.hide()

    remove_driver_win = None
    remove_driver_combo = None
    remove_button = None
    back_button = None

    try:
        remove_driver_win = Window(app, title = "Remove Driver", width = 400, height = 150, bg = BG_COLOR) # Use app as master
        Text(remove_driver_win, text="Select Driver to remove:", color = TEXT_COLOR)

        remove_driver_combo = Combo(remove_driver_win, options=[""], width='fill')

        try:
            cursor.execute("SELECT DriverID, DriverName FROM drivers ORDER BY DriverName")
            drivers_list = cursor.fetchall()
            remove_driver_combo.clear()
            remove_driver_combo.append("")
            for driver in drivers_list:
                remove_driver_combo.append(f"{driver['DriverID']}: {driver['DriverName']}")
            if not drivers_list:
                remove_driver_combo.append("No drivers found")
                remove_driver_combo.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Failed to load drivers: {err.msg}")
            remove_driver_combo.append("Error loading data")
            remove_driver_combo.disable()

        def remove_driver():
            selected_driver_text = remove_driver_combo.value
            if not selected_driver_text or ":" not in selected_driver_text:
                info("Input Error", "Please select a valid driver to remove.")
                return

            try:
                driver_id = int(selected_driver_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid driver selection format.")
                return

            if not app.yesno("Confirm Deletion", f"Delete Driver?\n{selected_driver_text}"): return

            try:
                # Check for related trips before deleting
                cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DriverID = %s", (driver_id,))
                trip_count_result = cursor.fetchone()
                if trip_count_result and trip_count_result['trip_count'] > 0:
                     # Warn user if driver is assigned to trips
                     if not app.yesno("Warning: Driver Assigned to Trips",
                                      f"This driver is assigned to {trip_count_result['trip_count']} trip(s).\n"
                                      f"Deleting them may cause issues or fail if trips reference them.\n\n"
                                      f"Continue deletion?"):
                         return

                cursor.execute("DELETE FROM drivers WHERE DriverID = %s", (driver_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Driver removed:\n{selected_driver_text}")
                else: info("Error", "Driver could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_driver_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                 conn.rollback()
                 # Handle FK constraint violation
                 if err.errno == 1451: info("Database Error", "Cannot delete driver: They are currently assigned to one or more trips.\nPlease remove or reassign the trips first.")
                 else: info("Database Error", f"Failed to remove driver: {err.msg}")

        button_box = Box(remove_driver_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text = "Remove Selected Driver", grid=[0,0], command = remove_driver)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command=lambda: go_back(remove_driver_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        remove_driver_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Driver window: {e}")
        if remove_driver_win: remove_driver_win.destroy()
        parent_window.show()

# Modified: Added parent_window parameter
def open_remove_trip_window(parent_window):
    parent_window.hide()

    remove_trip_win = None
    remove_trip_combo = None
    remove_button = None
    back_button = None

    try:
        remove_trip_win = Window(app, title="Remove Trip", width=450, height=150, bg=BG_COLOR) # Use app as master
        Text(remove_trip_win, text="Select Trip to remove:", color=TEXT_COLOR)

        remove_trip_combo = Combo(remove_trip_win, options=[""], width='fill')

        try:
            # Fetch trips with destination details for identification
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName FROM trips t
                LEFT JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY t.Date DESC, t.TripID DESC
            """)
            trips_list = cursor.fetchall()
            remove_trip_combo.clear()
            remove_trip_combo.append("")
            for trip in trips_list:
                combo_text = f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName'] or 'Unknown Destination'}"
                remove_trip_combo.append(combo_text)
            if not trips_list:
                 remove_trip_combo.append("No trips found")
                 remove_trip_combo.disable()

        except mysql.connector.Error as err:
            info("Database Error", f"Failed to load trips: {err.msg}")
            remove_trip_combo.append("Error loading data")
            remove_trip_combo.disable()

        def remove_trip():
            selected_trip_text = remove_trip_combo.value
            if not selected_trip_text or ":" not in selected_trip_text:
                info("Input Error", "Please select a valid trip to remove.")
                return

            try:
                trip_id = int(selected_trip_text.split(":")[0])
            except (ValueError, IndexError):
                info("Input Error", "Invalid trip selection format.")
                return

            if not app.yesno("Confirm Deletion", f"Delete Trip?\n{selected_trip_text}"): return # Single confirmation first

            try:
                # Check for related bookings before deleting trip
                cursor.execute("SELECT COUNT(*) as booking_count FROM bookings WHERE TripID = %s", (trip_id,))
                booking_count_result = cursor.fetchone()
                if booking_count_result and booking_count_result['booking_count'] > 0:
                    # Warn that deleting trip might delete bookings
                    if not app.yesno("Warning: Trip Has Bookings",
                                     f"This trip has {booking_count_result['booking_count']} booking(s).\n"
                                     f"Deleting the trip will likely delete its bookings too (if cascading deletes are enabled).\n\n"
                                     f"Continue?"):
                        return
                    # cursor.execute("DELETE FROM bookings WHERE TripID = %s", (trip_id,)) # Uncomment if ON DELETE CASCADE not set in DB

                cursor.execute("DELETE FROM trips WHERE TripID = %s", (trip_id,))
                conn.commit()
                if cursor.rowcount > 0: info("Success", f"Trip removed:\n{selected_trip_text}")
                else: info("Error", "Trip could not be removed (might already be deleted).")
                # Use go_back to destroy current and show parent
                go_back(remove_trip_win, parent_window) # MODIFIED
            except mysql.connector.Error as err:
                conn.rollback()
                # Handle FK error
                if err.errno == 1451: info("Database Error", "Cannot delete trip: It has existing bookings.\nPlease remove the bookings first.")
                else: info("Database Error", f"Failed to remove trip: {err.msg}")

        button_box = Box(remove_trip_win, layout="grid", width="fill", align="bottom")
        remove_button = PushButton(button_box, text="Remove Selected Trip", grid=[0,0], command=remove_trip)
        # Modified Back Button Command
        back_button = PushButton(button_box, text="Back", grid=[1,0],
                                 command=lambda: go_back(remove_trip_win, parent_window)) # MODIFIED
        remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
        back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
        remove_trip_win.show()

    except Exception as e:
        info("Error", f"Failed to open Remove Trip window: {e}")
        if remove_trip_win: remove_trip_win.destroy()
        parent_window.show()

#endregion Remove Windows


# --- Query Window ---
# Modified: Added parent_window parameter and use it for Back button
def open_query_window(parent_window):
    """Opens a window for executing various predefined database queries (Admin only)."""
    parent_window.hide() # Hide the calling menu

    global query_window # Still use global for simplicity, though class structure would be better
    # Uses global for simplicity, allows nested functions to potentially access if needed.
    query_window = Window(app, title="Database Queries (Admin)", width=800, height=600, bg=BG_COLOR) # Use app as master
    Text(query_window, text="Select a Query:", color=TEXT_COLOR)

    # --- Query 1: Passengers by Trip --- (MODIFIED for Grid View)
    # --- Query 1: Passengers on a Specific Trip ---
    def lincoln_passengers():
        """Opens a sub-window to select a trip, then displays its passenger list."""
        selection_window = Window(query_window, title="Select Trip for Passenger List", width=450, height=200, bg=BG_COLOR)
        Text(selection_window, text="Select Trip:", color=TEXT_COLOR)
        trip_query_combo = Combo(selection_window, options=[], width="fill")

        # Populate trip combo
        try: # Populate Trip ComboBox
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY t.Date DESC, d.DestinationName
            """)
            trips_for_combo = cursor.fetchall()
            trip_query_combo.clear(); trip_query_combo.append("")
            if trips_for_combo:
                for trip in trips_for_combo:
                    trip_query_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
            else:
                trip_query_combo.append("No trips available")
                trip_query_combo.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trips for query: {err}"); selection_window.destroy(); return

        # Inner function to run query and display results
        def run_passenger_query():
            selected_trip_text = trip_query_combo.value
            if not selected_trip_text or ":" not in selected_trip_text:
                info("Input Error", "Please select a trip.")
                return

            try:
                # Extract Trip ID and Destination Name from the combo text
                # Extract trip ID and description
                parts = selected_trip_text.split(":", 1)
                trip_id = int(parts[0])
                trip_desc = parts[1].strip() # Contains "YYYY-MM-DD - DestinationName"
                dest_name_parts = trip_desc.split(" - ", 1)
                destination_name = dest_name_parts[1] if len(dest_name_parts) > 1 else "Selected Trip"

                # Fetch passenger data for the selected trip
                cursor.execute("""
                    SELECT c.CustomerID, c.FirstName, c.Surname, b.NumberofPeople
                    FROM customers c
                    JOIN bookings b ON c.CustomerID = b.CustomerID
                    WHERE b.TripID = %s
                    ORDER BY c.Surname, c.FirstName
                """, (trip_id,))
                passengers = cursor.fetchall()

                # --- Create Grid View Window ---
                # Create results window
                result_window = Window(query_window, title=f"Passengers - Trip {trip_id}: {destination_name}", width=600, height=450, bg=BG_COLOR)

                # Main container for the grid
                grid_container = Box(result_window, width="fill", height="fill", border=1) # Use fill for height
                grid_box = Box(grid_container, layout="grid", width="fill", align="top")

                # Back button container
                back_button_box = Box(result_window, width="fill", align="bottom")

                headers = ["ID", "First Name", "Surname", "# People"]
                data_keys = ["CustomerID", "FirstName", "Surname", "NumberofPeople"]

                # Create Headers
                # Add headers
                for col, header in enumerate(headers):
                    Text(grid_box, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True, align="left")

                # Create Data Rows
                # Add data rows
                if passengers:
                    for row, passenger_dict in enumerate(passengers, start=1):
                        for col, key in enumerate(data_keys):
                            data_to_display = str(passenger_dict.get(key, ''))
                            Text(grid_box, text=data_to_display, grid=[col, row], color=TEXT_COLOR, size=10, align="left")
                else:
                    # Display message within the grid box if no results
                    # Span the message across the header width if no trips found
                    Text(grid_box, text="No passengers booked on this trip.", color=TEXT_COLOR, grid=[0, 1, len(headers), 1], align="left")

                # Add a single Back/Close button
                close_button = PushButton(back_button_box, text="Close", command=result_window.destroy, align="right")
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR

                result_window.show()
                selection_window.destroy() # Close the selection window # Close selection window after showing results

            except (ValueError, IndexError):
                info("Input Error", "Invalid trip selection format.")
            except mysql.connector.Error as err:
                info("Database Error", f"Error fetching passenger data: {err}")
            except Exception as e:
                 info("Error", f"An unexpected error occurred displaying passengers: {e}")
                 import traceback; traceback.print_exc()

        btn_box = Box(selection_window, layout="grid", width="fill", align="bottom")
        ok_button = PushButton(btn_box, text="Show Passengers", grid=[0,0], command=run_passenger_query)
        cancel_button = PushButton(btn_box, text="Cancel", grid=[1,0], command=selection_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        selection_window.show()
    # END of lincoln_passengers

    # --- Query 2: Available trips ---
    # --- Query 2: Available Upcoming Trips (MODIFIED TO USE GRID) --- 
    def available_trips():
        """Queries and displays upcoming trips with calculated available seats in a grid."""
        try:
            # Fetches trips on or after today's date.
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName, d.CityName, c.Seats,
                       COALESCE((SELECT SUM(b.NumberofPeople) FROM bookings b WHERE b.TripID = t.TripID), 0) AS BookedSeats
                FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                JOIN coaches c ON t.CoachID = c.CoachID
                WHERE t.Date >= CURDATE()
                ORDER BY t.Date ASC
            """)
            trips = cursor.fetchall()

            # Create results window
            result_window = Window(query_window, title="Available Trips (Upcoming)", width=700, height=450, bg=BG_COLOR) # Increased width slightly
            grid_container = Box(result_window, width="fill", height="fill", border=1)
            grid_box = Box(grid_container, layout="grid", width="fill", align="top")
            back_button_box = Box(result_window, width="fill", align="bottom")

            headers = ["ID", "Date", "Destination", "City", "Seats Avail."]
            # Define data keys, adding a temporary key for the calculated available seats
            data_keys = ["TripID", "Date", "DestinationName", "CityName", "AvailableSeats"]

            # Add headers
            for col, header in enumerate(headers):
                Text(grid_box, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True, align="left")

            if trips:
                # Add data rows
                for row, trip_dict in enumerate(trips, start=1):
                    # Calculate available seats and add to the dictionary for this row
                    available = trip_dict['Seats'] - trip_dict['BookedSeats']
                    trip_dict['AvailableSeats'] = available # Add the calculated value

                    for col, key in enumerate(data_keys):
                        raw_value = trip_dict.get(key, '')
                        # Format data for display
                        if isinstance(raw_value, datetime.date):
                            data_to_display = raw_value.strftime('%Y-%m-%d')
                        elif isinstance(raw_value, (int, float)):
                             data_to_display = str(raw_value)
                        elif raw_value is None:
                            data_to_display = ""
                        else:
                            data_to_display = str(raw_value)

                        Text(grid_box, text=data_to_display, grid=[col, row], color=TEXT_COLOR, size=10, align="left")
            else:
                # Span the message across the header width if no trips found
                Text(grid_box, text="No upcoming trips currently available.", color=TEXT_COLOR, grid=[0, 1, len(headers), 1], align="left")

            close_button = PushButton(back_button_box, text="Close", command=result_window.destroy, align="right")
            close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR

            result_window.show()

        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching available trip data: {err}")
            # Optionally display error in the window if it exists
            try:
                if result_window and result_window.visible:
                    clear_box(grid_box) # Clear previous content attempt
                    Text(grid_box, text=f"Database Error:\n{err}", color="red", size=12, grid=[0, 0])
            except NameError: # Handle case where result_window wasn't created yet
                 pass
        except Exception as e:
            info("Error", f"An unexpected error occurred displaying available trips: {e}")
            try:
                 if result_window and result_window.visible:
                    clear_box(grid_box)
                    Text(grid_box, text=f"Unexpected Error:\n{e}", color="red", size=12, grid=[0, 0])
            except NameError:
                 pass
            import traceback; traceback.print_exc()


    # --- Query 3: Customers by Postcode ---
    # --- Query 3: Customers by Postcode Area ---
    def postcode_customers():
        """Opens a sub-window for postcode input, displays matching customers with pagination."""
        postcode_window = Window(query_window, title="Enter Postcode Area", width=300, height=150, bg=BG_COLOR)
        Text(postcode_window, text="Enter Postcode Prefix (e.g., 'SW1A'):", color=TEXT_COLOR)
        postcode_entry = TextBox(postcode_window, width='fill')
        postcode_entry.focus()

        # --- Helper function to display a specific page of postcode results ---
        def display_postcode_results(postcode, page, result_window, grid_box, pagination_box):
            """Fetches and displays a page of customers matching the postcode prefix."""
            try:
                offset = page * query_records_per_page # Uses specific page size for this query
                postcode_like = postcode + '%' # Prepares for LIKE query, case-insensitive

                # Get total count for pagination
                # Count total matching records for pagination
                count_query = "SELECT COUNT(*) as total FROM customers WHERE UPPER(Postcode) LIKE %s"
                cursor.execute(count_query, (postcode_like,))
                total_records = cursor.fetchone()['total']
                total_pages = (total_records + query_records_per_page - 1) // query_records_per_page

                # Fetch records for the current page
                # Fetch data for the current page
                data_query = """
                    SELECT CustomerID, FirstName, Surname, AddressLine1, Postcode
                    FROM customers
                    WHERE UPPER(Postcode) LIKE %s /* Case-insensitive match */
                    ORDER BY Postcode, Surname
                    LIMIT %s OFFSET %s /* Pagination */
                """
                cursor.execute(data_query, (postcode_like, query_records_per_page, offset))
                customers = cursor.fetchall()

                # Clear previous results
                clear_box(grid_box)
                clear_box(pagination_box)

                if customers:
                    headers = ["ID", "Name", "Address", "Postcode"]
                    data_keys = ["CustomerID", "Name", "AddressLine1", "Postcode"] # 'Name' generated below

                    # Create Headers
                    for col, header in enumerate(headers):
                        Text(grid_box, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True, align="left")

                    # Create Data Rows
                    for row, customer_dict in enumerate(customers, start=1):
                        # Combine first/last name for display
                        full_name = f"{customer_dict.get('FirstName', '')} {customer_dict.get('Surname', '')}"
                        customer_dict['Name'] = full_name # Add to dict for easy access via data_keys

                        for col, key in enumerate(data_keys):
                            data_to_display = str(customer_dict.get(key, ''))
                            Text(grid_box, text=data_to_display, grid=[col, row], color=TEXT_COLOR, size=10, align="left")
                else:
                    # Display message within the grid box if no results on this page (shouldn't happen if total_records > 0)
                    if page == 0: # Only show "No customers" on first page attempt
                       Text(grid_box, text=f"No customers found starting with postcode '{postcode}'.", color=TEXT_COLOR, grid=[0, 1, 4, 1], align="left")

                # --- Create Pagination Controls ---
                # Add Pagination Controls
                if page > 0:
                    prev_button = PushButton(pagination_box, text="<< Previous",
                                             # Lambda calls this same display function for the previous page
                                             command=lambda p=page: display_postcode_results(postcode, p - 1, result_window, grid_box, pagination_box),
                                             grid=[0, 0], align="left")
                    prev_button.bg = BUTTON_BG_COLOR; prev_button.text_color = BUTTON_TEXT_COLOR

                Text(pagination_box, text=f"Page {page + 1} of {max(1, total_pages)}", grid=[1, 0], align="left", color=TEXT_COLOR)

                if page < total_pages - 1:
                    next_button = PushButton(pagination_box, text="Next >>",
                                             # Lambda calls this display function for the next page
                                             command=lambda p=page: display_postcode_results(postcode, p + 1, result_window, grid_box, pagination_box),
                                             grid=[2, 0], align="left")
                    next_button.bg = BUTTON_BG_COLOR; next_button.text_color = BUTTON_TEXT_COLOR

            except mysql.connector.Error as err:
                clear_box(grid_box); clear_box(pagination_box)
                Text(grid_box, text=f"Database Error:\n{err}", color="red", size=12, grid=[0, 0])
                print(f"DB Error displaying postcode results: {err}")
            except Exception as e:
                clear_box(grid_box); clear_box(pagination_box)
                Text(grid_box, text=f"An unexpected error occurred:\n{e}", color="red", size=12, grid=[0, 0])
                import traceback; traceback.print_exc()

        # --- Inner function to trigger postcode query and open results window ---
        def run_postcode_query():
            postcode = postcode_entry.value.strip().upper()
            if not postcode: info("Input Error", "Please enter a postcode area."); return

            # Create the results window structure *before* fetching data
            result_window = Window(query_window, title=f"Customers in {postcode}*", width=700, height=500, bg=BG_COLOR) # Adjusted size
            grid_container = Box(result_window, width="fill", height="fill", border=1) # Use fill for height
            grid_box = Box(grid_container, layout="grid", width="fill", align="top")
            pagination_box = Box(result_window, layout="grid", width="fill", align="bottom")
            back_button_box = Box(result_window, width="fill", align="bottom") # Box for the back button

            # Call the display function for the first page
            # Call helper to display the first page of results
            display_postcode_results(postcode, 0, result_window, grid_box, pagination_box)

            # Add a single Back/Close button
            back_button = PushButton(back_button_box, text="Back to Queries", command=result_window.destroy, align="right")
            # Back button command needed adjustment from original, just use destroy
            # back_button = PushButton(back_button_box, text="Close Results", command=result_window.destroy, align="right")
            back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR

            result_window.show()
            postcode_window.destroy() # Close input window


        btn_box = Box(postcode_window, layout="grid", width="fill", align="bottom")
        ok_button = PushButton(btn_box, text="Find Customers", grid=[0,0], command=run_postcode_query)
        cancel_button = PushButton(btn_box, text="Cancel", grid=[1,0], command=postcode_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        postcode_window.show()

    # --- Query 4: Trip Income ---
    # --- Query 4: Calculate Total Income for a Trip ---
    def trip_income_window():
        """Opens a sub-window to select a trip, then calculates and displays its total booking income."""
        income_window = Window(query_window, title = "Calculate Trip Income", width = 400, height = 200, bg = BG_COLOR)
        Text(income_window, text="Select Trip:", color=TEXT_COLOR) # Changed to Combo
        trip_income_combo = Combo(income_window, options=[], width='fill')

        # Populate trip combo
        try: # Populate Trip ComboBox
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                ORDER BY t.Date DESC, d.DestinationName
            """)
            trips_for_income = cursor.fetchall()
            trip_income_combo.clear(); trip_income_combo.append("")
            if trips_for_income:
                for trip in trips_for_income:
                    trip_income_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
            else:
                trip_income_combo.append("No trips available")
                trip_income_combo.disable()
        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trips for income: {err}"); income_window.destroy(); return

        # Inner function to calculate and display income
        def calculate_income():
            selected_trip_income = trip_income_combo.value
            if not selected_trip_income or ":" not in selected_trip_income:
                info("Input Error", "Please select a trip.")
                return
            try:
                trip_id = int(selected_trip_income.split(":")[0])
                # Query to SUM BookingCost for the selected trip
                cursor.execute("SELECT SUM(b.BookingCost) AS TotalIncome FROM bookings b WHERE b.TripID = %s", (trip_id,))
                result = cursor.fetchone()
                # Get sum, default to 0 if null
                income = result['TotalIncome'] if result and result['TotalIncome'] is not None else 0
                # Display result in info popup, formatted as currency
                info(f"Income for Trip {trip_id}", f"Total Booking Income: £{income:.2f}")
            except (ValueError, IndexError): info("Input Error", "Invalid trip selection.")
            except mysql.connector.Error as err: info("Database Error", f"Error calculating income: {err}")

        btn_box = Box(income_window, layout="grid", width="fill", align="bottom")
        calculate_button = PushButton(btn_box, text = "Calculate Income", grid=[0,0], command = calculate_income)
        cancel_button = PushButton(btn_box, text = "Close", grid=[1,0], command = income_window.destroy) # Close selection window
        calculate_button.bg = BUTTON_BG_COLOR; calculate_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        income_window.show()

    # --- Buttons for each query ---
    # --- Buttons on the main Query Window to trigger each query ---
    query_button_box = Box(query_window, layout="grid", width="fill")
    passengers_button = PushButton(query_button_box, text="Passengers by Trip", grid=[0,0], width=20, command=lincoln_passengers)
    trips_button = PushButton(query_button_box, text="Available Trips", grid=[1,0], width=20, command=available_trips)
    postcode_button = PushButton(query_button_box, text="Customers by Postcode", grid=[0,1], width=20, command=postcode_customers)
    income_button = PushButton(query_button_box, text = "Calculate Trip Income", grid=[1,1], width=20, command = trip_income_window)
    for button in query_button_box.children:
         if isinstance(button, PushButton): button.bg = BUTTON_BG_COLOR; button.text_color = BUTTON_TEXT_COLOR

    # Modified Back Button to use go_back with the passed parent_window
    # Back button to return to the menu from which Queries was opened (passed as parent_window)
    back_button = PushButton(query_window, text="Back to Menu",
                             command=lambda: go_back(query_window, parent_window), # MODIFIED
                             align="bottom")
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    query_window.show()

# --- Login and Main App ---
def check_admin_login():
    """Validates hardcoded admin credentials."""
    if username_entry.value.lower() == "admin" and password_entry.value == "admin":
        open_admin_main_window()
    else:
        info("Login Failed", "Incorrect username or password.")
        password_entry.value = "" # Clear password field on failure


def open_admin_login_window():
    """Opens the admin login prompt."""
    app.hide()
    global admin_login_window, username_entry, password_entry
    admin_login_window = Window(app, title="Admin Login", width=300, height=200, bg=BG_COLOR)
    Text(admin_login_window, text="Username:", color=TEXT_COLOR)
    username_entry = TextBox(admin_login_window, width="fill")
    Text(admin_login_window, text="Password:", color=TEXT_COLOR)
    password_entry = TextBox(admin_login_window, hide_text=True, width="fill") # hide_text masks password
    username_entry.focus() # Set focus to username field # Set focus for convenience

    button_box = Box(admin_login_window, layout="grid", width="fill")
    login_button = PushButton(button_box, text="Login", grid=[0,0], command=check_admin_login)
    # Back button closes login and shows main app window
    back_button = PushButton(button_box, text="Back", grid=[1,0],
                             command=lambda: go_back(admin_login_window, app)) # Use go_back correctly # Back to main app screen

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

# Configure grid weights to make the logo area expand vertically on resize.
app.tk.grid_columnconfigure(0, weight=1)
app.tk.grid_columnconfigure(1, weight=1)
app.tk.grid_rowconfigure(0, weight=1) # Logo area gets more space # Logo row expands
app.tk.grid_rowconfigure(1, weight=0) # Title row fixed
app.tk.grid_rowconfigure(2, weight=0) # Button row fixed

# --- Global Window Variable Declarations ---
# Define window variables globally *before* they might be used in lambdas/comparisons
# Define window variables globally. Initialized to None.
# Necessary for functions that need to show/hide/destroy these windows from different scopes.
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
# Add/Remove windows are temporary, no need for global refs unless reused

# --- Start the GUI Event Loop ---
app.display()

# --- Cleanup: Close Database Connection on Exit ---
# --- Close Connection ---
# Ensures the database connection is closed when the application window is closed.
if conn and conn.is_connected():
    cursor.close()
    conn.close()
    print("Database connection closed.")