
import streamlit as st
import pandas as pd
import math
import requests
from bs4 import BeautifulSoup
import openai
import json

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

        # Clean Amount column - replace infinite and NaN values with 0
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')  # Convert to numeric, NaN for invalid
            df['Amount'] = df['Amount'].replace([float('inf'), -float('inf')], 0)  # Replace infinite with 0
            df['Amount'] = df['Amount'].fillna(0)  # Replace NaN with 0

        return df

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_investor_summary(df, lead_only=False):
    """
    Create an investor-centric summary DataFrame from deals data.

    Args:
        df (pd.DataFrame): Original deals DataFrame
        lead_only (bool): If True, only include lead investors

    Returns:
        pd.DataFrame: Investor summary with metrics
    """
    investor_data = []

    # Get all unique investors from both columns
    all_investors = set()

    for _, row in df.iterrows():
        # Parse lead investors
        lead_investors = str(row['Lead Investor(s)']).split(', ') if pd.notna(row['Lead Investor(s)']) else []
        other_investors = str(row['Other Investors']).split(', ') if pd.notna(row['Other Investors']) else []

        # Clean and add investors (skip "Not specified")
        for investor in lead_investors:
            investor = investor.strip()
            if investor and investor != "Not specified" and investor != "nan":
                all_investors.add(investor)

        # Add other investors only if not lead_only
        if not lead_only:
            for investor in other_investors:
                investor = investor.strip()
                if investor and investor != "Not specified" and investor != "nan":
                    all_investors.add(investor)

    # Calculate metrics for each investor
    for investor in all_investors:
        investor_deals = []
        total_invested = 0
        verticals = []
        stages = []
        lead_deals = 0

        # Find all deals this investor participated in
        for _, row in df.iterrows():
            lead_investors = str(row['Lead Investor(s)']).split(', ') if pd.notna(row['Lead Investor(s)']) else []
            other_investors = str(row['Other Investors']).split(', ') if pd.notna(row['Other Investors']) else []

            # Clean investor names for comparison
            lead_investors = [inv.strip() for inv in lead_investors]
            other_investors = [inv.strip() for inv in other_investors]

            # Check participation
            is_lead = investor in lead_investors
            is_other = investor in other_investors

            if is_lead or (is_other and not lead_only):
                investor_deals.append(row)
                # Safely add amount, handling NaN and infinite values
                amount = row['Amount']
                if pd.notna(amount) and not math.isinf(amount):
                    total_invested += amount
                verticals.append(row['Climate Vertical'])
                stages.append(row['Funding Stage'])
                if is_lead:
                    lead_deals += 1

        # Calculate preferred verticals (top 2-3)
        vertical_counts = pd.Series(verticals).value_counts()
        preferred_verticals = vertical_counts.head(3).index.tolist()

        # Calculate preferred stages (top 2-3)
        stage_counts = pd.Series(stages).value_counts()
        preferred_stages = stage_counts.head(3).index.tolist()

        investor_data.append({
            'Investor Name': investor,
            'Deals Done': len(investor_deals),
            'Lead Deals': lead_deals,
            'Total Invested': total_invested,
            'Preferred Verticals': ', '.join(preferred_verticals),
            'Preferred Stages': ', '.join(preferred_stages)
        })

    # Create DataFrame and sort by total invested
    investor_df = pd.DataFrame(investor_data)
    investor_df = investor_df.sort_values('Total Invested', ascending=False).reset_index(drop=True)

    return investor_df

def get_investor_deals(df, investor_name):
    """
    Get all deals for a specific investor.

    Args:
        df (pd.DataFrame): Original deals DataFrame
        investor_name (str): Name of the investor

    Returns:
        pd.DataFrame: All deals this investor participated in
    """
    investor_deals = []

    for _, row in df.iterrows():
        lead_investors = str(row['Lead Investor(s)']).split(', ') if pd.notna(row['Lead Investor(s)']) else []
        other_investors = str(row['Other Investors']).split(', ') if pd.notna(row['Other Investors']) else []

        # Clean investor names for comparison
        lead_investors = [inv.strip() for inv in lead_investors]
        other_investors = [inv.strip() for inv in other_investors]

        if investor_name in lead_investors or investor_name in other_investors:
            # Add role information
            role = "Lead" if investor_name in lead_investors else "Other"
            row_dict = row.to_dict()
            row_dict['Role'] = role
            investor_deals.append(row_dict)

    return pd.DataFrame(investor_deals)

