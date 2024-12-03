
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
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
    invoice_counter = 1  # To create sequential invoice numbers

    for month in months:
        for carrier in carriers:
            invoice_amount = np.round(np.random.uniform(1000, 5000), 2)
            is_disputed = np.random.rand() < 0.2
            disputed_amount = np.round(np.random.uniform(0, invoice_amount * 0.3) if is_disputed else 0, 2)
            billing_cycle = f'{2024}-{int(month[-2:]):02d}-{np.random.choice([1, 2])}'  # Format: Year-Month-Fortnight

            # Generate a unique invoice number
            invoice_number = f'{carrier.replace(" ", "")[:3].upper()}-{month.replace("-", "")}-{invoice_counter:04d}'
            invoice_counter += 1

            data.append({
                'Invoice Number': invoice_number,
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


# Tab 1: Invoice Reconciliation
with tab1:
    st.subheader("Invoice Reconciliation Overview")

    # Add Compact Counter for Settled vs Unsettled Invoices
    if not filtered_df.empty:
        settled_count = filtered_df[filtered_df['Settlement Status'] == 'Settled'].shape[0]
        unsettled_count = filtered_df[filtered_df['Settlement Status'] == 'Unsettled'].shape[0]

   # Display the counts with a consistent, centered design
    st.markdown("### Settlement Summary")
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; gap: 20px;">
            <div style="text-align: center; padding: 15px; width: 260px; 
                        border: 2px solid #007BFF; border-radius: 12px; 
                        background: linear-gradient(135deg, #85C1E9, #EAF2F8); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
                <h5 style="color: #FF4D4D; margin: 0; font-size: 1.2em;">✅ Settled</h5>
                <p style="margin: 10px 0; color: #1E4DD8; font-size: 1.5em; font-weight: bold;">
                    {settled_count} Invoices
                </p>
            </div>
            <div style="text-align: center; padding: 15px; width: 260px; 
                        border: 2px solid #FF5733; border-radius: 12px; 
                        background: linear-gradient(135deg, #F5B7B1, #FDEDEC); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
                <h5 style="color: #FF4D4D; margin: 0; font-size: 1.2em;">❌ Unsettled</h5>
                <p style="margin: 10px 0; color: #1E4DD8; font-size: 1.5em; font-weight: bold;">
                    {unsettled_count} Invoices
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # Chart: Disputed vs Processed Amounts by Carrier
    if not filtered_df.empty:
        processed_vs_disputed = px.bar(
            filtered_df, x='Carrier Name', y=['Invoice Amount (USD)', 'Disputed Amount (USD)'],
            title="Disputed vs Processed Amounts by Carrier", barmode="group", labels={
                "Carrier Name": "Carrier", "value": "Amount (USD)"}
        )

        processed_vs_disputed.update_layout(
            title={
                'text': "Disputed vs Processed Amounts by Carrier",
                'font': {'size': 24},
                'x': 0.35
            }
        )
        st.plotly_chart(processed_vs_disputed)

    # Chart: Invoice Disputes by Month
    monthly_disputes = filtered_df.round(2).groupby('Invoice Month').agg({
        'Invoice Amount (USD)': 'sum', 'Disputed Amount (USD)': 'sum'}).reset_index()
    monthly_disputes = np.round(monthly_disputes, 2)
    monthly_disputes_fig = px.line(
        monthly_disputes.round(2), x='Invoice Month', y=['Invoice Amount (USD)', 'Disputed Amount (USD)'],
        title="Invoice Disputes by Month", labels={"value": "Amount (USD)"}
    )

    monthly_disputes_fig.update_layout(
        title={ 
            'text': "Invoice Disputes by Month",
                'font': {'size': 24},
                'x': 0.35
            }
        )
    st.plotly_chart(monthly_disputes_fig)

    # Table: Summary Table
    table1_data = create_summary_table(filtered_df, [
        'Invoice Number', 'Carrier Name', 'Reconciliation Status', 'Invoice Amount (USD)', 
        'Disputed Amount (USD)', 'Dispute Type', 'Settlement Status'
    ])

    def highlight_settlement_status1(val):
        """Highlight 'Pending' in red and 'Settled' in green."""
        if val == 'Unsettled':
            return 'color: red; font-weight: bold;'
        elif val == 'Settled':
            return 'color: green; font-weight: bold;'
        return ''

    styled_table = table1_data.style.applymap(
        highlight_settlement_status1, subset=['Settlement Status']
    ).set_properties(**{'text-align': 'left'})
    st.dataframe(styled_table, use_container_width=True, height=250)




# Tab 2: Reconciliation Summary
with tab2:
    st.subheader("Reconciliation Summary")
    
    # Counter: Current Billing Cycle
    current_cycle_data = filtered_df[filtered_df['Billing Cycle'] == filtered_df['Billing Cycle'].max()]
    current_cycle_data['Receivables'] = np.round(np.random.uniform(2000, 10000, len(current_cycle_data)), 2)
    current_cycle_count = len(current_cycle_data[current_cycle_data['Reconciliation Status'] == 'Pending'])
    current_cycle_amount = current_cycle_data[current_cycle_data['Reconciliation Status'] == 'Pending']['Receivables'].sum()
    
    # Counter: Quarter to Date (QTD)
    current_quarter = pd.Timestamp.now().quarter
    qtd_data = filtered_df[filtered_df['Billing Cycle'].apply(lambda x: pd.Timestamp(x).quarter) == current_quarter]
    qtd_data['Receivables'] = np.round(np.random.uniform(5000, 15000, len(qtd_data)), 2)
    qtd_cycle_count = len(qtd_data[qtd_data['Reconciliation Status'] == 'Pending'])
    qtd_cycle_amount = qtd_data[qtd_data['Reconciliation Status'] == 'Pending']['Receivables'].sum()

    
# Clickable Counters using st.components.v1.html
    components.html(
        f"""
        <div style="display: flex; justify-content: center; gap: 40px; margin: 20px;">
            <!-- Current Billing Cycle -->
            <a style="text-decoration: none;">
                <div style="text-align: center; padding: 15px; width: 250px; 
                            border: 2px solid #6C63FF; border-radius: 12px; 
                            background: linear-gradient(135deg, #A3ABFF, #ECECFF); 
                            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                    <h5 style="color: #6C63FF; margin: 0; font-size: 1.2em;">🔴 Unreconciled (Current)</h5>
                    <p style="margin: 10px 0; color: #2B55CC; font-size: 1.5em; font-weight: bold;">
                        {current_cycle_count} Invoices
                    </p>
                    <p style="margin: 5px 0; color: #555; font-size: 1.1em;">
                        Receivables: <span style="color: #2B55CC; font-weight: bold;">${current_cycle_amount:,.2f}</span>
                    </p>
                </div>
            </a>

            <!-- Quarter-to-Date -->
            <a style="text-decoration: none;">
                <div style="text-align: center; padding: 15px; width: 250px; 
                            border: 2px solid #FF6B6B; border-radius: 12px; 
                            background: linear-gradient(135deg, #FFA3A3, #FFECEC); 
                            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                    <h5 style="color: #FF6B6B; margin: 0; font-size: 1.2em;">🔴 Unreconciled (QTD)</h5>
                    <p style="margin: 10px 0; color: #CC2B2B; font-size: 1.5em; font-weight: bold;">
                        {qtd_cycle_count} Invoices
                    </p>
                    <p style="margin: 5px 0; color: #555; font-size: 1.1em;">
                        Receivables: <span style="color: #CC2B2B; font-weight: bold;">${qtd_cycle_amount:,.2f}</span>
                    </p>
                </div>
            </a>
        </div>
        """,
        height=150,  # Adjust height as necessary
    )


    # Chart: Pending Reconciliation by Carrier
    pending_reconciliation = filtered_df[filtered_df['Reconciliation Status'] == 'Pending']
    pending_summary = pending_reconciliation.groupby('Carrier Name')['Invoice Amount (USD)'].sum().reset_index()
    pending_reconciliation_fig = px.bar(
        pending_summary, 
        x='Carrier Name', 
        y='Invoice Amount (USD)',
        title="Pending Reconciliation by Carrier"
    )

    pending_reconciliation_fig.update_layout(
        title={
            'text': "Pending Reconciliation by Carrier",
            'font': {'size': 24},
            'x': 0.35
        }
    )
    st.plotly_chart(pending_reconciliation_fig)

    # Table: Reconciliation Summary
    filtered_df['Receivables'] = np.round(filtered_df['Invoice Amount (USD)'] - filtered_df['Disputed Amount (USD)'], 2)
    filtered_df['Payables'] = np.round(filtered_df['Disputed Amount (USD)'], 2)

    summary_table2 = filtered_df.groupby(['Carrier Name', 'Billing Cycle']).agg({
        'Invoice Amount (USD)': 'sum',
        'Disputed Amount (USD)': 'sum',
    }).reset_index()

    summary_table2['Receivables'] = current_cycle_data['Receivables']
    summary_table2['Payables'] = np.round(np.random.uniform(500, 2500, len(summary_table2)), 2)
    summary_table2['Netted Amount'] = np.round(summary_table2['Receivables'] - summary_table2['Payables'], 2)
    summary_table2['Settlement Status'] = np.random.choice(['Settled', 'Pending'], len(summary_table2))

    summary_table2_rounded = summary_table2.round(2)
    summary_table2_display = summary_table2_rounded.astype(str)

    def highlight_settlement_status1(val):
        if val == 'Pending':
            return 'color: red; font-weight: bold;'
        elif val == 'Settled':
            return 'color: green; font-weight: bold;'
        return ''

    styled_table = summary_table2_display.style.applymap(highlight_settlement_status1, subset=['Settlement Status']).set_properties(**{'text-align': 'left'})
    st.dataframe(styled_table, use_container_width=True, height=250)


# Tab 3: Dispute Summary
with tab3:
    st.subheader("Dispute Summary")

    # Ensure 'Disputed Usage (Mins)' is added to the filtered dataframe
    if 'Disputed Usage (Mins)' not in filtered_df.columns:
        filtered_df['Disputed Usage (Mins)'] = np.random.uniform(0, 500, size=len(filtered_df)).round(2)
        filtered_df.loc[filtered_df['Dispute Type'] == 'Rate Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(0, 5000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Rate Dispute'])).round(2)
        filtered_df.loc[filtered_df['Dispute Type'] == 'Volume Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(100, 2000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Volume Dispute'])).round(2)

    if 'Disputed Amount (USD)' not in filtered_df.columns:
        filtered_df['Disputed Amount (USD)'] = (filtered_df['Disputed Usage (Mins)'] * np.random.uniform(0.05, 0.2, size=len(filtered_df))).round(2)

    # Dispute Count
    rate_disputes = len(filtered_df[filtered_df['Dispute Type'] == 'Rate Dispute'])
    volume_disputes = len(filtered_df[filtered_df['Dispute Type'] == 'Volume Dispute'])

   # Counters
    
    st.markdown(
        """
        <div style="display: flex; justify-content: center; gap: 20px;">
            <div style="text-align: center; padding: 15px; width: 260px; 
                        border: 2px solid #6C63FF; border-radius: 12px; 
                        background: linear-gradient(135deg, #A3ABFF, #ECECFF); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
                <h5 style="color: #007BFF; margin: 0; font-size: 1.2em;">🔵 Rate Disputes</h5>
                <p style="margin: 10px 0; color: #2B55CC; font-size: 1.5em; font-weight: bold;">
                    10 Ongoing
                </p>
            </div>
            <div style="text-align: center; padding: 15px; width: 260px; 
                        border: 2px solid #FF5733; border-radius: 12px; 
                        background: linear-gradient(135deg, #F5B7B1, #FDEDEC); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
                <h5 style="color: #FF5733; margin: 0; font-size: 1.2em;">🔴 Volume Disputes</h5>
                <p style="margin: 10px 0; color: #C70039; font-size: 1.5em; font-weight: bold;">
                    5 Ongoing
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
)


    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    # Chart 1: Disputed Amounts by Carrier
    with col1:
        disputed_amounts = filtered_df.groupby('Carrier Name')['Disputed Amount (USD)'].sum().reset_index()
        disputed_amounts_fig = px.bar(
            disputed_amounts, x='Carrier Name', y='Disputed Amount (USD)', 
            title="Disputed Amounts by Carrier"
        )
        st.plotly_chart(disputed_amounts_fig, use_container_width=True)

    # Chart 2: Disputed Usage by Carrier
    with col2:
        disputed_usage = filtered_df.groupby('Carrier Name')['Disputed Usage (Mins)'].sum().reset_index()
        disputed_usage_fig = px.bar(
            disputed_usage, x='Carrier Name', y='Disputed Usage (Mins)', 
            title="Disputed Usage by Carrier"
        )
        st.plotly_chart(disputed_usage_fig, use_container_width=True)

     # Ensure 'Disputed Usage (Mins)' is added to the filtered dataframe
    if 'Disputed Usage (Mins)' not in filtered_df.columns:
        filtered_df['Disputed Usage (Mins)'] = np.random.uniform(0, 500, size=len(filtered_df)).round(2)
        filtered_df.loc[filtered_df['Dispute Type'] == 'Rate Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(0, 5000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Rate Dispute'])).round(2)
        filtered_df.loc[filtered_df['Dispute Type'] == 'Volume Dispute', 'Disputed Usage (Mins)'] = np.random.uniform(100, 2000, size=len(filtered_df[filtered_df['Dispute Type'] == 'Volume Dispute'])).round(2)

    if 'Disputed Amount (USD)' not in filtered_df.columns:
        filtered_df['Disputed Amount (USD)'] = (filtered_df['Disputed Usage (Mins)'] * np.random.uniform(0.05, 0.2, size=len(filtered_df))).round(2)

    # Dispute Count
    rate_disputes = len(filtered_df[filtered_df['Dispute Type'] == 'Rate Dispute'])
    volume_disputes = len(filtered_df[filtered_df['Dispute Type'] == 'Volume Dispute'])

    # Group by 'Carrier Name' and create the summary table
    summary_table3 = filtered_df.groupby('Carrier Name').agg({
        'Invoice Amount (USD)': 'sum',
        'Disputed Amount (USD)': 'sum',
        'Disputed Usage (Mins)': 'sum',
        'Dispute Type': lambda x: x.mode()[0] if not x.mode().empty else None,  # Fix here
        'Settlement Status': lambda x: x.mode()[0] if not x.mode().empty else None  # Similarly handle empty modes
    }).reset_index()

    st.dataframe(summary_table3, use_container_width=True, height=250)


# Tab 4: Settlement Summary
with tab4:
    st.subheader("Settlement Summary")

    # Group by 'Carrier Name' and aggregate the required fields
    summary_table4 = filtered_df.groupby('Carrier Name').agg({
        'Disputed Amount (USD)': 'sum',  # Summing disputed amounts per carrier
        'Settlement Status': 'count',  # Counting the invoices (total invoices per carrier)
    }).reset_index()

    # Rename 'Settlement Status' to 'Total Invoices' for clarity
    summary_table4.rename(columns={'Settlement Status': 'Total Invoices'}, inplace=True)

    # Define meaningful values based on telecom billing scenarios
    summary_table4['Settled Invoices'] = summary_table4.apply(
        lambda row: row['Total Invoices'] - np.random.randint(1, 3), axis=1
    )  # Randomly settled invoices
    summary_table4['Pending Settlements'] = summary_table4['Total Invoices'] - summary_table4['Settled Invoices']

    # Total Settled Amount: Assuming 80% of the disputed amount is settled
    summary_table4['Total Settled Amount'] = np.round(summary_table4['Disputed Amount (USD)'] * 0.8, 2)

    # Outstanding Amount: Remaining amount (20% of disputed amounts)
    summary_table4['Outstanding Amount'] = np.round(summary_table4['Disputed Amount (USD)'] * 0.2, 2)

    # Settlement Completion Rate: Ratio of settled invoices to total invoices
    summary_table4['Settlement Completion Rate'] = np.round(
        (summary_table4['Settled Invoices'] / summary_table4['Total Invoices']) * 100, 2
    )

    # Settlement Adjustment: Simulated random adjustments
    summary_table4['Settlement Adjustment'] = np.round(np.random.uniform(0, 500, len(summary_table4)), 2)

    # Calculate total pending settlements and disputed amount
    total_pending_settlements = summary_table4['Pending Settlements'].sum()
    total_disputed_amount = summary_table4['Disputed Amount (USD)'].sum()

    # Add counters for Total Pending Settlements and Total Disputed Amount
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; gap: 20px; margin: 20px;">
            <div style="text-align: center; padding: 15px; width: 270px; 
                        border: 2px solid #6C63FF; border-radius: 12px; 
                        background: linear-gradient(135deg, #A3ABFF, #ECECFF); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                <h5 style="color: #007BFF; margin: 0; font-size: 1.2em;">🔵 Unsettled Invoices</h5>
                <p style="margin: 10px 0; color: #2B55CC; font-size: 1.5em; font-weight: bold;">
                    {total_pending_settlements}
                </p>
            </div>
            <div style="text-align: center; padding: 15px; width: 270px; 
                        border: 2px solid #FF5733; border-radius: 12px; 
                        background: linear-gradient(135deg, #F5B7B1, #FDEDEC); 
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                <h5 style="color: #FF5733; margin: 0; font-size: 1.2em;">🔴 Unsettled Amount </h5>
                <p style="margin: 10px 0; color: #C70039; font-size: 1.5em; font-weight: bold;">
                    ${total_disputed_amount:,.2f}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Create columns for the two charts
    col1, col2 = st.columns(2)

    # Chart 1: Settlement Status by Carrier (Pie Chart)
    with col1:
        settlement_status = filtered_df.groupby(['Carrier Name', 'Settlement Status']).size().reset_index(name='Count')
        settlement_pie = px.pie(
            settlement_status, names='Settlement Status', values='Count', title="Overall Settlement Status"
        )
        settlement_pie.update_layout(
            title={
                'text': "Overall Settlement Status",
                'font': {'size': 24},  # Increase font size
                'x': 0.25  # Center title
            }
        )
        st.plotly_chart(settlement_pie, use_container_width=True)

    # Chart 2: Outstanding Amount by Carrier (Bar Chart)
    with col2:
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
        outstanding_bar.update_traces(
            texttemplate='%{text:.2f}',  # Format text to 2 decimal places
            textposition='outside',     # Position text outside bars
            textangle=0                 # Horizontal text
        )
        outstanding_bar.update_layout(
            title={
                'text': "Outstanding Amount by Carrier",
                'font': {'size': 24},  # Increase font size
                'x': 0.25  # Center title
            },
            xaxis_title="Carrier Name",
            yaxis_title="Outstanding Amount (USD)",
            template="plotly_white"
        )
        st.plotly_chart(outstanding_bar, use_container_width=True)

    # Display the summary table below the charts
    summary_table4_rounded = summary_table4.round(2)
    summary_table4_display = summary_table4_rounded.astype(str)
    st.dataframe(
        summary_table4_display.style.set_properties(**{'text-align': 'center'}), 
        use_container_width=True, 
        height=250
    )
