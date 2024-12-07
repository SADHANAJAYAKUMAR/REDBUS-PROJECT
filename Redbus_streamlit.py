import streamlit as st
import mysql.connector
import pandas as pd

# Function to establish a connection to the MySQL database
def create_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="2312",
            database="redbus"
        )
    except mysql.connector.Error as err:
        st.error(f"Database connection failed: {err}")
        return None

# Function to fetch table names dynamically
@st.cache_data
def fetch_tables():
    connection = create_connection()
    if connection:
        query = "SHOW TABLES"
        try:
            tables = pd.read_sql(query, connection)
            connection.close()
            return tables.iloc[:, 0].tolist()  # Extract table names
        except Exception as e:
            st.error(f"Error fetching table names: {e}")
            connection.close()
            return []
    else:
        return []

# Function to fetch filter options dynamically
@st.cache_data
def get_filter_options(column_name, table_name):
    connection = create_connection()
    if connection:
        query = f"SELECT DISTINCT {column_name} FROM {table_name}"
        try:
            options = pd.read_sql(query, connection)
            connection.close()
            return options[column_name].dropna().tolist()
        except Exception as e:
            st.error(f"Error fetching options for {column_name}: {e}")
            connection.close()
            return []
    else:
        return []

# Function to retrieve filtered data
@st.cache_data
def fetch_filtered_data_with_bus_type(table_name, filters):
    connection = create_connection()
    if connection:
        base_query = f"SELECT * FROM {table_name}"
        conditions = []
        params = []

        # Build query based on user inputs
        if filters["bus_type"]:
            conditions.append(f"Bus_Type IN ({','.join(['%s'] * len(filters['bus_type']))})")
            params.extend(filters["bus_type"])

        if filters["route_name"]:
            conditions.append(f"Route_Name IN ({','.join(['%s'] * len(filters['route_name']))})")
            params.extend(filters["route_name"])

        if filters["Start_of_Journey"]:
            start_time_min, start_time_max = filters["Start_of_Journey"]
            conditions.append("CAST(Start_of_Journey AS TIME) BETWEEN %s AND %s")
            params.extend([start_time_min, start_time_max])

        if filters["End_of_Journey"]:
            end_time_min, end_time_max = filters["End_of_Journey"]
            conditions.append("CAST(End_of_Journey AS TIME) BETWEEN %s AND %s")
            params.extend([end_time_min, end_time_max])

        if filters["price_range"]:
            min_price, max_price = filters["price_range"]
            conditions.append("Price BETWEEN %s AND %s")
            params.extend([min_price, max_price])

        if filters["star_rating"]:
            min_rating, max_rating = filters["star_rating"]
            conditions.append("Star_Rating BETWEEN %s AND %s")
            params.extend([min_rating, max_rating])

        if filters["seat_availability"]:
            min_seats, max_seats = filters["seat_availability"]
            conditions.append("Seat_Availability BETWEEN %s AND %s")
            params.extend([min_seats, max_seats])

        # Combine conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        try:
            # Execute query
            data = pd.read_sql(base_query, connection, params=params)
            connection.close()
            return data
        except Exception as e:
            st.error(f"Error executing query: {e}")
            connection.close()
            return pd.DataFrame()
    else:
        return pd.DataFrame()

# Streamlit App
r = st.sidebar.radio("Navigation", ["Home", "About us"])

