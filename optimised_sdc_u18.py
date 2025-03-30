import mysql.connector
from guizero import App, Text, Picture, PushButton, Box, TextBox, Combo, Window, ListBox, info # Added Window, ListBox, info
from mysql.connector import errorcode
import datetime

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
    # Use dictionary=True for easier access by column name
    cursor = conn.cursor(dictionary=True)
except mysql.connector.Error as err:
    # Use guizero's info box for errors if App is available, otherwise print
    try:
        # Create a temporary App just to show the error if the main one isn't ready
        temp_app = App(title="DB Connection Error", visible=False)
        info("Database Connection Error", f"Failed to connect to database: {err}")
        temp_app.destroy()
    except Exception: # If guizero itself fails
         print(f"CRITICAL DATABASE ERROR: {err}")
    exit() # Stop the script if DB connection fails


# --- Pagination Globals ---
current_page = 0
records_per_page = 15 # Adjusted for potentially smaller window sizes


# --- Helper Functions from Example ---

def clear_box(box):
    # Safely destroy widgets - make a copy of the list to iterate over
    # as destroying widgets modifies the original list
    widgets_to_destroy = box.children[:]
    for widget in widgets_to_destroy:
        widget.destroy()

def create_search_box(parent_box, table_name, table_view_box, pagination_box):
    """Creates a search interface for tables"""
    # Use a Box to contain search elements horizontally
    search_container = Box(parent_box, align="top", width="fill", layout="grid")

    Text(search_container, text="Search:", grid=[0,0], align="left", color=TEXT_COLOR)
    search_input = TextBox(search_container, width=25, grid=[1,0], align="left") # Adjusted width

    # Define searchable fields for YOUR tables
    search_fields = {
        "trips": ["TripID", "CoachID", "DriverID", "DestinationID", "Date"],
        "destinations": ["DestinationID", "DestinationName", "Hotel", "CityName", "Days"],
        "coaches": ["CoachID", "Registration", "Seats"],
        "drivers": ["DriverID", "DriverName"], # Use DriverName as in your schema
        "customers": ["CustomerID", "FirstName", "Surname", "Email", "City", "Postcode", "PhoneNumber"],
        "bookings": ["BookingID", "CustomerID", "TripID", "BookingCost", "NumberOfPeople", "SpecialRequest", "BookingDate"]
    }

    # Ensure the table_name exists in search_fields
    if table_name not in search_fields:
        # Handle case where table might not be searchable or is misspelled
        Text(search_container, text="Search not available for this table.", grid=[2,0], align="left", color="red")
        return # Stop if no fields defined

    Text(search_container, text=" by:", grid=[2,0], align="left", color=TEXT_COLOR) # Added colon for clarity
    field_dropdown = Combo(search_container, options=search_fields[table_name], grid=[3,0], align="left")
    # Set default selection if options exist
    if search_fields[table_name]:
        field_dropdown.value = search_fields[table_name][0]

    # Search button
    search_button = PushButton(search_container, text="Search", grid=[4,0], align="left",
               command=lambda: fetch_and_display_table(table_name, table_view_box, pagination_box,
                                                     search_term=search_input.value,
                                                     search_field=field_dropdown.value))
    search_button.bg = BUTTON_BG_COLOR
    search_button.text_color = BUTTON_TEXT_COLOR


