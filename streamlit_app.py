
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import base64
import os


# Page configuration
st.set_page_config(layout="wide", page_title="Billing Reconciliation Dashboard")

def get_base64_image(image_path):
    """
    Convert an image to a base64-encoded string.
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        st.error(f"Logo file not found at: {image_path}")
        return None

def display_page_logo():
    logo_url = "https://raw.githubusercontent.com/YuleAsh/blank-app-1/main/Du.png"
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="{logo_url}" alt="Logo" width="300" />
        </div>
        """,
        unsafe_allow_html=True,
    )

# Call the logo display function at the very top
display_page_logo()



# Set display format for pandas globally
pd.options.display.float_format = "{:.2f}".format


# Sample data generation (50 records) with both disputed and undisputed data
def generate_sample_data():
    np.random.seed(42)
    months = pd.date_range(start="2024-01-01", periods=12, freq='M').strftime('%Y-%m').tolist()
    carriers = [f'Carrier {i}' for i in range(1, 11)]  # 10 unique carriers
    data = []

    for month in months:
        for carrier in carriers:
            invoice_amount = np.round(np.random.uniform(1000, 5000),2)
            is_disputed = np.random.rand() < 0.2
            disputed_amount = np.round(np.random.uniform(0, invoice_amount * 0.3) if is_disputed else 0,2)
            billing_cycle = f'{2024}-{int(month[-2:]):02d}-{np.random.choice([1, 2])}'  # Format: Year-Month-Fortnight

            data.append({
                'Carrier Name': carrier,
                'Invoice Amount (USD)': invoice_amount,
                'Disputed Amount (USD)': disputed_amount,
                'Reconciliation Status': np.random.choice(['Pending', 'Completed', 'In Progress']),
                'Dispute Type': np.random.choice(['Rate Dispute', 'Volume Dispute']) if is_disputed else None,
                'Settlement Status': np.random.choice(['Settled', 'Unsettled']) if is_disputed else 'Settled',
                'Invoice Month': month,
                'Billing Cycle': billing_cycle,
                'Usage (Mins)': np.random.uniform(100, 500)  # Ensure 'Usage (Mins)' is included
            })

    return pd.DataFrame(data)

df = generate_sample_data()
df=df.round(2)


# Dashboard title
st.title("Billing Reconciliation Dashboard")

# Filters
carrier_filter = st.selectbox("Select Carrier (Optional)", options=["All"] + list(df['Carrier Name'].unique()))
month_filter = st.selectbox("Select Month (Optional)", options=["All"] + list(df['Invoice Month'].unique()))

# Applying filters (if selected) to data
filtered_df = df.copy()
filtered_df = filtered_df.round(2)
if carrier_filter != "All":
    filtered_df = filtered_df[filtered_df['Carrier Name'] == carrier_filter]
if month_filter != "All":
    filtered_df = filtered_df[filtered_df['Invoice Month'] == month_filter]

# Function to create summary tables with specific fields and alignment
def create_summary_table(data, columns):
    table = data[columns].copy()
    for col in ['Invoice Amount (USD)', 'Disputed Amount (USD)', 'Usage (Mins)']:
        if col in table.columns:
            table[col] = table[col].map("{:.2f}".format)
    return table

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Invoice Reconciliation", "Reconciliation Summary", "Dispute Summary", "Settlement Summary"])


# Tab 1: Invoice Recon
with tab1:
    st.subheader("Invoice Reconciliation Overview")
    st.write("### Summary Table")
    table1_data = create_summary_table(filtered_df, [
        'Carrier Name', 'Reconciliation Status', 'Invoice Amount (USD)', 
        'Disputed Amount (USD)', 'Dispute Type', 'Settlement Status'
    ])
    st.dataframe(table1_data, use_container_width=True, height=250)

    # Chart: Disputed vs Processed Amounts by Carrier
    st.write("### Disputed vs Processed Amounts by Carrier")
    if not filtered_df.empty:
        processed_vs_disputed = px.bar(filtered_df, x='Carrier Name', y=['Invoice Amount (USD)', 'Disputed Amount (USD)'],
                                       title="Disputed vs Processed Amounts by Carrier", barmode="group",  labels={
        "Carrier Name": "Carrier", "value": "Amount (USD)"})
        st.plotly_chart(processed_vs_disputed)

    # Chart: Invoice Disputes by Month
    st.write("### Invoice Disputes by Month")
    monthly_disputes = filtered_df.round(2).groupby('Invoice Month').agg({
        'Invoice Amount (USD)': 'sum', 'Disputed Amount (USD)': 'sum'}).reset_index()
    monthly_disputes = np.round(monthly_disputes, 2)
    monthly_disputes_fig = px.line(monthly_disputes.round(2), x='Invoice Month', y=['Invoice Amount (USD)', 'Disputed Amount (USD)'],
                                   title="Invoice Disputes by Month",  labels={"value": "Amount (USD)"} )
    st.plotly_chart(monthly_disputes_fig)

