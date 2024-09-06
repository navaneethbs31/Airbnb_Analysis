import pymongo
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
import matplotlib.pyplot as plt
from urllib.parse import quote_plus

# MongoDB connection
username = "xxxx"
password = "xxxxx"
cluster_address = "your cluster address"

encoded_username = quote_plus(username)
encoded_password = quote_plus(password)
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_address}/?retryWrites=true&w=majority"

client = pymongo.MongoClient(uri)
db = client.sample_airbnb
collection = db.listingsAndReviews

data = collection.find()
df = pd.DataFrame(list(data))

# Convert non-hashable columns to strings
for col in df.columns:
    if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
        df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)

df = df.drop_duplicates()

# Handle missing values
fill_values = {
    'price': df['price'].median(),  # Example: fill missing prices with median
}

if 'rating' in df.columns:
    fill_values['rating'] = df['rating'].mean()  # Fill missing ratings with mean if 'rating' column exists

df = df.fillna(fill_values)
df['price'] = df['price'].astype(float)

st.title('Airbnb Listings Analysis')

st.write("Available Columns:")
st.write(df.columns)

st.write("Sample Data:")
st.write(df.head())

# Check the column related to neighborhood overview
location_column = 'neighborhood_overview'  # Update with the available column name if different

if location_column in df.columns:
    st.sidebar.header('Filter options')
    selected_location = st.sidebar.text_input('Search Neighborhood Overview', '')

    # Filter based on the neighborhood overview text (basic text search)
    filtered_df = df[df[location_column].str.contains(selected_location, case=False, na=False)]

    min_price = st.sidebar.slider('Minimum Price', 0, int(df['price'].max()), 0)
    max_price = st.sidebar.slider('Maximum Price', 0, int(df['price'].max()), int(df['price'].max()))

    filtered_df = filtered_df[(filtered_df['price'] >= min_price) & (filtered_df['price'] <= max_price)]

    if filtered_df.empty:
        st.write("No data available for the selected filters.")
    else:
        st.write("Filtered Data:")
        st.write(filtered_df)

else:
    st.write(f"Column '{location_column}' not found in the data.")

# Price Distribution by Location (No geospatial data available)
fig = px.histogram(df, x='price', title='Price Distribution')
st.plotly_chart(fig)

# Availability Over Time (if dates are present)
if 'availability.start_date' in df.columns and 'availability.end_date' in df.columns:
    df['availability_duration'] = pd.to_datetime(df['availability.end_date'], errors='coerce') - pd.to_datetime(df['availability.start_date'], errors='coerce')
    df['availability_duration'] = df['availability_duration'].dt.days

    fig, ax = plt.subplots()
    ax.plot(df['availability_duration'], marker='o', linestyle='-', color='b')
    ax.set_title('Availability Duration Over Listings')
    ax.set_xlabel('Listing Index')
    ax.set_ylabel('Availability (days)')
    st.pyplot(fig)

# Save cleaned data to CSV
df.to_csv('cleaned_airbnb_data.csv', index=False)
