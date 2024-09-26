import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
from PIL import Image
import warnings

warnings.filterwarnings('ignore')

# Set up the Streamlit page configuration
st.set_page_config(page_title="AirBnb Analysis", page_icon=":bar_chart:", layout="wide")

# Add the Airbnb logo
st.image("airbnb_logo.png", width=100)

# Title and subtitle for the app
st.markdown("<h1 style='text-align: center;'> 📊 AirBnb Analysis</h1>", unsafe_allow_html=True)
st.markdown('<style>div.block-container{padding-top:3rem;}</style>', unsafe_allow_html=True)

# Sample introduction or description
st.subheader("Welcome to the Airbnb Analysis dashboard!")
st.write("This application allows you to explore various aspects of Airbnb listings, including availability, pricing, and neighborhood insights.")

# Navigation Menu
SELECT = option_menu(
    menu_title=None,
    options=["Home", "Explore Data"],
    icons=["house", "bar-chart"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "white"},
        "icon": {"color": "black", "font-size": "20px"},
        "nav-link": {"font-size": "20px", "text-align": "center", "margin": "-2px", "--hover-color": "#FF5A5F"},
        "nav-link-selected": {"background-color": "#FF5A5F"}
    }
)

# ----------------Home----------------------#
if SELECT == "Home":
    col1,col2,col3=st.columns(3)
    with col2:
        st.image("airbnb_logo.png",width=400)
    st.subheader("Overview")
    st.write(
        "Airbnb is an American company based in San Francisco that operates an online marketplace for short- and long-term homestays and experiences. "
        "The company acts as a broker and charges a commission from each booking."
    )
    st.subheader('Skills Acquired from This Project')
    skills = [
        "Python Scripting",
        "Data Preprocessing",
        "Data Visualization",
        "Exploratory Data Analysis (EDA)",
        "Streamlit",
        "MongoDB",
        "Power BI"
    ]
    st.write(", ".join(skills))

    st.subheader('Domain Knowledge')
    domains = [
        "Travel Industry",
        "Property Management",
        "Tourism"
    ]
    st.write(", ".join(domains))

