import pymongo
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
import matplotlib.pyplot as plt
from urllib.parse import quote_plus

# MongoDB connection
username = "navabs"
password = "123456@nava"
cluster_address = "ac-z5l2sxl-shard-00-00.a4spb07.mongodb.net"

# Encode the username and password
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

# Construct the MongoDB connection URI
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_address}/?retryWrites=true&w=majority"

# Create a MongoClient instance
client = pymongo.MongoClient(uri)
db = client.sample_airbnb
collection = db.listingsAndReviews

# Retrieve data from MongoDB
data = collection.find()
df = pd.DataFrame(list(data))

# Convert non-hashable columns to strings
for col in df.columns:
    if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
        df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)

# Drop duplicates
df = df.drop_duplicates()

# Handle missing values
df = df.fillna({
    'price': df['price'].median(),  # Example: fill missing prices with median
    # Add other fields as needed
})

# Convert data types
df['price'] = df['price'].astype(float)

# Check if 'location.coordinates' column exists and flatten if necessary
if 'location.coordinates' in df.columns:
    df[['longitude', 'latitude']] = pd.DataFrame(df['location.coordinates'].tolist(), index=df.index)

# Streamlit application
st.title('Airbnb Listings Analysis')

# Print the column names and a sample of the data for debugging
st.write("Columns in DataFrame:")
st.write(df.columns)

st.write("Sample Data:")
st.write(df.head())

# Interactive map
if 'neighbourhood' in df.columns:
    st.sidebar.header('Filter options')
    selected_location = st.sidebar.selectbox('Select Location', df['neighbourhood'].unique())

    filtered_df = df[df['neighbourhood'] == selected_location]

    if filtered_df.empty:
        st.write("No data available for the selected location.")
    else:
        map_center = [filtered_df['latitude'].mean(), filtered_df['longitude'].mean()]
        m = folium.Map(location=map_center, zoom_start=12)

        for _, row in filtered_df.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"Price: ${row['price']}, Rating: {row['rating']}"
            ).add_to(m)

        st.write(m)
else:
    st.write("Column 'neighbourhood' not found in the data.")

# Price Distribution by Location
if 'longitude' in df.columns and 'latitude' in df.columns:
    fig = px.scatter(df, x='longitude', y='latitude', color='price',
                     title='Price Distribution by Location')
    st.plotly_chart(fig)

# Availability Over Time
if 'availability.start_date' in df.columns and 'availability.end_date' in df.columns:
    df['availability_duration'] = pd.to_datetime(df['availability.end_date']) - pd.to_datetime(df['availability.start_date'])
    df['availability_duration'] = df['availability_duration'].dt.days

    fig, ax = plt.subplots()
    ax.plot(df['availability_duration'], marker='o', linestyle='-')
    ax.set_title('Availability Over Time')
    ax.set_xlabel('Listing ID')
    ax.set_ylabel('Availability (days)')

    st.pyplot(fig)

# Price Distribution in Specific Region
if 'neighbourhood' in df.columns:
    region_df = df[df['neighbourhood'] == 'Upper West Side']
    if not region_df.empty:
        fig = px.histogram(region_df, x='price', title='Price Distribution in Upper West Side')
        st.plotly_chart(fig)

# Interactive Price and Rating Over Time
if 'longitude' in df.columns and 'latitude' in df.columns:
    fig = px.scatter(df, x='longitude', y='latitude', color='price',
                     animation_frame='availability.start_date',
                     title='Interactive Price and Rating Over Time')
    st.plotly_chart(fig)

# Save cleaned data to CSV
df.to_csv('cleaned_airbnb_data.csv', index=False)