# Tab 2: Reconciliation Summary
with tab2:
    st.subheader("Reconciliation Summary")
    st.write("### Summary Table")

    # Calculate Receivables and Payables
    filtered_df['Receivables'] = np.round(filtered_df['Invoice Amount (USD)'] - filtered_df['Disputed Amount (USD)'], 2)
    filtered_df['Payables'] = np.round(filtered_df['Disputed Amount (USD)'], 2)

    # Group by 'Carrier Name' and 'Billing Cycle'
    summary_table2 = filtered_df.groupby(['Carrier Name', 'Billing Cycle']).agg({
        'Invoice Amount (USD)': 'sum',
        'Disputed Amount (USD)': 'sum',
    }).reset_index()

    # Add additional columns like Receivables, Payables, Netted Amount, and Settlement Status
    summary_table2['Receivables'] = np.round(np.random.uniform(1000, 3000, len(summary_table2)), 2)
    summary_table2['Payables'] = np.round(np.random.uniform(500, 2500, len(summary_table2)), 2)
    summary_table2['Netted Amount'] = np.round(summary_table2['Receivables'] - summary_table2['Payables'], 2)
    summary_table2['Settlement Status'] = np.random.choice(['Settled', 'Pending'], len(summary_table2))

    # Round numerical values for clarity
    summary_table2_rounded = summary_table2.round(2)

    summary_table2_display = summary_table2_rounded.astype(str)

    # Apply conditional formatting for 'Settlement Status'
    def highlight_settlement_status1(val):
        """Highlight 'Pending' in red and 'Settled' in green."""
        if val == 'Pending':
            return 'color: red;' 
        elif val == 'Settled':
            return 'color: green;'
        return ''

    # Use Styler for applying formatting
    styled_table = summary_table2_display.style.applymap(highlight_settlement_status1, subset=['Settlement Status']).set_properties(**{'text-align': 'left'})
  
    # Display table using st.dataframe with scrollable height
    st.dataframe(
        styled_table,
        use_container_width=True,
        height=400  # Set fixed height for scrollable table
    )

    # Chart: Pending Reconciliation by Carrier
    st.write("### Carriers with Pending Reconciliation")
    pending_reconciliation = filtered_df[filtered_df['Reconciliation Status'] == 'Pending']
    pending_summary = pending_reconciliation.groupby('Carrier Name')['Invoice Amount (USD)'].sum().reset_index()
    pending_reconciliation_fig = px.bar(
        pending_summary, 
        x='Carrier Name', 
        y='Invoice Amount (USD)',
        title="Invoices with Pending Reconciliation by Carrier"
    )
    st.plotly_chart(pending_reconciliation_fig)


# Tab 3: Dispute Summary
with tab3:
    st.subheader("Dispute Summary")
    st.write("### Summary Table")
    
    # Simulate realistic values for 'Disputed Usage (Mins)'
    # Disputed Usage is based on the type of dispute (Rate or Volume)
    filtered_df['Disputed Usage (Mins)'] = np.random.uniform(0, 500, size=len(filtered_df)).round(2)
    filtered_df.loc[filtered_df['Dispute Type'] == 'Rate Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(0, 5000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Rate Dispute'])).round(2)
    filtered_df.loc[filtered_df['Dispute Type'] == 'Volume Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(100, 2000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Volume Dispute'])).round(2)

    # Simulate realistic 'Disputed Amount' linked to usage
    filtered_df['Disputed Amount (USD)'] = (filtered_df['Disputed Usage (Mins)'] * np.random.uniform(0.05, 0.2, size=len(filtered_df))).round(2)

    # Group by 'Carrier Name' and calculate aggregated metrics
    summary_table3 = filtered_df.groupby('Carrier Name').agg({
        'Invoice Amount (USD)': 'sum',  # Sum of all invoices for each carrier
        'Disputed Amount (USD)': 'sum',  # Sum of all disputed amounts
        'Disputed Usage (Mins)': 'sum',  # Total disputed usage minutes
        'Dispute Type': lambda x: np.random.choice(x.dropna().unique()) if not x.dropna().empty else None,  # Combine unique dispute types
        'Settlement Status': lambda x: np.random.choice(x.dropna().unique()) if not x.dropna().empty else None  # Combine settlement statuses
    }).reset_index()

    # Round numerical values in the summary table
    summary_table3[['Invoice Amount (USD)', 'Disputed Amount (USD)', 'Disputed Usage (Mins)']] = summary_table3[
        ['Invoice Amount (USD)', 'Disputed Amount (USD)', 'Disputed Usage (Mins)']
    ].round(2)

    # Rename columns for clarity
    summary_table3.rename(columns={
        'Invoice Amount (USD)': 'Total Invoice Amount (USD)',
        'Disputed Amount (USD)': 'Total Disputed Amount (USD)',
        'Disputed Usage (Mins)': 'Total Disputed Usage (Mins)'
    }, inplace=True)

    # Display the summary table
    summary_table3_rounded = summary_table3.round(2)

    # Convert the DataFrame to strings to ensure the display keeps formatting
    summary_table3_display = summary_table3_rounded.astype(str)

    # Apply conditional formatting for 'Settlement Status'
    def highlight_settlement_status(val):
        """Highlight 'Unsettled' in red."""
        if val == 'Unsettled':
            return 'color: red;'
        else: return 'color: green;'
        return ''

    # Use Styler for applying formatting
    styled_table = summary_table3_display.style.applymap(highlight_settlement_status, subset=['Settlement Status']).set_properties(**{'text-align': 'left'})
    
    # Render the table as HTML and display using st.write
    st.write(styled_table.to_html(), unsafe_allow_html=True)

    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    # Chart 1: Disputed Amounts by Carrier
    with col1:
        disputed_amounts = filtered_df.groupby('Carrier Name')['Disputed Amount (USD)'].sum().reset_index()
        disputed_amounts['Disputed Amount (USD)'] = disputed_amounts['Disputed Amount (USD)'].round(2)
        disputed_amounts_fig = px.bar(
            disputed_amounts, x='Carrier Name', y='Disputed Amount (USD)', 
            title="Disputed Amounts by Carrier"
        )
        st.plotly_chart(disputed_amounts_fig, use_container_width=True)

    # Chart 2: Disputed Usage by Carrier
    with col2:
        disputed_usage = filtered_df.groupby('Carrier Name')['Disputed Usage (Mins)'].sum().reset_index()
        disputed_usage['Disputed Usage (Mins)'] = disputed_usage['Disputed Usage (Mins)'].round(2)
        disputed_usage_fig = px.bar(
            disputed_usage, x='Carrier Name', y='Disputed Usage (Mins)', 
            title="Disputed Usage (Mins) by Carrier"
        )
        st.plotly_chart(disputed_usage_fig, use_container_width=True)