def fetch_and_display_table(table_name, table_box, pagination_box, page=0, search_term=None, search_field=None):
    global current_page
    current_page = page
    offset = page * records_per_page

    base_query = ""
    select_query = ""
    columns = []
    where_clause = ""

    try:
        # --- Define Queries and Columns for YOUR specific tables ---
        if table_name == "bookings":
            # More complex query joining tables for better display
            select_query = """
                SELECT b.BookingID, c.CustomerID, CONCAT(c.FirstName, ' ', c.Surname) as CustomerName,
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
            # Define WHERE clause logic specifically for bookings if needed (using aliases)
            if search_term and search_field:
                 # Map user-friendly search field names to actual DB columns/aliases if they differ
                field_map = {
                    "BookingID": "b.BookingID", "CustomerID": "b.CustomerID", "TripID": "b.TripID",
                    "BookingCost": "b.BookingCost", "NumberOfPeople": "b.NumberofPeople",
                    "SpecialRequest": "b.SpecialRequest", "BookingDate": "b.BookingDate",
                    "CustomerName": "CONCAT(c.FirstName, ' ', c.Surname)", # Example for searching concatenated field
                    "DestinationName": "d.DestinationName" # Example
                }
                db_field = field_map.get(search_field, search_field) # Default to passed field if not in map
                # Use placeholders for security against SQL injection
                where_clause = f" WHERE {db_field} LIKE %s"
                search_value = f"%{search_term}%" # Prepare the value for LIKE


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
            if search_term and search_field:
                field_map = {
                    "TripID": "t.TripID", "CoachID": "t.CoachID", "DriverID": "t.DriverID",
                    "DestinationID": "t.DestinationID", "Date": "t.Date", "CoachReg": "c.Registration",
                    "DriverName": "dr.DriverName", "DestinationName": "d.DestinationName"
                }
                db_field = field_map.get(search_field, search_field)
                where_clause = f" WHERE {db_field} LIKE %s"
                search_value = f"%{search_term}%"

        elif table_name == "customers":
             select_query = "SELECT CustomerID, FirstName, Surname, Email, AddressLine1, AddressLine2, City, Postcode, PhoneNumber, SpecialNotes"
             base_query = f"FROM {table_name}"
             # Define columns manually for desired order/names
             columns = ["ID", "First Name", "Surname", "Email", "Address 1", "Address 2", "City", "Postcode", "Phone", "Notes"]
             if search_term and search_field:
                 # Ensure search_field is a valid column name for security
                 valid_columns = ["CustomerID", "FirstName", "Surname", "Email", "AddressLine1", "AddressLine2", "City", "Postcode", "PhoneNumber", "SpecialNotes"]
                 if search_field in valid_columns:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     search_value = f"%{search_term}%"
                 else:
                     info("Search Error", "Invalid search field selected.")
                     search_term = None # Prevent invalid search

        elif table_name == "coaches":
             select_query = "SELECT CoachID, Registration, Seats"
             base_query = f"FROM {table_name}"
             columns = ["ID", "Registration", "Seats"]
             if search_term and search_field:
                 valid_columns = ["CoachID", "Registration", "Seats"]
                 if search_field in valid_columns:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     search_value = f"%{search_term}%"
                 else:
                     info("Search Error", "Invalid search field selected.")
                     search_term = None

        elif table_name == "destinations":
            select_query = "SELECT DestinationID, DestinationName, Hotel, DestinationCost, CityName, Days"
            base_query = f"FROM {table_name}"
            columns = ["ID", "Name", "Hotel", "Cost", "City", "Days"]
            if search_term and search_field:
                valid_columns = ["DestinationID", "DestinationName", "Hotel", "DestinationCost", "CityName", "Days"]
                if search_field in valid_columns:
                     # Format cost search correctly
                     if search_field == 'DestinationCost':
                         # Basic check if search term is numeric for cost
                         if search_term.isdigit() or (search_term.startswith('£') and search_term[1:].isdigit()):
                             cost_value = search_term.lstrip('£')
                             where_clause = f" WHERE {search_field} = %s" # Exact match for cost might be better
                             search_value = cost_value
                         else:
                             info("Search Error", "Cost search requires a number.")
                             search_term = None # Prevent invalid search
                     else:
                         where_clause = f" WHERE {search_field} LIKE %s"
                         search_value = f"%{search_term}%"
                else:
                     info("Search Error", "Invalid search field selected.")
                     search_term = None

        elif table_name == "drivers":
             select_query = "SELECT DriverID, DriverName" # Use DriverName
             base_query = f"FROM {table_name}"
             columns = ["ID", "Driver Name"]
             if search_term and search_field:
                 valid_columns = ["DriverID", "DriverName"]
                 if search_field in valid_columns:
                     where_clause = f" WHERE {search_field} LIKE %s"
                     search_value = f"%{search_term}%"
                 else:
                     info("Search Error", "Invalid search field selected.")
                     search_term = None

        else:
            # Default behavior: Select all columns, fetch names dynamically
            select_query = "SELECT *"
            base_query = f"FROM {table_name}"
            # Fetch column names dynamically ONLY if not defined above
            if not columns:
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = [col['Field'] for col in cursor.fetchall()] # Access by key 'Field'

            if search_term and search_field:
                 # Basic validation: Check if search_field is in fetched columns
                 if search_field in columns:
                    where_clause = f" WHERE {search_field} LIKE %s"
                    search_value = f"%{search_term}%"
                 else:
                    info("Search Error", "Invalid search field selected.")
                    search_term = None # Prevent invalid search


        # --- Execute Queries ---
        count_query = f"SELECT COUNT(*) as total {base_query}{where_clause}"
        if where_clause:
            cursor.execute(count_query, (search_value,))
        else:
            cursor.execute(count_query)
        total_records = cursor.fetchone()['total']

        data_query = f"{select_query} {base_query}{where_clause} LIMIT %s OFFSET %s"
        query_params = []
        if where_clause:
            query_params.append(search_value)
        query_params.extend([records_per_page, offset])

        cursor.execute(data_query, tuple(query_params))
        records = cursor.fetchall() # Fetchall returns list of dicts

        total_pages = (total_records + records_per_page - 1) // records_per_page

        # --- Clear and Display ---
        clear_box(table_box)
        clear_box(pagination_box)

        # Create the table grid if there are records or headers
        if records or columns:
            table_grid = Box(table_box, layout="grid", width="fill", align="top")

            # Display headers
            for col, header in enumerate(columns):
                # Make headers bold
                Text(table_grid, text=header, grid=[col, 0], color=TEXT_COLOR, size=11, font="Arial", bold=True)

            # Display rows (using dictionary access)
            for row, record_dict in enumerate(records, start=1):
                col_index = 0
                # Iterate through the defined column order for consistent display
                for header in columns:
                    # Try to find the corresponding key in the fetched record dictionary
                    # This handles aliases and cases where SELECT * was used vs specific selects
                    key_found = False
                    # Check common variations (original name, alias if simple)
                    possible_keys = [header.replace(" ", ""), header] # Add more variations if needed based on your aliases
                    if table_name == "bookings" and header == "Cost": possible_keys.append("Cost")
                    if table_name == "bookings" and header == "ID": possible_keys.append("BookingID")
                    if table_name == "trips" and header == "ID": possible_keys.append("TripID")
                    if table_name == "customers" and header == "ID": possible_keys.append("CustomerID")
                    if table_name == "coaches" and header == "ID": possible_keys.append("CoachID")
                    if table_name == "destinations" and header == "ID": possible_keys.append("DestinationID")
                    if table_name == "drivers" and header == "ID": possible_keys.append("DriverID")


                    data_to_display = "N/A" # Default if key not found
                    for key in record_dict.keys():
                        # A simple check if the key *contains* the header name (case-insensitive)
                        # or matches common aliases might be needed if headers don't map directly.
                        # For now, we assume the SELECT query provides keys matching `columns` or easily derived ones.
                        # Let's refine based on the specific SELECTs:
                        data_key = None
                        if table_name == "bookings":
                            map_bk = {"ID": "BookingID", "Cust. ID": "CustomerID", "Customer Name": "CustomerName", "Trip ID": "TripID", "Destination": "DestinationName", "Trip Date": "TripDate", "# People": "NumberofPeople", "Cost": "Cost", "Request": "SpecialRequest", "Booking Date": "BookingDate"}
                            data_key = map_bk.get(header)
                        elif table_name == "trips":
                            map_tr = {"ID": "TripID", "Coach ID": "CoachID", "Coach Reg": "CoachReg", "Driver ID": "DriverID", "Driver Name": "DriverName", "Dest. ID": "DestinationID", "Destination": "DestinationName", "Date": "Date"}
                            data_key = map_tr.get(header)
                        elif table_name == "customers":
                            map_cu = {"ID": "CustomerID", "First Name": "FirstName", "Surname": "Surname", "Email": "Email", "Address 1": "AddressLine1", "Address 2": "AddressLine2", "City": "City", "Postcode": "Postcode", "Phone": "PhoneNumber", "Notes": "SpecialNotes"}
                            data_key = map_cu.get(header)
                        elif table_name == "coaches":
                             map_co = {"ID": "CoachID", "Registration": "Registration", "Seats": "Seats"}
                             data_key = map_co.get(header)
                        elif table_name == "destinations":
                             map_de = {"ID": "DestinationID", "Name": "DestinationName", "Hotel": "Hotel", "Cost": "DestinationCost", "City": "CityName", "Days": "Days"}
                             data_key = map_de.get(header)
                        elif table_name == "drivers":
                             map_dr = {"ID": "DriverID", "Driver Name": "DriverName"}
                             data_key = map_dr.get(header)
                        else: # Default case if not specifically mapped
                             data_key = header # Assume header name is the key

                        if data_key and data_key in record_dict:
                             data_to_display = str(record_dict[data_key]) if record_dict[data_key] is not None else "" # Handle None
                             key_found = True
                             break # Found the data for this column

                    Text(table_grid, text=data_to_display, grid=[col_index, row], color=TEXT_COLOR, size=10)
                    col_index += 1

        elif not columns:
             Text(table_box, text="Could not determine table columns.", color="red")
        else:
             Text(table_box, text="No records found.", color=TEXT_COLOR)


        # --- Pagination controls ---
        # Use a Box with grid layout for controls
        pagination_controls = Box(pagination_box, layout="grid", width="fill", align="bottom")

        # Previous Button
        if page > 0:
            prev_button = PushButton(pagination_controls, text="<< Previous",
                      command=lambda: fetch_and_display_table(table_name, table_box, pagination_box,
                                                            page - 1, search_term, search_field),
                      grid=[0, 0], align="left")
            prev_button.bg = BUTTON_BG_COLOR
            prev_button.text_color = BUTTON_TEXT_COLOR

        # Page Info Text
        Text(pagination_controls, text=f"Page {page + 1} of {max(1, total_pages)}", grid=[1, 0], align="left", color=TEXT_COLOR) # Use max(1, ...) for page 1 of 0 case

        # Next Button
        if page < total_pages - 1:
            next_button = PushButton(pagination_controls, text="Next >>",
                      command=lambda: fetch_and_display_table(table_name, table_box, pagination_box,
                                                            page + 1, search_term, search_field),
                      grid=[2, 0], align="left")
            next_button.bg = BUTTON_BG_COLOR
            next_button.text_color = BUTTON_TEXT_COLOR

    except mysql.connector.Error as err:
        clear_box(table_box) # Clear any partial drawing
        clear_box(pagination_box)
        Text(table_box, text=f"Database Error:\n{err}", color="red", size=12)
        print(f"Database Error in fetch_and_display_table: {err}") # Log for debugging
    except Exception as e:
        clear_box(table_box) # Clear any partial drawing
        clear_box(pagination_box)
        Text(table_box, text=f"An unexpected error occurred:\n{e}", color="red", size=12)
        print(f"Unexpected Error in fetch_and_display_table: {e}") # Log for debugging


# <<<--- End of Added/Modified Code --->>>


# --- GUI Functions ---

def go_back(current_window, previous_window):
    """Hides the current window and shows the previous window."""
    current_window.hide()
    if previous_window: # Check if previous window exists
        previous_window.show()
    else:
        app.show() # Fallback to main app window if previous is None

# --- Helper functions for back buttons ---
# ... (keep all your existing go_back_* functions) ...
def go_back_to_admin_main():
    go_back(admin_main_window, app) # Should go back to app (main login screen choice) or previous menu? Let's assume app for now.
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

# --- Modified Back Button Functions for Data Windows ---
# These now go back to the menu window from which they were opened

def go_back_to_staff_bookings_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_bookings_window)

def go_back_to_admin_customers_menu_from_data(window_to_hide):
     # Need to know WHICH customers window opened it (admin or staff)
     # For now, assume admin context if called from admin menu functions
    go_back(window_to_hide, customers_window) # Assumes customers_window is the admin one

def go_back_to_staff_customers_menu_from_data(window_to_hide):
     # Explicit function for staff context
     go_back(window_to_hide, staff_customers_window)


def go_back_to_admin_coaches_menu_from_data(window_to_hide):
    go_back(window_to_hide, coaches_window)

def go_back_to_admin_destinations_menu_from_data(window_to_hide):
    go_back(window_to_hide, destinations_window)

def go_back_to_staff_destinations_menu_from_data(window_to_hide):
    go_back(window_to_hide, staff_destinations_window)


def go_back_to_admin_drivers_menu_from_data(window_to_hide):
    go_back(window_to_hide, drivers_window)

def go_back_to_staff_trips_menu_from_data(window_to_hide): # Renamed for clarity
    go_back(window_to_hide, staff_trips_window)

def go_back_to_main_menu(window_to_hide):  # Takes window to hide as argument
    go_back(window_to_hide, app) # Go back to the main app window


# --- Data Fetching Functions ---
# These are NO LONGER DIRECTLY USED by the data display windows,
# but might be used by other parts of your code (e.g., populating Combos). Keep them for now.
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


# --- MODIFIED Functions to open data windows ---

def open_bookings_data_window(parent_window):
    """Opens a new window to display booking data using the integrated table view."""
    parent_window.hide()
    # Make the window variable local to avoid potential global conflicts if opened multiple times
    bookings_data_win = Window(app, title="Booking Data", width=950, height=600, bg=BG_COLOR) # Wider
    Text(bookings_data_win, text="All Bookings", color=TEXT_COLOR, size=14, font="Arial", align="top")

    # Box for search controls (created by create_search_box)
    search_area_box = Box(bookings_data_win, align="top", width="fill")

    # Box to hold the table grid
    table_view_box = Box(bookings_data_win, align="top", width="fill", height="fill", border=1) # Added border

    # Box for pagination controls
    pagination_box = Box(bookings_data_win, align="bottom", width="fill")

    # Create search controls and populate the first page
    create_search_box(search_area_box, "bookings", table_view_box, pagination_box)
    fetch_and_display_table("bookings", table_view_box, pagination_box, page=0) # Load initial page

    # Back button - Determine correct back function based on parent
    back_command = None
    if parent_window == staff_bookings_window:
         back_command=lambda: go_back_to_staff_bookings_menu_from_data(bookings_data_win)
    # Add elif for admin context if bookings are viewed there too
    # else: # Default or error case
    #     back_command = lambda: go_back(bookings_data_win, app) # Fallback

    if back_command:
        back_button = PushButton(pagination_box, text="Back", command=back_command, align="right") # Move back button maybe?
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
         Text(pagination_box, text="Cannot determine parent window", color="red")


    bookings_data_win.show()


def open_customers_data_window(parent_window):
    """Opens customer data view using integrated table."""
    parent_window.hide()
    customers_data_win = Window(app, title="Customer Data", width=1100, height=600, bg=BG_COLOR)
    Text(customers_data_win, text="All Customers", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(customers_data_win, align="top", width="fill")
    table_view_box = Box(customers_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(customers_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "customers", table_view_box, pagination_box)
    fetch_and_display_table("customers", table_view_box, pagination_box, page=0)

    # Determine correct back function
    back_command = None
    if parent_window == customers_window: # Assumes customers_window is Admin's
         back_command = lambda: go_back_to_admin_customers_menu_from_data(customers_data_win)
    elif parent_window == staff_customers_window:
         back_command = lambda: go_back_to_staff_customers_menu_from_data(customers_data_win)

    if back_command:
        back_button = PushButton(pagination_box, text="Back", command=back_command, align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
         Text(pagination_box, text="Cannot determine parent window", color="red")


    customers_data_win.show()


def open_coaches_data_window(parent_window):
    """Opens coach data view using integrated table."""
    parent_window.hide()
    coaches_data_win = Window(app, title="Coach Data", width=800, height=600, bg=BG_COLOR)
    Text(coaches_data_win, text="All Coaches", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(coaches_data_win, align="top", width="fill")
    table_view_box = Box(coaches_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(coaches_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "coaches", table_view_box, pagination_box)
    fetch_and_display_table("coaches", table_view_box, pagination_box, page=0)

    # Back button (Assuming only Admin views/manages coaches directly in this structure)
    back_button = PushButton(pagination_box, text="Back", command=lambda: go_back_to_admin_coaches_menu_from_data(coaches_data_win), align="right")
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR

    coaches_data_win.show()

def open_destinations_data_window(parent_window):
    """Opens destination data view using integrated table."""
    parent_window.hide()
    destinations_data_win = Window(app, title="Destination Data", width=800, height=600, bg=BG_COLOR)
    Text(destinations_data_win, text="All Destinations", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(destinations_data_win, align="top", width="fill")
    table_view_box = Box(destinations_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(destinations_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "destinations", table_view_box, pagination_box)
    fetch_and_display_table("destinations", table_view_box, pagination_box, page=0)

    # Determine correct back function
    back_command = None
    if parent_window == destinations_window: # Assumes destinations_window is Admin's
         back_command = lambda: go_back_to_admin_destinations_menu_from_data(destinations_data_win)
    elif parent_window == staff_destinations_window:
         back_command = lambda: go_back_to_staff_destinations_menu_from_data(destinations_data_win)


    if back_command:
        back_button = PushButton(pagination_box, text="Back", command=back_command, align="right")
        back_button.bg = BUTTON_BG_COLOR
        back_button.text_color = BUTTON_TEXT_COLOR
    else:
         Text(pagination_box, text="Cannot determine parent window", color="red")


    destinations_data_win.show()


def open_drivers_data_window(parent_window):
    """Opens driver data view using integrated table."""
    parent_window.hide()
    drivers_data_win = Window(app, title="Driver Data", width=800, height=600, bg=BG_COLOR)
    Text(drivers_data_win, text="All Drivers", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(drivers_data_win, align="top", width="fill")
    table_view_box = Box(drivers_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(drivers_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "drivers", table_view_box, pagination_box)
    fetch_and_display_table("drivers", table_view_box, pagination_box, page=0)

    # Back button (Assuming only Admin views/manages drivers directly)
    back_button = PushButton(pagination_box, text="Back", command=lambda: go_back_to_admin_drivers_menu_from_data(drivers_data_win), align="right")
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR

    drivers_data_win.show()


def open_trips_data_window(parent_window):
    """Opens trip data view using integrated table."""
    parent_window.hide()
    trips_data_win = Window(app, title="Trip Data", width=900, height=600, bg=BG_COLOR) # Wider
    Text(trips_data_win, text="All Trips", color=TEXT_COLOR, size=14, font="Arial", align="top")

    search_area_box = Box(trips_data_win, align="top", width="fill")
    table_view_box = Box(trips_data_win, align="top", width="fill", height="fill", border=1)
    pagination_box = Box(trips_data_win, align="bottom", width="fill")

    create_search_box(search_area_box, "trips", table_view_box, pagination_box)
    fetch_and_display_table("trips", table_view_box, pagination_box, page=0)

    # Back button (Assuming only Staff views trips directly from their menu)
    back_button = PushButton(pagination_box, text="Back", command=lambda: go_back_to_staff_trips_menu_from_data(trips_data_win), align="right")
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR

    trips_data_win.show()


#region Admin Windows
# --- Admin Window Functions ---
def open_customers_window():
    admin_main_window.hide()
    global customers_window # Keep global ref if needed by other functions like back buttons
    customers_window = Window(app, title="Admin Customers", width=800, height=600, bg=BG_COLOR)
    Text(customers_window, text="Customers Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(customers_window, layout="auto", width="fill")
    # Pass the current window (customers_window) to the function that opens the data view
    view_customers_button = PushButton(button_box, text="View Customers", width=20, command=lambda: open_customers_data_window(customers_window))
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
    Text(destinations_window, text="Destinations Management (Admin)", color=TEXT_COLOR, size=14, font="Arial")
    button_box = Box(destinations_window, layout="auto", width="fill")
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20, command=lambda: open_destinations_data_window(destinations_window))
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
    view_coaches_button = PushButton(button_box, text="View Coaches", width=20, command=lambda: open_coaches_data_window(coaches_window))
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
    view_drivers_button = PushButton(button_box, text="View Drivers", width=20, command=lambda: open_drivers_data_window(drivers_window))
    add_drivers_button = PushButton(button_box, text="Add Drivers", width=20, command=open_add_driver_window)
    remove_drivers_button = PushButton(button_box, text="Remove Drivers", width=20, command=open_remove_driver_window)

    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_admin_main_from_drivers)
    view_drivers_button.bg = BUTTON_BG_COLOR; view_drivers_button.text_color = BUTTON_TEXT_COLOR
    add_drivers_button.bg = BUTTON_BG_COLOR; add_drivers_button.text_color = BUTTON_TEXT_COLOR
    remove_drivers_button.bg = BUTTON_BG_COLOR; remove_drivers_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    drivers_window.show()


def open_admin_main_window():
    # Check if admin_login_window exists before trying to hide it
    global admin_login_window
    try:
        if admin_login_window and admin_login_window.visible:
             admin_login_window.hide()
    except NameError: # If admin_login_window was never created or already destroyed
         pass
    except AttributeError: # If the object exists but doesn't have 'visible' (unlikely for Window)
         pass


    global admin_main_window
    admin_main_window = Window(app, title="Admin Main", width=800, height=600, bg=BG_COLOR)
    Text(admin_main_window, text="Admin Main Menu", color=TEXT_COLOR, size=14, font="Arial") # Title clarity
    button_box = Box(admin_main_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_customers_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_destinations_window)
    coaches_button = PushButton(button_box, text="COACHES", width=15, command=open_coaches_window)
    drivers_button = PushButton(button_box, text="DRIVERS", width=15, command=open_drivers_window)
    search_button = PushButton(button_box, text="QUERIES", width=15, command=open_query_window) # Changed text to Queries
    back_button = PushButton(button_box, text="Logout", width=15, command=lambda: go_back_to_main_menu(admin_main_window)) # Logout goes to main screen

    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    coaches_button.bg = BUTTON_BG_COLOR; coaches_button.text_color = BUTTON_TEXT_COLOR
    drivers_button.bg = BUTTON_BG_COLOR; drivers_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR # Style for Search button
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR # Style for Back/Logout button

    admin_main_window.show()

#endregion Admin Windows


#region Staff Windows
# --- Staff Window Functions ---
def open_staff_customers_window():
    staff_window.hide()
    global staff_customers_window
    staff_customers_window = Window(app, title="Staff Customers", width=800, height=600, bg=BG_COLOR)
    Text(staff_customers_window, text="Customers (Staff)", color=TEXT_COLOR, size=14, font="Arial") # Added context
    button_box = Box(staff_customers_window, layout="auto", width="fill")
    # Staff might only view/add/remove customers relevant to them? Assuming full view for now.
    view_customer_button = PushButton(button_box, text="View Customers", width=20, command=lambda: open_customers_data_window(staff_customers_window)) # Added View
    add_customer_button = PushButton(button_box, text="Add Customer", width=20, command=open_add_customer_window)
    # Remove customer might be admin only - keeping it here based on original code
    remove_customer_button = PushButton(button_box, text="Remove Customer", width=20, command=open_remove_customer_window)
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_customers)

    view_customer_button.bg = BUTTON_BG_COLOR; view_customer_button.text_color = BUTTON_TEXT_COLOR # Style view button
    add_customer_button.bg = BUTTON_BG_COLOR; add_customer_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_button.bg = BUTTON_BG_COLOR; remove_customer_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_customers_window.show()


def open_staff_bookings_window():
    staff_window.hide()
    global staff_bookings_window
    staff_bookings_window = Window(app, title="Staff Bookings", width=800, height=600, bg=BG_COLOR)
    Text(staff_bookings_window, text="Bookings (Staff)", color=TEXT_COLOR, size=14, font="Arial") # Added context
    button_box = Box(staff_bookings_window, layout="auto", width="fill")
    view_bookings_button = PushButton(button_box, text="View Bookings", width=20, command=lambda: open_bookings_data_window(staff_bookings_window))
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
    Text(staff_destinations_window, text="View Destinations (Staff)", color=TEXT_COLOR, size=14, font="Arial") # Added context
    button_box = Box(staff_destinations_window, layout="auto", width="fill")
    view_destinations_button = PushButton(button_box, text="View Destinations", width=20, command=lambda: open_destinations_data_window(staff_destinations_window))
    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_destinations)
    view_destinations_button.bg = BUTTON_BG_COLOR; view_destinations_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_destinations_window.show()

def open_staff_trips_window():
    staff_window.hide()
    global staff_trips_window
    staff_trips_window = Window(app, title="Staff Trips", width=800, height=600, bg=BG_COLOR)
    Text(staff_trips_window, text="Trips (Staff)", color=TEXT_COLOR, size=14, font="Arial") # Added context
    button_box = Box(staff_trips_window, layout="auto", width="fill")
    view_trips_button = PushButton(button_box, text="View Trips", width=20, command=lambda: open_trips_data_window(staff_trips_window))
    add_trips_button = PushButton(button_box, text="Add Trips", width=20, command=open_add_trip_window)
    remove_trips_button = PushButton(button_box, text="Remove Trips", width = 20) # Add command=open_remove_trip_window if you implement it

    back_button = PushButton(button_box, text="Back", width=20, command=go_back_to_staff_main_from_trips)
    view_trips_button.bg = BUTTON_BG_COLOR; view_trips_button.text_color = BUTTON_TEXT_COLOR
    add_trips_button.bg = BUTTON_BG_COLOR; add_trips_button.text_color = BUTTON_TEXT_COLOR
    remove_trips_button.bg = BUTTON_BG_COLOR; remove_trips_button.text_color = BUTTON_TEXT_COLOR # Add command later
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    staff_trips_window.show()

def open_staff_window():
    app.hide()
    global staff_window
    staff_window = Window(app, title="Staff Interface", width=800, height=600, bg=BG_COLOR)
    Text(staff_window, text="Staff Main Menu", color=TEXT_COLOR, size=14, font="Arial") # Title clarity
    button_box = Box(staff_window, layout="auto", width="fill")
    customers_button = PushButton(button_box, text="CUSTOMERS", width=15, command=open_staff_customers_window)
    bookings_button = PushButton(button_box, text="BOOKINGS", width=15, command=open_staff_bookings_window)
    destinations_button = PushButton(button_box, text="DESTINATIONS", width=15, command=open_staff_destinations_window)
    trips_button = PushButton(button_box, text="TRIPS", width=15, command=open_staff_trips_window)
    search_button = PushButton(button_box, text="QUERIES", width=15, command=open_query_window)  # Changed text Queries
    back_button = PushButton(button_box, text="Logout", width=15, command=lambda: go_back_to_main_menu(staff_window)) # Logout goes to main screen

    customers_button.bg = BUTTON_BG_COLOR; customers_button.text_color = BUTTON_TEXT_COLOR
    bookings_button.bg = BUTTON_BG_COLOR; bookings_button.text_color = BUTTON_TEXT_COLOR
    destinations_button.bg = BUTTON_BG_COLOR; destinations_button.text_color = BUTTON_TEXT_COLOR
    trips_button.bg = BUTTON_BG_COLOR; trips_button.text_color = BUTTON_TEXT_COLOR
    search_button.bg = BUTTON_BG_COLOR; search_button.text_color = BUTTON_TEXT_COLOR # Style for search button
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR # Style for back/logout button
    staff_window.show()

#endregion Staff Windows


# --- Keep all your Add/Remove Window functions (`open_add_*`, `open_remove_*`) as they are ---
#region Add Windows
def open_add_customer_window():
    # Ensure you handle which window to return to (staff_customers_window or customers_window)
    # For simplicity, let's assume it's called from staff context for now
    parent = staff_customers_window # Default assumption

    # You might need to pass the parent window if called from multiple places
    # def open_add_customer_window(parent_window):

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
            # --- Input Validation ---
            if not first_name_entry.value:
                info("Input Error", "First Name is required.")
                return
            if not surname_entry.value:
                info("Input Error", "Surname is required.")
                return
            if not email_entry.value:
                info("Input Error", "Email is required.")
                return
            # Email validation using a regular expression (placed *after* empty check)
            email = email_entry.value
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_regex, email):
                info("Input Error", "Invalid email format.")
                return
            if not address1_entry.value:
                info("Input Error", "Address Line 1 is required.")
                return
            if not city_entry.value:
                info("Input Error", "City is required.")
                return
            if not postcode_entry.value:
                info("Input Error", "Postcode is required.")
                return
            if not phone_entry.value:
                info("Input Error", "Phone Number is required.")
                return


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
            # Show the correct parent window
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            info("Database Error", "Failed to add customer. Check Your Input")

    add_button = PushButton(add_customer_window, text="Add Customer", command=add_customer)
    # Back button should also show the correct parent
    back_button = PushButton(add_customer_window, text="Back", command=lambda: (add_customer_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR
    add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR
    back_button.text_color = BUTTON_TEXT_COLOR
    add_customer_window.show()


def open_add_booking_window():
    # Assume called from staff context
    parent = staff_bookings_window

    global add_booking_window, customer_combo, trip_combo, booking_cost_entry, num_people_entry, special_request_entry, date_of_booking_entry
    add_booking_window = Window(app, title="Add Booking", width=450, height=450, bg=BG_COLOR) #Increased window size
    Text(add_booking_window, text = "Enter Booking Details:", color = TEXT_COLOR)

    Text(add_booking_window, text="Customer:", color=TEXT_COLOR)
    customer_combo = Combo(add_booking_window, options=[], width="fill")
    # Populate customer Combo
    try:
        cursor.execute("SELECT CustomerID, FirstName, Surname FROM customers ORDER BY Surname, FirstName") # Added ordering
        customers = cursor.fetchall()
        customer_combo.clear()
        customer_combo.append("") # Add a blank option first
        for customer in customers:
             customer_combo.append(f"{customer['CustomerID']}: {customer['FirstName']} {customer['Surname']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load customers: {err}")
        add_booking_window.destroy()
        parent.show() # Show parent again if error
        return  # Exit the function

    Text(add_booking_window, text="Trip:", color=TEXT_COLOR)
    trip_combo = Combo(add_booking_window, options=[], width="fill")
     # Populate trip Combo
    try:
        # Only show future trips
        cursor.execute("""
            SELECT t.TripID, t.Date, d.DestinationName, d.DestinationID
            FROM trips t
            JOIN destinations d ON t.DestinationID = d.DestinationID
            WHERE t.Date >= CURDATE()
            ORDER BY t.Date
        """)
        trips = cursor.fetchall()
        trip_combo.clear() #clear options
        trip_combo.append("") # Add a blank option first
        for trip in trips:
            trip_combo.append(f"{trip['TripID']}: {trip['Date']} - {trip['DestinationName']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load trips: {err}")
        add_booking_window.destroy()
        parent.show() # Show parent again if error
        return

    # REMOVED Booking Cost TextBox - Should likely be calculated
    # Text(add_booking_window, text="Booking Cost:", color=TEXT_COLOR)
    # booking_cost_entry = TextBox(add_booking_window)


    Text(add_booking_window, text="Number of People:", color=TEXT_COLOR)
    num_people_entry = TextBox(add_booking_window)

    Text(add_booking_window, text="Special Request:", color=TEXT_COLOR)
    special_request_entry = TextBox(add_booking_window)

    # Date of Booking set automatically
    Text(add_booking_window, text="Date of Booking:", color=TEXT_COLOR)
    date_of_booking_display = Text(add_booking_window, text = "")  # Display-only Text widget

    import datetime
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    date_of_booking_display.value = current_date # Display the date


    # Function for adding booking.
    def add_booking():
        calculated_cost = 0 # Initialize cost
        try:
            # --- Input Validation ---
            selected_customer = customer_combo.value
            if not selected_customer:
                info("Input Error", "Please select a customer.")
                return
            customer_id = int(selected_customer.split(":")[0]) # Extract ID

            selected_trip = trip_combo.value
            if not selected_trip:
                info("Input Error", "Please select a trip.")
                return
            trip_id = int(selected_trip.split(":")[0]) # Extract ID

            # Number of people validation
            if not num_people_entry.value.isdigit() or int(num_people_entry.value) <= 0:
                info("Input Error", "Number of People must be a positive integer.")
                return
            num_people = int(num_people_entry.value) # Converting to int

            # --- Calculate Cost ---
            cursor.execute("""
                SELECT d.DestinationCost
                FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                WHERE t.TripID = %s
            """, (trip_id,))
            cost_result = cursor.fetchone()
            if cost_result and cost_result['DestinationCost'] is not None:
                 calculated_cost = float(cost_result['DestinationCost']) * num_people
            else:
                 info("Error", "Could not retrieve destination cost for calculation.")
                 # Decide whether to proceed with 0 cost or stop
                 # calculated_cost = 0 # Or return

            # Check against coach capacity
            cursor.execute("""
                SELECT c.Seats
                FROM trips t
                JOIN coaches c ON t.CoachID = c.CoachID
                WHERE t.TripID = %s
            """, (trip_id,))
            seat_result = cursor.fetchone()
            if seat_result:
                available_seats = seat_result['Seats']
                # Check already booked seats
                cursor.execute("SELECT SUM(NumberofPeople) as booked FROM bookings WHERE TripID = %s", (trip_id,))
                booked_result = cursor.fetchone()
                booked_seats = booked_result['booked'] if booked_result['booked'] else 0

                if num_people > (available_seats - booked_seats):
                    info("Input Error", f"Not enough seats available. Only {available_seats - booked_seats} left on this trip.")
                    return # Exit if not enough seats
            else:
                info("Database Error", "Could not retrieve coach capacity information.")
                return # Stop if capacity cannot be checked


            # --- Insert Booking ---
            cursor.execute("""
            INSERT INTO bookings (CustomerID, TripID, BookingCost, NumberofPeople, SpecialRequest, BookingDate)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (customer_id, trip_id, calculated_cost, # Use calculated cost
             num_people, special_request_entry.value, current_date)) # Use current_date
            conn.commit()
            info("Booking Added", f"Booking added successfully. Total Cost: £{calculated_cost:.2f}")
            add_booking_window.destroy()
            parent.show()

        except mysql.connector.Error as err:
             info("Database Error",f"Error Adding booking: {err}") #better error
             print(f"Database Error: {err}")
        except ValueError:
            info("Input Error", "Invalid ID format selected or number format error.")
        except IndexError: # added to handle the case if split fails
            info("Input Error", "Invalid selection in dropdown.")
        except TypeError: # Handle potential None from cost_result
             info("Error", "Could not calculate cost properly.")


    add_button = PushButton(add_booking_window, text="Add Booking", command=add_booking)
    back_button = PushButton(add_booking_window, text="Back", command=lambda: (add_booking_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_booking_window.show()


def open_add_coach_window():
    # Assume called from admin context
    parent = coaches_window

    global add_coach_window, coach_reg_entry, seats_entry
    add_coach_window = Window(app, title = "Add Coach", width = 400, height = 400, bg = BG_COLOR)
    Text(add_coach_window, text="Enter Coach Details:", color = TEXT_COLOR)

    Text(add_coach_window, text = "Coach Registration:", color = TEXT_COLOR)
    coach_reg_entry = TextBox(add_coach_window)

    Text(add_coach_window, text="Seats in Coach", color = TEXT_COLOR)
    seats_entry = TextBox(add_coach_window)

    def add_coach():
        try:
            if not coach_reg_entry.value:
                info("Input Error", "Coach Registration Required")
                return
            if not seats_entry.value.isdigit() or int(seats_entry.value) <= 0:
                info("Input Error", "Number of seats must be a positive number")
                return
            cursor.execute("""
            INSERT INTO coaches (Registration, Seats)
            VALUES (%s, %s)""",
            (coach_reg_entry.value, seats_entry.value))
            conn.commit()
            info("Coach Added", "The coach has been added to the database.")
            add_coach_window.destroy()
            parent.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            # Check for duplicate entry error (error code 1062)
            if err.errno == errorcode.ER_DUP_ENTRY:
                 info("Database Error", "A coach with this registration already exists.")
            else:
                 info("Database Error", f"Failed to add coach. Check input. Error: {err.errno}")


    add_button = PushButton(add_coach_window, text="Add Coach", command=add_coach)
    back_button = PushButton(add_coach_window, text="Back", command=lambda: (add_coach_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_coach_window.show()

def open_add_destination_window():
     # Assume called from admin context
    parent = destinations_window

    global add_destination_window, destination_name_entry, hotel_name_entry
    global destination_cost_entry, city_name_entry, days_entry

    add_destination_window = Window(app, title = "Add Destination", width = 400, height = 400, bg = BG_COLOR)
    Text(add_destination_window, text = "Enter Destination Details:", color = TEXT_COLOR)

    Text(add_destination_window, text = "Destination Name:", color = TEXT_COLOR)
    destination_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Hotel Name:", color = TEXT_COLOR)
    hotel_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Destination Cost (£):", color = TEXT_COLOR) # Specify currency
    destination_cost_entry = TextBox(add_destination_window)

    Text(add_destination_window, text="City Name:", color=TEXT_COLOR)
    city_name_entry = TextBox(add_destination_window)

    Text(add_destination_window, text = "Days:", color = TEXT_COLOR) # Colon added
    days_entry = TextBox(add_destination_window)

    def add_destination():
        try:
            # --- Input Validation ---
            if not destination_name_entry.value:
                info("Input Error", "Destination Name is required.")
                return
            if not hotel_name_entry.value:
                info("Input Error", "Hotel Name is required.")
                return
            # Validate cost is numeric (allow decimals)
            try:
                 cost = float(destination_cost_entry.value)
                 if cost < 0: raise ValueError("Cost cannot be negative")
            except ValueError:
                 info("Input Error", "Destination Cost must be a valid positive number.")
                 return

            if not city_name_entry.value:
                info("Input Error", "City Name is required.")
                return
            if not days_entry.value.isdigit() or int(days_entry.value) <= 0:
                info("Input Error", "Days must be a positive number.")
                return

            cursor.execute("""
            INSERT INTO destinations (DestinationName, Hotel, DestinationCost, CityName, Days)
            VALUES (%s, %s, %s, %s, %s)""",
            (destination_name_entry.value, hotel_name_entry.value, cost, # Use validated cost
             city_name_entry.value, days_entry.value))
            conn.commit()
            info("Success", "Destination added successfully.")
            add_destination_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            if err.errno == errorcode.ER_DUP_ENTRY:
                 info("Database Error", "A destination with this name might already exist.")
            else:
                info("Database Error", f"Failed to add Destination. Error: {err.errno}")

    add_button = PushButton(add_destination_window, text = "Add Destination", command=add_destination)
    back_button = PushButton(add_destination_window, text="Back", command = lambda: (add_destination_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_destination_window.show()


def open_add_driver_window():
     # Assume called from admin context
    parent = drivers_window

    global add_driver_window, driver_name_entry

    add_driver_window = Window(app, title = "Add Driver", width = 400, height = 400, bg = BG_COLOR)
    Text(add_driver_window, text = "Enter the Driver's Details:", color = TEXT_COLOR) # Corrected text

    Text(add_driver_window, text="Driver Name:", color=TEXT_COLOR)
    driver_name_entry = TextBox(add_driver_window)

    def add_driver():
        try:
            if not driver_name_entry.value:
                info("Input Error", "Driver name is required.") # Corrected text
                return

            cursor.execute("""
            INSERT INTO drivers (DriverName)
            VALUES (%s)""", (driver_name_entry.value,))
            conn.commit()
            info("Success", "Driver added successfully.")
            add_driver_window.destroy()
            parent.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            if err.errno == errorcode.ER_DUP_ENTRY:
                info("Database Error", "A driver with this name might already exist.")
            else:
                info("Database Error", f"Failed to add Driver. Error: {err.errno}")

    add_button = PushButton(add_driver_window, text="Add Driver", command = add_driver)
    back_button = PushButton(add_driver_window, text="Back", command = lambda: (add_driver_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_driver_window.show()

def open_add_trip_window():
     # Assume called from staff context
    parent = staff_trips_window

    global add_trip_window, coach_combo, driver_combo, destination_combo, date_entry

    add_trip_window = Window(app, title="Add Trip", width = 400, height = 400, bg = BG_COLOR)
    Text(add_trip_window, text = "Enter Trip Details: ", color = TEXT_COLOR)

    Text(add_trip_window, text = "Coach:", color = TEXT_COLOR)
    coach_combo = Combo(add_trip_window, options=[], width="fill")
    #Populate the combo box
    try:
        cursor.execute("SELECT CoachID, Registration FROM coaches ORDER BY Registration") # Added ordering
        coaches = cursor.fetchall()
        coach_combo.clear()
        coach_combo.append("") # Blank option
        for coach in coaches:
            coach_combo.append(f"{coach['CoachID']}: {coach['Registration']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load coaches: {err}")
        add_trip_window.destroy()
        parent.show()
        return


    Text(add_trip_window, text = "Driver:", color = TEXT_COLOR)
    driver_combo = Combo(add_trip_window, options=[], width="fill")
    #Populate Driver Combo
    try:
        cursor.execute("SELECT DriverID, DriverName FROM drivers ORDER BY DriverName") # Added ordering
        drivers = cursor.fetchall()
        driver_combo.clear()
        driver_combo.append("") # Blank option
        for driver in drivers:
            driver_combo.append(f"{driver['DriverID']}: {driver['DriverName']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load drivers: {err}")
        add_trip_window.destroy()
        parent.show()
        return

    Text(add_trip_window, text="Destination:", color=TEXT_COLOR)
    destination_combo = Combo(add_trip_window, options=[], width="fill")
     #Populate Destination Combo
    try:
        cursor.execute("SELECT DestinationID, DestinationName FROM destinations ORDER BY DestinationName") # Added ordering
        destinations = cursor.fetchall()
        destination_combo.clear()
        destination_combo.append("") # Blank option
        for destination in destinations:
            destination_combo.append(f"{destination['DestinationID']}: {destination['DestinationName']}")
    except mysql.connector.Error as err:
        info("Database Error", f"Could not load destinations: {err}")
        add_trip_window.destroy()
        parent.show()
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
                info("Input Error", "Please select a destination.")
                return
            destination_id = int(selected_destination.split(":")[0])

            # Date validation
            trip_date_str = date_entry.value
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"  # YYYY-MM-DD
            if not re.match(date_pattern, trip_date_str):
                 info("Input Error", "Invalid date format. Use YYYY-MM-DD.")
                 return
            # Optional: Check if date is in the past
            try:
                trip_date = datetime.datetime.strptime(trip_date_str, "%Y-%m-%d").date()
                if trip_date < datetime.date.today():
                    if not app.yesno("Past Date", "The selected date is in the past. Continue?"):
                        return
            except ValueError:
                 info("Input Error", "Invalid date value (e.g., month > 12).")
                 return


            cursor.execute("""
            INSERT INTO trips (CoachID, DriverID, DestinationID, Date)
            VALUES (%s, %s, %s, %s)""",
            (coach_id, driver_id, destination_id, trip_date_str)) # Use original string
            conn.commit()
            info("Success", "Trip has been added successfully.")
            add_trip_window.destroy()
            parent.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            if err.errno == errorcode.ER_DUP_ENTRY:
                 info("Database Error", "A trip with these details might already exist (check constraints).")
            elif err.errno == 1452: # Foreign key constraint fails
                 info("Database Error", "Invalid Coach, Driver, or Destination ID selected.")
            else:
                 info("Database Error", f"Failed to add Trip. Error: {err.errno}")
        except ValueError:
            info("Input Error", "Invalid ID format selected.")
        except IndexError:
            info("Input Error", "Invalid selection in dropdown.")

    add_button = PushButton(add_trip_window, text = "Add Trip", command = add_trip)
    back_button = PushButton(add_trip_window, text = "Back", command = lambda: (add_trip_window.destroy(), parent.show()))
    add_button.bg = BUTTON_BG_COLOR; add_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    add_trip_window.show()
#endregion

#region Remove Windows

def open_remove_booking_window():
    # Assume called from staff context
    parent = staff_bookings_window

    global remove_booking_window, remove_booking_entry

    remove_booking_window = Window(app, title="Remove Booking", width = 400, height = 400, bg = BG_COLOR)
    Text(remove_booking_window, text = "Enter Booking ID you want to remove:", color = TEXT_COLOR)
    remove_booking_entry = TextBox(remove_booking_window)

    def remove_booking():
        booking_id = remove_booking_entry.value
        if not booking_id.isdigit():
             info("Input Error", "Booking ID must be a number.")
             return

        # Confirmation Dialog
        if not app.yesno("Confirm Deletion", f"Are you sure you want to delete Booking ID {booking_id}?"):
             return

        try:
            cursor.execute("DELETE FROM bookings WHERE BookingID = %s", (booking_id,))
            conn.commit()
            # Check if any row was actually deleted
            if cursor.rowcount > 0:
                info("Success", f"Booking ID {booking_id} removed successfully.")
            else:
                info("Not Found", f"Booking ID {booking_id} not found.")

            remove_booking_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            info("Database Error", f"Failed to remove Booking. Error: {err.errno}")

    remove_button = PushButton(remove_booking_window, text="Remove Booking", command=remove_booking)
    back_button = PushButton(remove_booking_window, text="Back", command=lambda: (remove_booking_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_booking_window.show()


def open_remove_coach_window():
     # Assume called from admin context
    parent = coaches_window

    global remove_coach_window, remove_coach_entry

    remove_coach_window = Window(app, title="Remove Coach", width=400, height=400, bg=BG_COLOR)
    Text(remove_coach_window, text="Enter Coach ID to remove:", color=TEXT_COLOR)
    remove_coach_entry = TextBox(remove_coach_window)

    def remove_coach():
        coach_id = remove_coach_entry.value
        if not coach_id.isdigit():
            info("Input Error", "Coach ID must be a number.")
            return

        if not app.yesno("Confirm Deletion", f"Are you sure you want to delete Coach ID {coach_id}? This might affect existing trips."):
            return

        try:
             # Check if coach is used in trips BEFORE deleting (optional but good practice)
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE CoachID = %s", (coach_id,))
            if cursor.fetchone()['trip_count'] > 0:
                if not app.yesno("Warning", "This coach is assigned to trips. Deleting it will cause issues. Continue anyway?"):
                    return

            cursor.execute("DELETE FROM coaches WHERE CoachID = %s", (coach_id,))
            conn.commit()
            if cursor.rowcount > 0:
                 info("Success", f"Coach ID {coach_id} removed successfully.")
            else:
                 info("Not Found", f"Coach ID {coach_id} not found.")
            remove_coach_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            if err.errno == 1451: # Foreign key constraint (might happen if check above fails or is bypassed)
                 info("Database Error", "Cannot delete coach because it is referenced by existing trips.")
            else:
                 info("Database Error", f"Failed to remove coach. Error: {err.errno}")

    remove_button = PushButton(remove_coach_window, text="Remove Coach", command=remove_coach)
    back_button = PushButton(remove_coach_window, text="Back", command=lambda: (remove_coach_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_coach_window.show()

def open_remove_customer_window():
    # Determine parent context - needs careful handling if called from admin AND staff
    # Let's assume STAFF context for now based on original flow
    parent = staff_customers_window

    global remove_customer_window, remove_customer_entry

    remove_customer_window = Window(app, title="Remove Customer", width=400, height=400, bg=BG_COLOR)
    Text(remove_customer_window, text="Enter Customer ID to remove:", color=TEXT_COLOR)
    remove_customer_entry = TextBox(remove_customer_window)

    def remove_customer():
        customer_id = remove_customer_entry.value
        if not customer_id.isdigit():
            info("Input Error", "Customer ID must be a number.")
            return

        if not app.yesno("Confirm Deletion", f"Are you sure you want to delete Customer ID {customer_id}? This will also delete their bookings."):
            return

        try:
             # Optional: Check for bookings first
            cursor.execute("SELECT COUNT(*) as booking_count FROM bookings WHERE CustomerID = %s", (customer_id,))
            if cursor.fetchone()['booking_count'] > 0:
                 if not app.yesno("Warning", "This customer has existing bookings. Deleting them will remove these bookings. Continue?"):
                      return
                 # Delete bookings first if necessary (or rely on CASCADE DELETE in DB)
                 # cursor.execute("DELETE FROM bookings WHERE CustomerID = %s", (customer_id,))


            cursor.execute("DELETE FROM customers WHERE CustomerID = %s", (customer_id,))
            conn.commit()
            if cursor.rowcount > 0:
                 info("Success", f"Customer ID {customer_id} removed successfully.")
            else:
                 info("Not Found", f"Customer ID {customer_id} not found.")
            remove_customer_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            if err.errno == 1451:
                info("Database Error", "Cannot delete customer due to related records (likely bookings). Delete bookings first.")
            else:
                info("Database Error", f"Failed to remove customer. Error: {err.errno}")

    remove_button = PushButton(remove_customer_window, text="Remove Customer", command=remove_customer)
    back_button = PushButton(remove_customer_window, text="Back", command= lambda: (remove_customer_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR;  back_button.text_color = BUTTON_TEXT_COLOR
    remove_customer_window.show()


def open_remove_destination_window():
    # Assume called from admin context
    parent = destinations_window

    global remove_destination_window, remove_destination_entry

    remove_destination_window = Window(app, title = "Remove Destination", width = 400, height = 400, bg=BG_COLOR)
    Text(remove_destination_window, text = "Enter the DestinationID you want to remove:", color = TEXT_COLOR)
    remove_destination_entry = TextBox(remove_destination_window)

    def remove_destination():
        destination_id = remove_destination_entry.value
        if not destination_id.isdigit():
             info("Input Error", "Destination ID must be a number.")
             return

        if not app.yesno("Confirm Deletion", f"Are you sure you want to delete Destination ID {destination_id}? This might affect existing trips."):
            return

        try:
            # Check if destination is used in trips
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DestinationID = %s", (destination_id,))
            if cursor.fetchone()['trip_count'] > 0:
                if not app.yesno("Warning", "This destination is used in trips. Deleting it will cause issues. Continue anyway?"):
                    return

            cursor.execute("DELETE FROM destinations WHERE DestinationID = %s", (destination_id,))
            conn.commit()
            if cursor.rowcount > 0:
                info("Success", f"Destination ID {destination_id} removed successfully.")
            else:
                 info("Not Found", f"Destination ID {destination_id} not found.")
            remove_destination_window.destroy()
            parent.show()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            if err.errno == 1451:
                 info("Database Error", "Cannot delete destination because it is referenced by existing trips.")
            else:
                info("Database Error", f"Failed to remove destination. Error: {err.errno}")

    remove_button = PushButton(remove_destination_window, text="Remove Destination", command=remove_destination)
    back_button = PushButton(remove_destination_window, text="Back", command = lambda: (remove_destination_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_destination_window.show()

def open_remove_driver_window():
    # Assume called from admin context
    parent = drivers_window

    global remove_driver_window, remove_driver_entry

    remove_driver_window = Window(app, title = "Remove Driver", width = 400, height = 400, bg = BG_COLOR)
    Text(remove_driver_window, text="Enter Driver ID to remove:", color = TEXT_COLOR)
    remove_driver_entry = TextBox(remove_driver_window)

    def remove_driver():
        driver_id = remove_driver_entry.value
        if not driver_id.isdigit():
             info("Input Error", "Driver ID must be a number.")
             return

        if not app.yesno("Confirm Deletion", f"Are you sure you want to delete Driver ID {driver_id}? This might affect existing trips."):
            return

        try:
            # Check if driver is used in trips
            cursor.execute("SELECT COUNT(*) as trip_count FROM trips WHERE DriverID = %s", (driver_id,))
            if cursor.fetchone()['trip_count'] > 0:
                 if not app.yesno("Warning", "This driver is assigned to trips. Deleting them will cause issues. Continue anyway?"):
                      return

            cursor.execute("DELETE FROM drivers WHERE DriverID = %s", (driver_id,))
            conn.commit()
            if cursor.rowcount > 0:
                info("Success", f"Driver ID {driver_id} removed successfully.")
            else:
                info("Not Found", f"Driver ID {driver_id} not found.")
            remove_driver_window.destroy()
            parent.show()
        except mysql.connector.Error as err:
             print(f"Database Error: {err}")
             if err.errno == 1451:
                 info("Database Error", "Cannot delete driver because they are referenced by existing trips.")
             else:
                info("Database Error", f"Failed to remove driver. Error: {err.errno}")

    remove_button = PushButton(remove_driver_window, text = "Remove Driver", command = remove_driver)
    back_button = PushButton(remove_driver_window, text="Back", command=lambda: (remove_driver_window.destroy(), parent.show()))
    remove_button.bg = BUTTON_BG_COLOR; remove_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    remove_driver_window.show()

#endregion Remove Windows


# --- Query Window (keep as is, unless you want pagination there too) ---
def open_query_window():
    """Opens a window for executing various database queries."""
     # Decide which window is the parent (could be admin or staff)
     # For simplicity, let's assume it closes and the user goes back manually
     # Or pass parent: def open_query_window(parent_window): parent_window.hide() ... back_button command=lambda: go_back(query_window, parent_window)

    global query_window # Make global if needed by sub-windows for closing etc.
    query_window = Window(app, title="Database Queries", width=800, height=600, bg=BG_COLOR)
    Text(query_window, text="Select a Query:", color=TEXT_COLOR)

    # --- Query 1: Passengers on a specific trip ---
    def lincoln_passengers():
        selection_window = Window(query_window, title="Select Trip for Passenger List", width=400, height=200, bg=BG_COLOR) # Clarified title
        Text(selection_window, text="Select Destination:", color=TEXT_COLOR)
        destination_combo = Combo(selection_window, options=[], width="fill")
        Text(selection_window, text="Enter Date (YYYY-MM-DD):", color=TEXT_COLOR)
        date_entry = TextBox(selection_window)

        try:
            cursor.execute("SELECT DestinationID, DestinationName FROM destinations ORDER BY DestinationName")
            destinations = cursor.fetchall()
            destination_options = [""] + [f"{dest['DestinationID']}: {dest['DestinationName']}" for dest in destinations] # Add blank option
            destination_combo.clear()
            for option in destination_options:
                destination_combo.append(option)
        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching destinations: {err}")
            selection_window.destroy()
            return

        def run_passenger_query():
            try:
                selected_destination = destination_combo.value
                trip_date_str = date_entry.value

                if not selected_destination:
                    info("Input Error", "Please select a destination.")
                    return
                if not trip_date_str:
                    info("Input Error", "Please enter a date.")
                    return
                 # Validate date format
                date_pattern = r"^\d{4}-\d{2}-\d{2}$"
                if not re.match(date_pattern, trip_date_str):
                    info("Input Error", "Invalid date format. Use YYYY-MM-DD.")
                    return

                destination_id = int(selected_destination.split(":")[0])

                # Find the specific TripID first (more robust than just dest+date)
                cursor.execute("SELECT TripID FROM trips WHERE DestinationID = %s AND Date = %s", (destination_id, trip_date_str))
                trip_result = cursor.fetchone()

                if not trip_result:
                     info("Not Found", "No trip found for the selected destination and date.")
                     return

                trip_id = trip_result['TripID']

                # Now get passengers for that specific TripID
                cursor.execute("""
                    SELECT c.CustomerID, c.FirstName, c.Surname
                    FROM customers c
                    JOIN bookings b ON c.CustomerID = b.CustomerID
                    WHERE b.TripID = %s
                    ORDER BY c.Surname, c.FirstName
                """, (trip_id,))
                passengers = cursor.fetchall()

                result_window = Window(query_window, title=f"Passengers on Trip {trip_id}", width=400, height=300, bg=BG_COLOR) # Show Trip ID
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
                if passengers:
                    result_list.append(f"{'ID':<5}{'Name':<25}") # Header
                    result_list.append("-" * 30)
                    for passenger in passengers:
                        result_list.append(f"{passenger['CustomerID']:<5}{passenger['FirstName']} {passenger['Surname']}")
                else:
                    result_list.append("No passengers booked on this trip.")
                close_button = PushButton(result_window, text="Close", command=result_window.destroy, align="bottom") # Align bottom
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show()
                selection_window.destroy()

            except mysql.connector.Error as err:
                info("Database Error", f"Error fetching passenger data: {err}")
            except (ValueError, IndexError):
                info("Input Error", "Invalid selection or date format.")


        ok_button = PushButton(selection_window, text="Show Passengers", command=run_passenger_query) # Clarified button text
        cancel_button = PushButton(selection_window, text="Cancel", command=selection_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        selection_window.show()


    # --- Query 2: Available trips in chronological order ---
    def available_trips():
        try:
            cursor.execute("""
                SELECT t.TripID, t.Date, d.DestinationName, d.CityName, c.Seats,
                       (SELECT SUM(b.NumberofPeople) FROM bookings b WHERE b.TripID = t.TripID) AS BookedSeats
                FROM trips t
                JOIN destinations d ON t.DestinationID = d.DestinationID
                JOIN coaches c ON t.CoachID = c.CoachID
                WHERE t.Date >= CURDATE()
                ORDER BY t.Date ASC  -- Changed to ASC for chronological
            """)
            trips = cursor.fetchall()

            result_window = Window(query_window, title="Available Trips (Upcoming)", width=650, height=400, bg=BG_COLOR) # Clarified Title
            result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)
            if trips:
                # Header
                result_list.append(f"{'ID':<5}{'Date':<12}{'Destination':<25}{'City':<15}{'Seats Avail.':<12}")
                result_list.append("-" * 70)
                for trip in trips:
                     booked = trip['BookedSeats'] if trip['BookedSeats'] else 0
                     available = trip['Seats'] - booked
                     result_list.append(f"{trip['TripID']:<5}{trip['Date']!s:<12}{trip['DestinationName']:<25}{trip['CityName']:<15}{available:<12}") # Use !s for date formatting
            else:
                result_list.append("No upcoming trips currently available.")
            close_button = PushButton(result_window, text = "Close", command = result_window.destroy, align="bottom")
            close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
            result_window.show()

        except mysql.connector.Error as err:
            info("Database Error", f"Error fetching trip data: {err}")

   # --- Query 3: Customers in a given postcode area ---
    def postcode_customers():
        postcode_window = Window(query_window, title="Enter Postcode Area", width=300, height=150, bg=BG_COLOR) # Clarified Title
        Text(postcode_window, text="Enter Postcode (e.g., 'SW1A'):", color=TEXT_COLOR) # Example format
        postcode_entry = TextBox(postcode_window)

        def run_postcode_query():
            try:
                postcode = postcode_entry.value.strip().upper() # Clean input

                if not postcode:
                    info("Input Error", "Please enter a postcode area.")
                    return

                # Use parameterised query LIKE for safety!
                cursor.execute("""
                    SELECT CustomerID, FirstName, Surname, AddressLine1, Postcode
                    FROM customers
                    WHERE UPPER(Postcode) LIKE %s
                    ORDER BY Postcode, Surname
                """, (postcode + '%',)) # Match start of postcode
                customers = cursor.fetchall()

                result_window = Window(query_window, title=f"Customers in {postcode}*", width=600, height=400, bg=BG_COLOR) # Indicate wildcard
                result_list = ListBox(result_window, width="fill", height="fill", scrollbar=True)

                if customers:
                     result_list.append(f"{'ID':<5}{'Name':<30}{'Address':<35}{'Postcode':<10}") # Header
                     result_list.append("-" * 80)
                     for customer in customers:
                        result_list.append(f"{customer['CustomerID']:<5}{customer['FirstName']} {customer['Surname']:<28}{customer['AddressLine1']:<35}{customer['Postcode']:<10}")
                else:
                    result_list.append(f"No customers found starting with postcode {postcode}.")

                close_button = PushButton(result_window, text="Close", command=result_window.destroy, align="bottom")
                close_button.bg = BUTTON_BG_COLOR; close_button.text_color = BUTTON_TEXT_COLOR
                result_window.show()
                postcode_window.destroy()

            except mysql.connector.Error as err:
                info("Database Error", f"Error fetching customer data: {err}")

        ok_button = PushButton(postcode_window, text="Find Customers", command=run_postcode_query) # Clarified Button Text
        cancel_button = PushButton(postcode_window, text="Cancel", command=postcode_window.destroy)
        ok_button.bg = BUTTON_BG_COLOR; ok_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        postcode_window.show()


  # --- Query 4:  Current Income for a specific trip
    def trip_income_window():
        income_window = Window(query_window, title = "Calculate Trip Income", width = 400, height = 200, bg = BG_COLOR)
        Text(income_window, text="Enter Trip ID:", color=TEXT_COLOR)
        trip_id_entry = TextBox(income_window)

        def calculate_income():
            try:
                trip_id = trip_id_entry.value
                if not trip_id.isdigit():
                    info("Input Error", "Trip ID must be a number.")
                    return

                cursor.execute("""
                    SELECT SUM(b.BookingCost) AS TotalIncome
                    FROM bookings b
                    WHERE b.TripID = %s
                """, (trip_id,))
                result = cursor.fetchone()

                # Also get destination info for context
                cursor.execute("""
                     SELECT t.Date, d.DestinationName FROM trips t
                     JOIN destinations d ON t.DestinationID = d.DestinationID
                     WHERE t.TripID = %s
                """, (trip_id,))
                trip_info = cursor.fetchone()
                info_title = f"Income for Trip {trip_id}"
                if trip_info:
                     info_title += f" ({trip_info['DestinationName']} on {trip_info['Date']})"


                if result and result['TotalIncome'] is not None:
                    info(info_title, f"Total Booking Income: £{result['TotalIncome']:.2f}") # Format currency
                else:
                    info(info_title, f"No bookings found, or income is £0.00.") # Format currency

            except mysql.connector.Error as err:
                info("Database Error", f"Error calculating income: {err}")
            # Don't destroy window immediately, allow user to check another ID
            # finally:
            #     income_window.destroy()

        calculate_button = PushButton(income_window, text = "Calculate Income", command = calculate_income) # Clarified Text
        cancel_button = PushButton(income_window, text = "Close", command = income_window.destroy) # Changed to Close
        calculate_button.bg = BUTTON_BG_COLOR; calculate_button.text_color = BUTTON_TEXT_COLOR
        cancel_button.bg = BUTTON_BG_COLOR; cancel_button.text_color = BUTTON_TEXT_COLOR
        income_window.show()


    # --- Buttons for each query in the main Query Window---
    query_button_box = Box(query_window, layout="grid", width="fill") # Use grid for buttons

    passengers_button = PushButton(query_button_box, text="Passengers by Trip", grid=[0,0], command=lincoln_passengers)
    trips_button = PushButton(query_button_box, text="Available Trips", grid=[1,0], command=available_trips)
    postcode_button = PushButton(query_button_box, text="Customers by Postcode", grid=[0,1], command=postcode_customers)
    income_button = PushButton(query_button_box, text = "Calculate Trip Income", grid=[1,1], command = trip_income_window)

    # Style query buttons
    for button in query_button_box.children:
         if isinstance(button, PushButton):
             button.bg = BUTTON_BG_COLOR
             button.text_color = BUTTON_TEXT_COLOR

    # Back button for query window
    back_button = PushButton(query_window, text="Back to Main Menu", command=query_window.destroy, align="bottom") # Align bottom
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    query_window.show()

# --- Login and Main App ---
def check_admin_login():
    # Basic check - consider hashing passwords in a real application
    if username_entry.value.lower() == "admin" and password_entry.value == "admin":
        open_admin_main_window()
    else:
        info("Login Failed", "Incorrect username or password.")
        # Optionally clear password field: password_entry.value = ""


def open_admin_login_window():
    app.hide()
    global admin_login_window, username_entry, password_entry # Keep global if needed by check_admin_login
    admin_login_window = Window(app, title="Admin Login", width=300, height=200, bg=BG_COLOR)
    Text(admin_login_window, text="Username:", color=TEXT_COLOR)
    username_entry = TextBox(admin_login_window, width="fill") # Fill width
    Text(admin_login_window, text="Password:", color=TEXT_COLOR)
    password_entry = TextBox(admin_login_window, hide_text=True, width="fill") # Fill width

    button_box = Box(admin_login_window, layout="grid", width="fill") # Grid for buttons
    login_button = PushButton(button_box, text="Login", grid=[0,0], command=check_admin_login)
    # Back button goes to the initial App screen
    back_button = PushButton(button_box, text="Back", grid=[1,0], command=lambda: go_back(admin_login_window, app))

    login_button.bg = BUTTON_BG_COLOR; login_button.text_color = BUTTON_TEXT_COLOR
    back_button.bg = BUTTON_BG_COLOR; back_button.text_color = BUTTON_TEXT_COLOR
    admin_login_window.show()



# --- Main App Setup ---
app = App("Silver Dawn Coaches", layout="grid", bg=BG_COLOR, width=800, height=600)

# Logo - Span across 2 columns, 1 row
logo = Picture(app, image="silverDawnLogo.png", grid=[0, 0, 2, 1])
# Ensure the image file 'silverDawnLogo.png' is in the same directory or provide the full path.
if not logo.image: # Check if image loaded
    Text(app, text="[Logo Image Not Found]", color="yellow", grid=[0, 0, 2, 1])


# Title - Span across 2 columns, 1 row, below logo
title = Text(app, text="SILVER DAWN COACHES\nBOOKING & DATA SYSTEM", size=16, font="Arial", grid=[0, 1, 2, 1], color=TEXT_COLOR) # Simplified title


# Role Selection Buttons - Place side-by-side below title
button_container = Box(app, grid=[0, 2, 2, 1], layout="grid") # Box to hold buttons
admin_button = PushButton(button_container, text="Admin Login", grid=[0,0], command=open_admin_login_window, align="left", width=15) # Width set
staff_button = PushButton(button_container, text="Staff Menu", grid=[1,0], command=open_staff_window, align="left", width=15) # Width set

admin_button.bg = BUTTON_BG_COLOR; admin_button.text_color = BUTTON_TEXT_COLOR
staff_button.bg = BUTTON_BG_COLOR; staff_button.text_color = BUTTON_TEXT_COLOR


# Set column/row weights for resizing behavior (optional but good)
app.tk.grid_columnconfigure(0, weight=1)
app.tk.grid_columnconfigure(1, weight=1)
app.tk.grid_rowconfigure(0, weight=1) # Logo area
app.tk.grid_rowconfigure(1, weight=0) # Title area
app.tk.grid_rowconfigure(2, weight=0) # Button area


app.display()

# --- Close Connection ---
if conn and conn.is_connected():
    cursor.close()
    conn.close()
    print("Database connection closed.")