if r == "Home":
    st.title("RedBus Data")

    # Fetch all table names
    tables = fetch_tables()

    if tables:
        # Table selection
        selected_table = st.selectbox("Select a state bus detail", tables)

        if selected_table:
            # Fetch filter options
            bus_type_groups = {
            "AC Sleeper Buses": [
                "A/C Sleeper (2+1)", "Volvo Multi Axle B9R A/C Sleeper (2+1)",
                "Bharat Benz A/C Sleeper (2+1)", "Volvo A/C Sleeper (2+1)",
                "VE A/C Sleeper (2+1)", "Volvo 9600 Multi-Axle A/C Sleeper (2+1)",
                "A/C Volvo B11R Multi-Axle Sleeper (2+1)", "AC Sleeper (2+1)"
            ],
            "AC Seater Buses": [
                "INDRA(A.C. Seater)", "A/C Seater Push Back (2+2)", "Volvo AC Seater (2+2)",
                "Electric A/C Seater (2+2)", "Himsuta AC Seater Volvo/Scania 2+2",
                "Shatabdi AC Seater 2+2", "Janrath AC Seater 2+3", "Pink Express AC Seater 2+2",
                "AC Seater Hvac 2+2", "Low Floor AC Seater 2+2", "A/C Executive (2+3)"
            ],
            "AC Semi Sleeper Buses": [
                "Volvo Multi-Axle I-Shift B11R Semi Sleeper (2+2)", "A/C Semi Sleeper (2+2)",
                "Scania Multi-Axle AC Semi Sleeper (2+2)", "Mercedes A/C Semi Sleeper (2+2)",
                "Volvo A/C Semi Sleeper (2+2)", "Volvo A/C B11R Multi Axle Semi Sleeper (2+2)",
                "Volvo 9600 A/C Semi Sleeper (2+2)", "Bharat Benz A/C Semi Sleeper (2+2)"
            ],
            "AC Seater/Sleeper Buses": [
                "A/C Seater / Sleeper (2+1)", "VE A/C Seater / Sleeper (2+1)",
                "Bharat Benz A/C Seater / Sleeper (2+1)", "A/C Seater / Sleeper (2+2)",
                "Volvo Multi Axle B11R AC Seater\Sleeper (2+1)"
            ],
            "Non-AC Sleeper Buses": [
                "NON A/C Sleeper (2+1)", "STAR LINER(NON-AC SLEEPER 2+1)"
            ],
            "Non-AC Seater Buses": [
                "Express(Non AC Seater)", "SUPER LUXURY (NON-AC, 2 + 2 PUSH BACK)", "Non AC Seater (2+2)",
                "Non AC Seater (2+3)", "Ordinary 3+2 Non AC Seater", "Express Non AC Seater 2+3",
                "Super Fast Non AC Seater (2+3)", "Swift Deluxe Non AC Air Bus (2+2)",
                "Ordinary Non AC Seater 2+3", "Rajdhani Non AC Seater 2+3"
            ],
            "Non-AC Seater/Sleeper Buses": [
                "NON A/C Seater / Sleeper (2+1)", "NON A/C Seater/ Sleeper (2+1)"
            ],
            "Luxury Buses": [
                "Super Luxury (Non AC Seater 2+2 Push Back)", "Rajdhani (AC Semi Sleeper 2+2)",
                "RAJDHANI (A.C. Semi Sleeper)", "Deluxe AC Seater 2+2"
            ],
            "Volvo Buses": [
                "Volvo Multi-Axle A/C Sleeper (2+1)", "Volvo Multi-Axle I-Shift A/C Semi Sleeper (2+2)",
                "Volvo A/C Semi Sleeper (2+2)", "Volvo A/C B11R Multi Axle Semi Sleeper (2+2)",
                "Volvo Multi-Axle I-Shift B11R Semi Sleeper (2+2)", "Volvo 9600 A/C Semi Sleeper (2+2)",
                "Volvo A/C Sleeper (2+1)", "Volvo AC Seater (2+2)"
            ]
        }
            selected_bus_type = st.multiselect("Select Seat Type",options=list(bus_type_groups.keys()),
                     format_func=lambda x: f"{x} ({len(bus_type_groups[x])} options)"
)

            # Translate selected group names into actual bus type values
            bus_type_values = [bus for group in selected_bus_type for bus in bus_type_groups[group]]

            route_name_options = get_filter_options("Route_Name", selected_table)
            selected_route_name = st.multiselect("Select Route Name", route_name_options)

            Start_of_Journey = st.slider(
                "Select start time",
                value=(pd.to_datetime('08:00').time(), pd.to_datetime('18:00').time()), 
                format="HH:mm"
            )
            End_of_Journey = st.slider(
                "Select end time",
                value=(pd.to_datetime('10:00').time(), pd.to_datetime('20:00').time()), 
                format="HH:mm"
            )

            price_range = st.slider("Select Price Range", 200, 3000, (200, 1500))  # Adjust min/max as needed
            star_rating = st.slider("Star Rating", 0.0, 5.0, (2.0, 4.0))
            seat_availability = st.slider("Available Seats", 1, 60, (1, 20))

            # Define Filters
            filters = {
                "bus_type": bus_type_values,
                "route_name": selected_route_name,
                "price_range": price_range,
                "star_rating": star_rating,
                "seat_availability": seat_availability,
                "Start_of_Journey": Start_of_Journey,
                "End_of_Journey": End_of_Journey
            }

            # Fetch and display filtered data
            data = fetch_filtered_data_with_bus_type(selected_table, filters)

            if not data.empty:
                st.subheader(f"Filtered Results from {selected_table}")
                st.write(f"Number of records: {len(data)}")
                st.dataframe(data)
            else:
                st.warning("No data found with the selected filters.")
    else:
        st.warning("No tables found in the database.")

elif r == "About us":
    st.title("About Us")
    st.write("""
        This Streamlit app connects to a MySQL database and allows users to explore bus data from the RedBus database.
        Users can dynamically filter data based on various parameters such as bus type, route name, price range, 
        star rating, and seat availability. The app displays results in an interactive table.
    """)