def categorize_deal_size(amount):
    """
    Categorize deal size into buckets relevant to funding stages.

    Args:
        amount (float): Deal amount in USD

    Returns:
        str: Deal size category
    """
    if amount < 1_000_000:
        return "Pre-Seed (<$1M)"
    elif amount <= 5_000_000:
        return "Seed ($1M-$5M)"
    elif amount <= 20_000_000:
        return "Series A ($5M-$20M)"
    else:
        return "Series B+ (>$20M)"

def add_geography_column(df):
    """
    Add geography information based on investor names and known patterns.
    This is a simplified approach - in production, you'd have a proper database.

    Args:
        df (pd.DataFrame): Original deals DataFrame

    Returns:
        pd.DataFrame: DataFrame with Geography column added
    """
    df = df.copy()

    # Simple geography mapping based on known investor patterns
    # This is a basic implementation - in reality you'd have a comprehensive database
    north_america_indicators = [
        'ventures', 'capital', 'partners', 'fund', 'investment', 'vc',
        'sequoia', 'andreessen', 'kleiner', 'accel', 'benchmark', 'greylock',
        'first round', 'union square', 'spark', 'foundry', 'insight',
        'general catalyst', 'nea', 'khosla', 'draper', 'sv angel'
    ]

    europe_indicators = [
        'european', 'london', 'berlin', 'paris', 'stockholm', 'amsterdam',
        'atomico', 'balderton', 'accel', 'index', 'northzone', 'creandum',
        'eurazeo', 'lakestar', 'rocket', 'target global'
    ]

    def determine_geography(lead_investors, other_investors):
        all_investors = str(lead_investors).lower() + ' ' + str(other_investors).lower()

        # Count indicators for each region
        na_score = sum(1 for indicator in north_america_indicators if indicator in all_investors)
        eu_score = sum(1 for indicator in europe_indicators if indicator in all_investors)

        if na_score > eu_score:
            return "North America"
        elif eu_score > na_score:
            return "Europe"
        else:
            return "Global/Other"

    # Apply geography determination
    df['Geography'] = df.apply(
        lambda row: determine_geography(row['Lead Investor(s)'], row['Other Investors']),
        axis=1
    )

    return df

def extract_data_with_ai(url):
    """
    Extract funding data from a news article URL using AI.

    Args:
        url (str): URL of the news article

    Returns:
        dict: Extracted funding data or error message
    """
    try:
        # Step A: Fetch and parse the article text
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main article body (this might need tuning for different sites)
        article_text = ' '.join(p.get_text() for p in soup.find_all('p'))

        if not article_text:
            return {"error": "Could not extract text from the article."}

        # Step B: Call the OpenAI API
        system_prompt = """
        You are an expert financial analyst. Extract the following information from the article text provided.
        Respond ONLY with a valid JSON object. If information is not found, use null.
        The schema is: {"companyName": "string", "amount": integer, "currency": "string", "fundingStage": "string", "leadInvestors": ["string"], "otherInvestors": ["string"], "climateVertical": "string"}
        """

        # Check if OpenAI API key is available
        if "OPENAI_API_KEY" not in st.secrets:
            return {"error": "OpenAI API key not configured. Please add OPENAI_API_KEY to Streamlit secrets."}

        openai.api_key = st.secrets["OPENAI_API_KEY"]

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": article_text[:4000]}  # Truncate to fit model context limit
            ]
        )

        # Step C: Return the structured data
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