# Tab 4: Settlement Summary
with tab4:
    st.subheader("Settlement Summary")
    st.write("### Summary Table")

    # Group by 'Carrier Name' and aggregate the required fields
    summary_table4 = filtered_df.groupby('Carrier Name').agg({
        'Disputed Amount (USD)': 'sum',  # Summing disputed amounts per carrier
        'Settlement Status': 'count',  # Counting the invoices (total invoices per carrier)
    }).reset_index()

    # Rename 'Settlement Status' to 'Total Invoices' for clarity
    summary_table4.rename(columns={'Settlement Status': 'Total Invoices'}, inplace=True)

    # Define meaningful values based on telecom billing scenarios
    summary_table4['Settled Invoices'] = summary_table4.apply(lambda row: row['Total Invoices'] - np.random.randint(1, 3), axis=1)  # Randomly settled invoices
    summary_table4['Pending Settlements'] = summary_table4['Total Invoices'] - summary_table4['Settled Invoices']  # Pending invoices

    # Total Settled Amount: Assuming 80% of the disputed amount is settled in most cases
    summary_table4['Total Settled Amount'] = np.round(summary_table4['Disputed Amount (USD)'] * 0.8, 2)  # Settled amount (80% of disputed amount)

    # Outstanding Amount: Remaining amount (could be 20% of disputed amounts)
    summary_table4['Outstanding Amount'] = np.round(summary_table4['Disputed Amount (USD)'] * 0.2, 2)  # Outstanding amount (20% of disputed amount)

    # Settlement Completion Rate: Ratio of settled invoices to total invoices
    summary_table4['Settlement Completion Rate'] = np.round((summary_table4['Settled Invoices'] / summary_table4['Total Invoices']) * 100, 2)

    # Settlement Adjustment: Simulating adjustments (could be based on dispute type, rates, etc.)
    summary_table4['Settlement Adjustment'] = np.round(np.random.uniform(0, 500, len(summary_table4)), 2)  # Adjustments as random values

    # Display the summary table with the practical fields
    summary_table4_rounded = summary_table4.round(2)
    summary_table4_display = summary_table4_rounded.astype(str)
    st.dataframe(summary_table4_display.style.set_properties(**{'text-align': 'center'}), use_container_width=True, height=300)

    # Create columns for the two charts
    st.write("### Settlement Visualizations")
    col1, col2 = st.columns(2)

    # Chart 1: Settlement Status by Carrier (Pie Chart)
    with col1:
        st.write("Settlement Status by Carrier")
        settlement_status = filtered_df.groupby(['Carrier Name', 'Settlement Status']).size().reset_index(name='Count')
        settlement_pie = px.pie(settlement_status, names='Settlement Status', values='Count', title="Settlement Status by Carrier")
        st.plotly_chart(settlement_pie, use_container_width=True)

    # Chart 2: Outstanding Amount by Carrier (Bar Chart)
    with col2:
        st.write("Outstanding Amount by Carrier")
        outstanding_bar = px.bar(
            summary_table4,
            x='Carrier Name',
            y='Outstanding Amount',
            title="Outstanding Amount by Carrier",
            text='Outstanding Amount',
            labels={'Outstanding Amount': 'Amount (USD)'},
            color='Outstanding Amount',
            color_continuous_scale='Reds'
        )
        outstanding_bar.update_layout(
            xaxis_title="Carrier Name",
            yaxis_title="Outstanding Amount (USD)",
            template="plotly_white"
        )
        st.plotly_chart(outstanding_bar, use_container_width=True)


