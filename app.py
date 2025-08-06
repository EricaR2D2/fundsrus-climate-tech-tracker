import streamlit as st
import pandas as pd

# Configure Streamlit page for wide layout and better visibility
st.set_page_config(
    page_title="FundsRUS - Climate Tech Funding Tracker",
    page_icon="🌍",
    layout="wide",  # Use wide layout to utilize full screen
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .logo-container {
        flex-shrink: 0;
    }
    .title-container {
        flex-grow: 1;
    }
    .funds-title {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #FFB347 0%, #4A90E2 50%, #87CEEB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .subtitle {
        color: #4A90E2;
        font-size: 1.2rem;
        font-style: italic;
        margin-top: 10px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header with logo and title
col1, col2 = st.columns([1, 4])

with col1:
    # Display the logo
    st.image("earth-sunrise-from-space-wallpaper-preview.jpg", width=150)

with col2:
    # Title with custom styling
    st.markdown('<h1 class="funds-title">FundsRUS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Track funding rounds, investors, and trends in climate technology startups</p>', unsafe_allow_html=True)

def load_data(filepath):
    """
    Load data from a JSON file and return as a pandas DataFrame.

    Args:
        filepath (str): Path to the JSON file

    Returns:
        pd.DataFrame: DataFrame with 'Funding Date' column converted to datetime
    """
    import json

    try:
        # Read the JSON file as text first
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read().strip()

        # Wrap the content in square brackets to make it a proper JSON array
        if not content.startswith('['):
            content = '[' + content + ']'

        # Parse the JSON
        data = json.loads(content)

        # Create DataFrame from the list of dictionaries
        df = pd.DataFrame(data)

        # Convert 'Funding Date' column to datetime objects
        df['Funding Date'] = pd.to_datetime(df['Funding Date'])

        return df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

# Main part of the script
if __name__ == "__main__":
    # Define the path to the data file
    data_file_path = "data.json"

    # Load the data
    df = load_data(data_file_path)

    # Check if data was loaded successfully
    if not df.empty:
        # Create main tabs
        tab1, tab2 = st.tabs(["Funding Tracker", "Glossary"])

        with tab1:
            # Sidebar filters
            st.sidebar.header("Filters")

            # Climate Vertical multi-select filter
            climate_verticals = df['Climate Vertical'].unique().tolist()
            selected_verticals = st.sidebar.multiselect(
                "Climate Vertical",
                options=climate_verticals,
                default=climate_verticals  # Show all by default
            )

            # Funding Stage select box filter
            funding_stages = ["All"] + df['Funding Stage'].unique().tolist()
            selected_stage = st.sidebar.selectbox(
                "Funding Stage",
                options=funding_stages,
                index=0  # Default to "All"
            )

            # Investor Name text input filter
            investor_search = st.sidebar.text_input(
                "Investor Name",
                placeholder="e.g., Breakthrough Energy Ventures"
            )

            # Filter the DataFrame based on user selections
            filtered_df = df.copy()

            # Apply Climate Vertical filter
            if selected_verticals:
                filtered_df = filtered_df[filtered_df['Climate Vertical'].isin(selected_verticals)]

            # Apply Funding Stage filter
            if selected_stage != "All":
                filtered_df = filtered_df[filtered_df['Funding Stage'] == selected_stage]

            # Apply Investor Name filter (case-insensitive search in both investor columns)
            if investor_search:
                investor_mask = (
                    filtered_df['Lead Investor(s)'].str.contains(investor_search, case=False, na=False) |
                    filtered_df['Other Investors'].str.contains(investor_search, case=False, na=False)
                )
                filtered_df = filtered_df[investor_mask]

            # KPI Dashboard Section
            st.subheader("📊 Dashboard Overview")

            # Create 3 columns for KPI metrics
            col1, col2, col3 = st.columns(3)

            # Calculate KPIs from filtered data
            total_funding = filtered_df['Amount'].sum()
            num_deals = len(filtered_df)
            avg_deal_size = total_funding / num_deals if num_deals > 0 else 0

            # Format total funding to be human-readable
            def format_currency(amount):
                if amount >= 1_000_000_000:
                    return f"${amount / 1_000_000_000:.1f}B"
                elif amount >= 1_000_000:
                    return f"${amount / 1_000_000:.1f}M"
                elif amount >= 1_000:
                    return f"${amount / 1_000:.1f}K"
                else:
                    return f"${amount:.0f}"

            # Display KPI metrics
            with col1:
                st.metric(
                    label="Total Funding Raised",
                    value=format_currency(total_funding)
                )

            with col2:
                st.metric(
                    label="Number of Deals",
                    value=f"{num_deals:,}"
                )

            with col3:
                st.metric(
                    label="Average Deal Size",
                    value=format_currency(avg_deal_size)
                )

            # Funding by Vertical Chart
            st.subheader("Funding by Vertical")

            if not filtered_df.empty:
                # Group by Climate Vertical and sum the amounts
                vertical_funding = filtered_df.groupby('Climate Vertical')['Amount'].sum().sort_values(ascending=False)

                # Create bar chart
                st.bar_chart(vertical_funding)
            else:
                st.info("No data available for the selected filters.")

            # Add subheader for the data table
            st.subheader("Recent Funding Events")

            # Display filtered data info
            st.write(f"📊 **Showing {len(filtered_df)} of {len(df)} funding events**")

            # Configure pandas display options for better visibility
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 100)

            # Use the filtered DataFrame directly
            display_df = filtered_df

            # Display the filtered DataFrame with enhanced formatting
            st.dataframe(
                display_df,
                use_container_width=True,  # Use full container width
                height=600,  # Set a good height to show more rows
                column_config={
                    "Company Name": st.column_config.TextColumn(
                        "Company Name",
                        width="medium"
                    ),
                    "Funding Date": st.column_config.DateColumn(
                        "Funding Date",
                        format="YYYY-MM-DD",
                        width="small"
                    ),
                    "Amount": st.column_config.NumberColumn(
                        "Amount",
                        width="medium"
                    ),
                    "Currency": st.column_config.TextColumn(
                        "Currency",
                        width="small"
                    ),
                    "Funding Stage": st.column_config.TextColumn(
                        "Funding Stage",
                        width="medium"
                    ),
                    "Lead Investor(s)": st.column_config.TextColumn(
                        "Lead Investor(s)",
                        width="large"
                    ),
                    "Other Investors": st.column_config.TextColumn(
                        "Other Investors",
                        width="large"
                    ),
                    "Climate Vertical": st.column_config.TextColumn(
                        "Climate Vertical",
                        width="medium"
                    ),
                    "Company Description": st.column_config.TextColumn(
                        "Company Description",
                        width="large"
                    ),
                    "Source URL": st.column_config.LinkColumn(
                        "Source URL",
                        width="small"
                    )
                }
            )

        with tab2:
            # Glossary Tab Content
            st.header("📚 Key Terminology")

            st.subheader("Pre-Seed/Seed Round")
            st.write("""
            **Pre-Seed** and **Seed** rounds are the earliest stages of startup funding. Pre-seed typically involves
            initial capital from founders, friends, and family to validate the business idea. Seed rounds follow,
            providing funding to develop the product, conduct market research, and build an initial team.
            These rounds usually range from $50K to $2M.
            """)

            st.subheader("Series A, B, C")
            st.write("""
            **Series A, B, C** represent sequential funding rounds as startups grow:

            - **Series A**: First major institutional funding round (typically $2M-$15M) to scale the product and expand the team
            - **Series B**: Growth funding (typically $10M-$50M) to expand market reach and accelerate revenue
            - **Series C**: Later-stage funding (typically $30M+) for market expansion, acquisitions, or preparing for IPO
            """)

            st.subheader("Venture Capital (VC)")
            st.write("""
            **Venture Capital (VC)** refers to investment firms that provide funding to high-growth startups in exchange
            for equity ownership. VCs typically invest in companies with strong growth potential and aim for significant
            returns through eventual exits (IPO or acquisition). They often provide mentorship and strategic guidance
            beyond just capital.
            """)

            st.subheader("Lead Investor")
            st.write("""
            The **Lead Investor** is the primary investor in a funding round who typically contributes the largest
            portion of capital and takes the lead in negotiating terms, conducting due diligence, and structuring
            the deal. They often secure a board seat and play an active role in guiding the company's strategic direction.
            """)

            st.subheader("Climate Vertical")
            st.write("""
            **Climate Vertical** refers to specific sectors within the climate technology space, such as renewable energy,
            carbon capture, sustainable transportation, or green agriculture. Each vertical addresses different aspects
            of climate change mitigation or adaptation, allowing investors to focus on particular areas of environmental impact.
            """)

    else:
        st.warning("No data to display. Please check your data.json file.")