def format_currency(amount):
    """
    Format currency amounts to be human-readable.

    Args:
        amount (float): Amount to format

    Returns:
        str: Formatted currency string
    """
    # Handle NaN, None, and infinite values
    if pd.isna(amount) or amount is None:
        return "$0"
    if math.isinf(amount):
        return "N/A"

    # Convert to float and handle any remaining edge cases
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "$0"

    # Handle negative values
    if amount < 0:
        return f"-{format_currency(abs(amount))}"

    # Format based on magnitude
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    return f"${amount:.0f}"

def display_investor_profile(df, investor_name):
    """
    Display detailed profile page for a specific investor.

    Args:
        df (pd.DataFrame): Original deals DataFrame
        investor_name (str): Name of the investor
    """
    # Header with investor name
    st.header(f"👤 {investor_name}")

    # Back to list button
    if st.button("← Back to Investor List"):
        st.session_state.selected_investor = None
        st.rerun()

    # Get investor's deals
    investor_deals_df = get_investor_deals(df, investor_name)

    if investor_deals_df.empty:
        st.warning("No deals found for this investor.")
        return

    # Calculate investor-specific KPIs
    total_deals = len(investor_deals_df)
    total_invested = investor_deals_df['Amount'].sum()

    # Get preferred verticals and stages
    verticals = investor_deals_df['Climate Vertical'].value_counts()
    stages = investor_deals_df['Funding Stage'].value_counts()

    # Display KPIs using st.metric for a professional dashboard feel
    col1, col2 = st.columns(2)
    col1.metric(label="Deals Done", value=total_deals)
    col2.metric(label="Total Capital Deployed (in their deals)", value=format_currency(total_invested))

    # Display preferred verticals and stages
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Preferred Climate Verticals")
        if not verticals.empty:
            for vertical, count in verticals.head(5).items():
                st.write(f"• **{vertical}**: {count} deals")
        else:
            st.write("No data available")

    with col2:
        st.subheader("Preferred Funding Stages")
        if not stages.empty:
            for stage, count in stages.head(5).items():
                st.write(f"• **{stage}**: {count} deals")
        else:
            st.write("No data available")

    # Display all deals table
    st.subheader("All Deals")
    st.write(f"📊 **{total_deals} deals found**")

    # Prepare deals table for display
    deals_display = investor_deals_df[[
        'Company Name', 'Funding Date', 'Amount', 'Currency',
        'Funding Stage', 'Climate Vertical', 'Role', 'Source URL'
    ]].copy()

    # Format the Amount column using our helper function
    deals_display['Amount'] = deals_display['Amount'].apply(format_currency)

    # Display the deals table
    st.dataframe(
        deals_display,
        use_container_width=True,
        height=400,
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
            "Amount": st.column_config.TextColumn(
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
            "Climate Vertical": st.column_config.TextColumn(
                "Climate Vertical",
                width="large"
            ),
            "Role": st.column_config.TextColumn(
                "Role",
                width="small"
            ),
            "Source URL": st.column_config.LinkColumn(
                "Source URL",
                width="small"
            )
        }
    )