# ----------------Explore Data----------------------#
if SELECT == "Explore Data":
    try:
        # Load the dataset
        df = pd.read_csv("cleaned_airbnb.csv", encoding="ISO-8859-1")

    except Exception as e:
        st.error(f"Error loading default dataset: {e}")

    st.sidebar.header("Choose your filter:")

    # Check for expected columns
    if 'address.suburb' in df.columns:
        neighbourhood = st.sidebar.multiselect("Pick the neighbourhood", df["address.suburb"].unique())
    else:
        st.error("Expected column 'address.suburb' not found in the dataset.")
        neighbourhood = []

    if not neighbourhood:
        df_filtered = df.copy()
    else:
        df_filtered = df[df["address.suburb"].isin(neighbourhood)]

    room_type_df = df_filtered.groupby(by=["room_type"], as_index=False)["price"].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Room Type View Data")
        fig = px.bar(room_type_df, x="room_type", y="price", text=['${:,.2f}'.format(x) for x in room_type_df["price"]],
                     template="seaborn")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Neighbourhood View Data")
        neighbourhood_group = df_filtered.groupby(by="address.suburb", as_index=False)["price"].sum()
        fig = px.pie(neighbourhood_group, values="price", names="address.suburb", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Composition")
    col3, col4 = st.columns(2)
    with col3:
        # Room Type Composition Pie Chart
        room_type_count = df_filtered['room_type'].value_counts().reset_index()
        room_type_count.columns = ['room_type', 'count']  # Rename columns for clarity
        fig = px.pie(room_type_count, values='count', names='room_type', title='Room Type Composition', hole=0.4)
        st.plotly_chart(fig)
    with col4:
        property_type_count = df_filtered['property_type'].value_counts().reset_index()
        property_type_count.columns = ['property_type', 'count']  # Rename columns for clarity
        fig = px.pie(property_type_count, values='count', names='property_type', title='Property Type Composition',
                     hole=0.4)
        st.plotly_chart(fig)

    st.subheader("Price Distribution")
    # Facet Grid of Histograms by Room Type
    fig = px.histogram(df_filtered, x="price", color="room_type", facet_col="room_type", nbins=30,
                       title="Price Distribution by Room Type")
    st.plotly_chart(fig)

    # Price Distribution Histogram
    fig = px.histogram(df_filtered, x="price", nbins=30, title="Total Price Distribution", template="seaborn")
    st.plotly_chart(fig)

    # Create availability categories using the correct column name
    df_filtered['availability_category'] = pd.cut(df_filtered['availability.availability_365'],
                                                  bins=[0, 30, 90, 180, 365],
                                                  labels=['0-30 Days', '31-90 Days', '91-180 Days', '181-365 Days'])

    availability_count = df_filtered['availability_category'].value_counts().reset_index()
    availability_count.columns = ['availability_category', 'count']

    st.header("Listings of Available Properties")
    fig = px.bar(availability_count,
                 x='availability_category',
                 y='count',
                 text='count',
                 title='Number of Listings by Availability Category',
                 template='seaborn')
    st.plotly_chart(fig)

    # Function to safely extract longitude and latitude from the string
    def extract_coordinates(coord_str):
        if isinstance(coord_str, str):
            coords = coord_str.split(',')
            if len(coords) == 2:
                return pd.Series([float(coords[0].strip()), float(coords[1].strip())])  # Longitude, Latitude
        return pd.Series([None, None])  # Return None if the format is incorrect


    # Apply the function to extract coordinates
    df_filtered[['longitude', 'latitude']] = df_filtered['address.location.coordinates'].apply(extract_coordinates)

    # Initial filter for properties that are available
    available_properties = df_filtered[df_filtered['availability.availability_365'] > 0]

    # Slider for minimum availability with a unique key
    min_availability = st.slider("Minimum Availability (days)", 0, 365, 0, key="min_availability_slider")
    st.write(":gray[Drag to select the minimum available days]")

    # Further filter based on slider input
    available_properties = available_properties[
        available_properties['availability.availability_365'] >= min_availability]

    st.subheader("Available Properties")
    df_s=available_properties[['name', 'address.suburb', 'room_type', 'price', 'availability.availability_365']]
    df_s=df_s.rename(columns={
        "name":"Name",
        "address.suburb":"Neighbourhood",
        "room_type":"Room Type",
        "price":"Price",
        "availability.availability_365":"Availability"
    })
    df_s=df_s.sort_values(by="Availability",ascending=True)
    st.dataframe(df_s.reset_index(drop=True), use_container_width=True)

    # Prepare data for the map
    if 'latitude' in df_filtered.columns and 'longitude' in df_filtered.columns:
        # Use the same filtered properties
        map_data = available_properties[['latitude', 'longitude']]

        # Display the map
        if not map_data.empty and map_data['latitude'].notnull().all() and map_data['longitude'].notnull().all():
            st.subheader("Map View of Available Properties")
            st.map(map_data)
        else:
            st.write("No properties available for the selected criteria.")
    else:
        st.write("Coordinates data is required for the map view.")

    #top 10 reviews
    top_reviews = df_filtered.nlargest(10, 'reviews_per_month')
    st.subheader("Top 10 Listings with the Most Reviews")
    fig = px.bar(top_reviews, x='name', y='reviews_per_month', text='reviews_per_month')
    st.plotly_chart(fig)


    st.subheader("Overview of Properties")
    df_sample = df_filtered[["address.suburb","room_type", "minimum_nights","amenities","bedrooms","host.host_name","price"]].head(5)
    df_sample = df_sample.rename(columns={
        "address.suburb": "Neighbourhood",
        "room_type": "Room Type",
        "minimum_nights": "Minimum Nights",
        "amenities": "Amenities",
        "bedrooms": "Bedrooms",
        "host.host_name": "Host Name",
        "price": "Price"
    })
    df_sample = df_sample.sort_values(by="Price", ascending=True)
    #st.dataframe(df_sample.reset_index(drop=True), use_container_width=True)
    #st.table(df_sample)
    # Display without index using HTML
    st.markdown(df_sample.to_html(index=False), unsafe_allow_html=True)
