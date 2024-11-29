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
        tables = pd.read_sql(query, connection)  # fetches the query result into dataframe
        connection.close()
        return tables.iloc[:, 0].tolist()  # Extract table names
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
            conditions.append("Seat_Availability >= %s")
            params.append(filters["seat_availability"])

        # Combine conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        try:
            # Execute query with parameters
            data = pd.read_sql(base_query, connection, params=params)

            # Add derived columns for Bus Type categorization
            data["Seating_Type"] = data["Bus_Type"].apply(
                lambda x: "Sleeper" if "Sleeper" in x else "Seater"
            )
            data["Comfort_Type"] = data["Bus_Type"].apply(
                lambda x: "AC" if "AC" in x else "Non-AC"
            )

            connection.close()
            return data
        except Exception as e:
            st.error(f"Error executing query: {e}")
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
            # Fetch Bus Type Options
            bus_type_options = get_filter_options("Bus_Type", selected_table)
            route_name_options = get_filter_options("Route_Name", selected_table)

            # Define combined filter options
            combined_options = [
                "Sleeper AC", "Sleeper Non-AC", "Seater AC", "Seater Non-AC"
            ]

            selected_route_name = st.multiselect("Select Route Name", route_name_options)
            Start_of_Journey = st.slider('Select start time',
                                         value=(pd.to_datetime('08:00').time(), pd.to_datetime('18:00').time()), format="HH:mm")
            End_of_Journey = st.slider('Select end time',
                                       value=(pd.to_datetime('10:00').time(), pd.to_datetime('20:00').time()), format="HH:mm")
            selected_combination = st.multiselect("Select Seat Type Combination", combined_options)
            price_range = st.slider("Select Price Range", 200, 3000, (200, 2000))  # Adjust min/max as needed
            star_rating = st.slider("Star Rating", 0.0, 5.0, (0.0, 5.0))
            seat_availability = st.slider("Available Seats", 1, 60)

            # Define Filters
            filters = {
                "bus_type": bus_type_options,
                "route_name": selected_route_name,
                "price_range": price_range,
                "star_rating": star_rating,
                "seat_availability": seat_availability,
                "Start_of_Journey": Start_of_Journey,
                "End_of_Journey": End_of_Journey
            }

            # Fetch and Display Filtered Data
            data = fetch_filtered_data_with_bus_type(selected_table, filters)

            if not data.empty:
                # Apply additional filtering for combined Bus Type options
                if selected_combination:
                    def match_combination(row):
                        # Convert the Bus_Type to lowercase for case-insensitive comparison
                        bus_type = row["Bus_Type"].lower()

                        # Determine the Seating_Type (Seater or Sleeper) by checking if "seater" or "sleeper" is in Bus_Type
                        seating = "Sleeper" if "sleeper" in bus_type else "Seater"

                        # Determine the Comfort_Type (AC or Non-AC) by checking if "ac" or "non ac" is in Bus_Type
                        comfort = "Non-AC" if "non ac" in bus_type else "AC"

                        # Combine the seating and comfort types
                        bus_combination = f"{seating} {comfort}"

                        # Check if the combination is in the selected combinations, case-insensitive
                        return bus_combination.lower() in [item.lower() for item in selected_combination]

                    # Apply the match_combination function to filter the data
                    data = data[data.apply(match_combination, axis=1)]

                # Display the filtered data
                st.subheader(f"Filtered Results from {selected_table}")
                st.write(f"Number of records: {len(data)}")
                st.dataframe(data)

            else:
                st.warning("No data found with the selected filters.")
    else:
        st.warning("No tables found in the database.")

elif r == "About us":
    st.title("About Us")
    st.write("This Streamlit app connects to a MySQL database and allows users to explore bus data from the RedBus database. Users can dynamically filter data based on various parameters such as bus type, route name, price range, star rating, and seat availability. The app also provides options to combine bus types (e.g., Sleeper AC, Seater Non-AC) for more precise filtering. The results are displayed in an interactive table, offering insights into the available bus services based on user-selected criteria.")