# Main part of the script
if __name__ == "__main__":
    # Initialize session state
    if 'selected_investor' not in st.session_state:
        st.session_state.selected_investor = None

    # Define the path to the data file
    data_file_path = "data.json"

    # Load the data
    df = load_data(data_file_path)

    # Check if data was loaded successfully
    if not df.empty:
        # Add geography column to the data
        df = add_geography_column(df)

        # Add deal size categories
        df['Deal Size Category'] = df['Amount'].apply(categorize_deal_size)

        # Create main tabs
        tab1, tab2 = st.tabs(["Investor Database", "Glossary"])

        with tab1:
            # Check if an investor is selected for profile view
            if st.session_state.selected_investor:
                # Display investor profile
                display_investor_profile(df, st.session_state.selected_investor)
            else:
                # Display main investor database
                # Add main title
                st.title("🏦 Climate Tech Investor Database")

                # Company Search Section
                st.subheader("🔍 Quick Company Search")
                company_search = st.text_input(
                    "Who funded this company?",
                    placeholder="e.g., PikaCharge, Reneo, Nira Energy...",
                    help="Enter a company name to quickly find their investors"
                )

                # Display company search results if search term is provided
                if company_search:
                    # Search for the company in the deals data
                    company_matches = df[df['Company Name'].str.contains(company_search, case=False, na=False)]

                    if not company_matches.empty:
                        st.success(f"Found {len(company_matches)} funding round(s) for companies matching '{company_search}':")

                        for idx, deal in company_matches.iterrows():
                            with st.expander(f"📈 {deal['Company Name']} - {deal['Funding Stage']} ({deal['Funding Date'].strftime('%Y-%m-%d')})"):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write("**💰 Deal Details:**")
                                    st.write(f"• **Amount**: {format_currency(deal['Amount'])} {deal['Currency']}")
                                    st.write(f"• **Stage**: {deal['Funding Stage']}")
                                    st.write(f"• **Date**: {deal['Funding Date'].strftime('%Y-%m-%d')}")
                                    st.write(f"• **Vertical**: {deal['Climate Vertical']}")

                                with col2:
                                    st.write("**🏦 Investors:**")
                                    if pd.notna(deal['Lead Investor(s)']) and deal['Lead Investor(s)'] != "Not specified":
                                        st.write(f"• **Lead Investor(s)**: {deal['Lead Investor(s)']}")
                                    if pd.notna(deal['Other Investors']) and deal['Other Investors'] != "Not specified":
                                        st.write(f"• **Other Investors**: {deal['Other Investors']}")

                                if pd.notna(deal['Source URL']):
                                    st.write(f"🔗 [Source]({deal['Source URL']})")
                    else:
                        st.warning(f"No companies found matching '{company_search}'. Try a different search term or check the spelling.")

                st.divider()  # Visual separator between search and main content

                # Sidebar filters
                st.sidebar.header("🎯 Build Your Investor Target List")

                # Advanced Filters Section
                st.sidebar.subheader("🎯 Advanced Filters")

                # Lead Investors Only checkbox - Critical for fundraising founders
                lead_only = st.sidebar.checkbox(
                    "Lead Investors Only",
                    value=False,
                    help="Show only investors who have led deals - a critical signal of conviction"
                )

                # Geography filter
                geographies = ["All"] + df['Geography'].unique().tolist()
                selected_geography = st.sidebar.selectbox(
                    "Geography",
                    options=geographies,
                    index=0,
                    help="Filter investors by geographic focus"
                )

                # Deal Size Buckets - Relevant to funding stages
                st.sidebar.subheader("💰 Deal Size Focus")
                deal_size_categories = ["All"] + df['Deal Size Category'].unique().tolist()
                selected_deal_size = st.sidebar.selectbox(
                    "Deal Size Category",
                    options=deal_size_categories,
                    index=0,
                    help="Filter by deal size buckets relevant to funding stages"
                )

                # Basic Filters Section
                st.sidebar.subheader("📊 Basic Filters")

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

                # Check if any filters have been applied (for contextual welcome message)
                filters_applied = (
                    lead_only or  # Lead investors only is checked
                    selected_geography != "All" or  # Geography filter is not "All"
                    selected_deal_size != "All" or  # Deal size filter is not "All"
                    len(selected_verticals) != len(climate_verticals) or  # Not all verticals selected
                    selected_stage != "All" or  # Funding stage filter is not "All"
                    investor_search.strip() != "" or  # Investor name search has text
                    company_search.strip() != ""  # Company search has text
                )

                # Display contextual welcome message for new users
                if not filters_applied:
                    st.info(
                        "👋 **Welcome, Founder!** Start by using the filters on the left to build your ideal investor profile. "
                        "Try filtering by geography, deal size, or climate vertical to find investors that match your startup's needs.",
                        icon="💡"
                    )

                # Filter the deals DataFrame first to get relevant investors
                filtered_deals_df = df.copy()

                # Apply Geography filter to deals
                if selected_geography != "All":
                    filtered_deals_df = filtered_deals_df[filtered_deals_df['Geography'] == selected_geography]

                # Apply Deal Size Category filter to deals
                if selected_deal_size != "All":
                    filtered_deals_df = filtered_deals_df[filtered_deals_df['Deal Size Category'] == selected_deal_size]

                # Apply Climate Vertical filter to deals
                if selected_verticals:
                    filtered_deals_df = filtered_deals_df[filtered_deals_df['Climate Vertical'].isin(selected_verticals)]

                # Apply Funding Stage filter to deals
                if selected_stage != "All":
                    filtered_deals_df = filtered_deals_df[filtered_deals_df['Funding Stage'] == selected_stage]

                # Create filtered investor summary based on filtered deals and lead_only setting
                if len(filtered_deals_df) > 0:
                    filtered_investor_summary = create_investor_summary(filtered_deals_df, lead_only=lead_only)
                else:
                    columns = ['Investor Name', 'Deals Done', 'Lead Deals', 'Total Invested', 'Preferred Verticals', 'Preferred Stages']
                    filtered_investor_summary = pd.DataFrame(columns=columns)

                # Apply Investor Name filter to investor summary
                if investor_search:
                    investor_mask = filtered_investor_summary['Investor Name'].str.contains(investor_search, case=False, na=False)
                    filtered_investor_summary = filtered_investor_summary[investor_mask]

                # KPI Dashboard Section
                st.subheader("📊 Investor Overview")

                # Create 3 columns for KPI metrics
                col1, col2, col3 = st.columns(3)

                # Calculate KPIs from filtered investor data
                total_investors = len(filtered_investor_summary)
                # Safely calculate total funding, handling any infinite or NaN values
                total_funding_tracked = filtered_investor_summary['Total Invested'].replace([float('inf'), -float('inf')], 0).fillna(0).sum()
                avg_investment_per_investor = total_funding_tracked / total_investors if total_investors > 0 else 0

                # Display KPI metrics
                with col1:
                    st.metric(
                        label="Active Investors",
                        value=f"{total_investors:,}"
                    )

                with col2:
                    st.metric(
                        label="Total Capital Tracked",
                        value=format_currency(total_funding_tracked)
                    )

                with col3:
                    st.metric(
                        label="Avg. Investment/Investor",
                        value=format_currency(avg_investment_per_investor)
                    )

                # Top Investors Chart
                st.subheader("Top Investors by Capital")

                if not filtered_investor_summary.empty:
                    # Get top 10 investors by total invested
                    top_investors_data = filtered_investor_summary.head(10)
                    
                    # Create a DataFrame for the chart with formatted labels
                    chart_data = top_investors_data.set_index('Investor Name')['Total Invested']
                    
                    # Display the chart
                    st.bar_chart(chart_data)
                    
                    # Add a formatted summary below the chart
                    st.write("**Top 5 Investors:**")
                    for idx, (investor, amount) in enumerate(chart_data.head(5).items(), 1):
                        st.write(f"{idx}. **{investor}**: {format_currency(amount)}")
                else:
                    st.info("No investors found for the selected filters.")

                # Add subheader for the investor table
                st.subheader("Climate Tech Investors")

                # Display filtered investor info
                st.write(f"📊 **Showing {len(filtered_investor_summary)} investors**")

                # Alphabetical navigation bar
                st.subheader("🔤 Browse by Name")

                # Define the alphabet cluster groups
                alphabet_clusters = ["All", "A-C", "D-F", "G-I", "J-L", "M-O", "P-R", "S-U", "V-Z", "#"]

                # Initialize the selected cluster in session_state if it doesn't exist
                if 'selected_cluster' not in st.session_state:
                    st.session_state.selected_cluster = "All"

                # Create a horizontal layout for the navigation buttons using st.columns
                cols = st.columns(len(alphabet_clusters))
                for i, cluster in enumerate(alphabet_clusters):
                    # Highlight the selected cluster with a different style
                    if cluster == st.session_state.selected_cluster:
                        if cols[i].button(f"**{cluster}**", key=f"btn_{cluster}", help=f"Currently showing: {cluster}"):
                            st.session_state.selected_cluster = cluster
                    else:
                        if cols[i].button(cluster, key=f"btn_{cluster}"):
                            st.session_state.selected_cluster = cluster

                # Filter the investor_summary DataFrame based on the selected cluster
                selected = st.session_state.selected_cluster
                if selected != "All":
                    if selected == "#":
                        # Logic for investors not starting with a letter
                        filtered_investors = filtered_investor_summary[~filtered_investor_summary['Investor Name'].str[0].str.isalpha()]
                    else:
                        # Logic for letter-based clusters
                        start_char, end_char = selected.split('-')
                        filtered_investors = filtered_investor_summary[
                            filtered_investor_summary['Investor Name'].str.upper().str[0].between(start_char, end_char)
                        ]
                else:
                    # If "All" is selected, use the full (sidebar-filtered) DataFrame
                    filtered_investors = filtered_investor_summary

                # Update the display count to reflect alphabetical filtering
                st.write(f"📊 **Showing {len(filtered_investors)} investors** (filtered by: {selected})")

                # Add view toggle for different display formats
                view_option = st.radio(
                    "Choose your view:",
                    ["📋 Card View", "📊 Table View"],
                    horizontal=True,
                    help="Card view is better for scanning, table view is better for detailed comparison"
                )

                # Create investor display based on selected view
                if not filtered_investors.empty:
                    if view_option == "📋 Card View":
                        st.write("💡 **Tip**: Scan the cards below to quickly identify investors that match your criteria:")

                        # Create rich investor cards
                        for idx, row in filtered_investors.iterrows():
                            investor_name = row['Investor Name']
                            deals_done = row['Deals Done']
                            lead_deals = row['Lead Deals']
                            total_invested = row['Total Invested']
                            preferred_verticals = row['Preferred Verticals'].split(', ') if row['Preferred Verticals'] else []
                            preferred_stages = row['Preferred Stages'].split(', ') if row['Preferred Stages'] else []

                            # Create horizontal rule to separate cards
                            st.markdown("---")

                            # Create card layout with columns
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                # Investor name as subheader
                                st.subheader(f"🏦 {investor_name}")

                                # Create visual tags for preferred verticals
                                if preferred_verticals and preferred_verticals[0]:
                                    st.markdown("**🎯 Top Climate Verticals:**")
                                    vertical_tags = " ".join([f"`{vertical.strip()}`" for vertical in preferred_verticals[:3] if vertical.strip()])
                                    st.markdown(vertical_tags)

                                # Create visual tags for preferred stages
                                if preferred_stages and preferred_stages[0]:
                                    st.markdown("**📈 Preferred Funding Stages:**")
                                    stage_tags = " ".join([f"`{stage.strip()}`" for stage in preferred_stages[:3] if stage.strip()])
                                    st.markdown(stage_tags)

                            with col2:
                                # Key metrics in the right column
                                st.metric("Total Deals", deals_done)
                                st.metric("Lead Deals", lead_deals, help="Deals where they were the lead investor")
                                st.metric("Capital Deployed", format_currency(total_invested))

                                # View profile button
                                if st.button("👁️ View Profile", key=f"card_btn_{idx}", help="See detailed investor profile"):
                                    st.session_state.selected_investor = investor_name
                                    st.rerun()

                    else:  # Table View
                        st.write("Click on an investor name to view their detailed profile:")

                        # Create buttons for each investor (original format)
                        for idx, row in filtered_investors.iterrows():
                            investor_name = row['Investor Name']
                            deals_done = row['Deals Done']
                            lead_deals = row['Lead Deals']
                            total_invested = row['Total Invested']

                            # Format the button label with key info including lead deals
                            button_label = f"👤 {investor_name} | {deals_done} deals ({lead_deals} lead) | {format_currency(total_invested)}"

                            if st.button(button_label, key=f"investor_{idx}"):
                                st.session_state.selected_investor = investor_name
                                st.rerun()

                # Display interactive table only in Table View
                if view_option == "📊 Table View":
                    st.subheader("Interactive Investor Table")

                    # Configure pandas display options for better visibility
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', None)
                    pd.set_option('display.max_colwidth', 100)

                    # Use the alphabetically filtered investor DataFrame
                    display_df = filtered_investors.copy()

                    # Format the Total Invested column using our helper function
                    if not display_df.empty:
                        display_df['Total Invested'] = display_df['Total Invested'].apply(format_currency)

                        # Add a 'Select' column with checkboxes for building target list
                        display_df.insert(0, 'Select', False)

                    # Display the investor summary DataFrame with interactive checkboxes
                    st.write("💡 **Tip**: Check the boxes next to investors you want to target, then export your list!")

                    edited_df = st.data_editor(
                        display_df,
                        use_container_width=True,  # Use full container width
                        height=400,  # Reduced height since we have buttons above
                        column_config={
                            "Select": st.column_config.CheckboxColumn(
                                "Select",
                                help="Check to add this investor to your target list",
                                width="small"
                            ),
                            "Investor Name": st.column_config.TextColumn(
                                "Investor Name",
                                width="large"
                            ),
                            "Deals Done": st.column_config.NumberColumn(
                                "Deals Done",
                                width="small"
                            ),
                            "Lead Deals": st.column_config.NumberColumn(
                                "Lead Deals",
                                width="small",
                                help="Number of deals where this investor was the lead - key conviction signal"
                            ),
                            "Total Invested": st.column_config.TextColumn(
                                "Total Invested",
                                width="medium"
                            ),
                            "Preferred Verticals": st.column_config.TextColumn(
                                "Preferred Verticals",
                                width="large"
                            ),
                            "Preferred Stages": st.column_config.TextColumn(
                                "Preferred Stages",
                                width="medium"
                            )
                        },
                        disabled=["Investor Name", "Deals Done", "Lead Deals", "Total Invested", "Preferred Verticals", "Preferred Stages"],
                        hide_index=True
                    )

                    # Check which investors were selected and provide export functionality
                    if not edited_df.empty:
                        selected_investors = edited_df[edited_df['Select'] == True]

                        if len(selected_investors) > 0:
                            st.success(f"🎯 **{len(selected_investors)} investors selected for your target list!**")

                            # Prepare the export data (remove the Select column for cleaner export)
                            export_df = selected_investors.drop('Select', axis=1)

                            # Convert DataFrame to CSV
                            csv_data = export_df.to_csv(index=False)

                            # Create download button
                            st.download_button(
                                label="📥 Export Selected Investors to CSV",
                                data=csv_data,
                                file_name=f"target_investors_{len(selected_investors)}_selected.csv",
                                mime="text/csv",
                                help="Download your selected investors as a CSV file for outreach planning"
                            )

                            # Show a preview of selected investors
                            with st.expander(f"Preview of {len(selected_investors)} Selected Investors"):
                                st.dataframe(export_df, use_container_width=True)
                        else:
                            st.info("💡 Select investors using the checkboxes above to build your target list and export to CSV.")
                    else:
                        st.info("No investors found for the selected filters.")

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

    # AI Assistant Feature
    st.markdown("---")
    with st.expander("🤖 AI Assistant: Extract New Funding Deal"):
        st.info("Paste the URL of a funding announcement article below to see the AI in action.", icon="💡")
        url_input = st.text_input("Article URL")

        if st.button("Extract Funding Data"):
            if url_input:
                with st.spinner("Reading article and calling AI... this may take a moment."):
                    extracted_data = extract_data_with_ai(url_input)
                    st.subheader("Extracted Data:")
                    st.json(extracted_data)
                    st.success("Extraction complete! This data can be added to the main database in a future version.")
            else:
                st.warning("Please enter a URL.")

    # Add data freshness caption to build trust
    if not df.empty:
        last_updated_date = df['Funding Date'].max().strftime("%B %d, %Y")
        st.caption(f"Data sourced from public announcements. Last updated: {last_updated_date}")








