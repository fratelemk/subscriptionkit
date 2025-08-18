import os
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SubscriptionKit",
    page_icon="💳",
    layout="wide"
)

# Configuration constants
FILEPATH = "data.csv"
SALARY = 3500
SALARY_CURRENCY = "RON"
DEFAULT_CURRENCY = "EUR"
CURRENCIES = ("USD", "GBP", "EUR", "RON")

# Initialize currency converter
@st.cache_resource
def get_currency_converter():
    """Initialize and cache the currency converter."""
    try:
        return CurrencyConverter(verbose=False)
    except Exception as e:
        logger.error(f"Failed to initialize currency converter: {e}")
        st.error("Currency converter initialization failed. Please refresh the page.")
        return None

currency_converter = get_currency_converter()

def ensure_data_file_exists():
    """Create CSV file with headers if it doesn't exist."""
    if not os.path.exists(FILEPATH):
        df = pd.DataFrame(columns=["Subscription", "Currency", "Amount"])
        df.to_csv(FILEPATH, index=False)
        logger.info(f"Created new data file: {FILEPATH}")

def load_data():
    """Load subscription data with error handling."""
    ensure_data_file_exists()
    try:
        df = pd.read_csv(FILEPATH)
        if df.empty:
            return pd.DataFrame(columns=["Subscription", "Currency", "Amount"])
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error("Failed to load subscription data.")
        return pd.DataFrame(columns=["Subscription", "Currency", "Amount"])

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert currency with error handling."""
    if not currency_converter:
        return amount
    
    if from_currency == to_currency:
        return amount
    
    try:
        return currency_converter.convert(amount, from_currency, to_currency)
    except Exception as e:
        logger.error(f"Currency conversion failed: {from_currency} to {to_currency}, amount: {amount}, error: {e}")
        st.warning(f"Currency conversion failed for {from_currency} to {to_currency}. Using original amount.")
        return amount

def apply_conversion(row: pd.Series, target_currency: str) -> str:
    """Apply currency conversion to a row and format the result."""
    amount = float(row["Amount"])
    from_currency = row["Currency"]
    
    converted_amount = convert_currency(amount, from_currency, target_currency)
    return f"{converted_amount:.2f} {target_currency}"

def calculate_remaining_salary(total_expenses: float, expense_currency: str) -> str:
    """Calculate remaining salary after expenses."""
    if expense_currency == SALARY_CURRENCY:
        remaining = SALARY - total_expenses
    else:
        salary_in_expense_currency = convert_currency(SALARY, SALARY_CURRENCY, expense_currency)
        remaining = salary_in_expense_currency - total_expenses
    
    return f"{remaining:.2f} {expense_currency}"

def add_subscription(subscription: str, currency: str, amount: float) -> bool:
    """Add a new subscription to the CSV file."""
    try:
        new_record = pd.DataFrame(
            [[subscription, currency, amount]],
            columns=["Subscription", "Currency", "Amount"],
        )
        
        # Check if file has data to determine if we need headers
        file_is_empty = not os.path.exists(FILEPATH) or os.path.getsize(FILEPATH) == 0
        new_record.to_csv(FILEPATH, mode="a", header=file_is_empty, index=False)
        return True
    except Exception as e:
        logger.error(f"Failed to add subscription: {e}")
        st.error("Failed to add subscription. Please try again.")
        return False

def validate_subscription_input(subscription: str, currency: str, amount: float) -> tuple[bool, str]:
    """Validate user input for new subscription."""
    if not subscription or not subscription.strip():
        return False, "Subscription name cannot be empty."
    
    if not currency:
        return False, "Please select a currency."
    
    if amount <= 0:
        return False, "Amount must be greater than 0."
    
    return True, ""

# Main app
def main():
    st.title("💳 SubscriptionKit")
    st.write("Track your monthly subscriptions and manage your budget.")
    
    if not currency_converter:
        st.stop()
    
    # Add new subscription section
    with st.expander("➕ Add New Subscription", expanded=False):
        with st.form("add_subscription_form", border=False, clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                subscription = st.text_input("Subscription Name", placeholder="e.g., Netflix, Spotify")
            
            with col2:
                currency = st.selectbox("Currency", CURRENCIES, index=1)  # Default to GBP
            
            with col3:
                amount = st.number_input("Monthly Amount", min_value=0.01, format="%.2f", value=9.99)
            
            submit = st.form_submit_button("Add Subscription", use_container_width=True)
            
            if submit:
                is_valid, error_message = validate_subscription_input(subscription, currency, amount)
                
                if is_valid:
                    if add_subscription(subscription.strip(), currency, amount):
                        st.success(f"✅ Added: {subscription} - {amount:.2f} {currency}")
                        st.rerun()
                else:
                    st.error(f"❌ {error_message}")
    
    st.divider()
    
    # Load and display data
    df = load_data()
    
    if df.empty:
        st.info("No subscriptions found. Add your first subscription above!")
        return
    
    # Convert amounts for display
    df_display = df.copy()
    df_display["Amount (Original)"] = df_display.apply(
        lambda row: f"{row['Amount']:.2f} {row['Currency']}", axis=1
    )
    df_display["Amount"] = df_display.apply(
        lambda row: apply_conversion(row, DEFAULT_CURRENCY), axis=1
    )
    
    # Calculate total
    total_amount = sum(
        float(amount_str.split()[0]) 
        for amount_str in df_display["Amount"]
    )

    # Display dataframe
    st.subheader("📊 Your Subscriptions")
    
    # Reorder columns for better display
    display_columns = ["Subscription", "Amount (Original)", "Amount"]
    st.dataframe(
        df_display[display_columns], 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Subscription": st.column_config.TextColumn("Service"),
            "Amount (Original)": st.column_config.TextColumn("Original Amount"),
            "Amount": st.column_config.TextColumn(f"Amount ({DEFAULT_CURRENCY})")
        }
    )

    st.divider()
    
    # Monthly report
    st.subheader("📈 Monthly Report")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Monthly Costs", 
            value=f"{total_amount:.2f} {DEFAULT_CURRENCY}"
        )
    
    with col2:
        remaining = calculate_remaining_salary(total_amount, DEFAULT_CURRENCY)
        remaining_value = float(remaining.split()[0])
        delta_color = "normal" if remaining_value >= 0 else "inverse"
        st.metric(label="Remaining Salary", value=remaining)
    
    with col3:
        if total_amount > 0:
            percentage = (total_amount / convert_currency(SALARY, SALARY_CURRENCY, DEFAULT_CURRENCY)) * 100
            st.metric(
                label="% of Salary Used", 
                value=f"{percentage:.1f}%"
            )

    st.divider()
    
    # Add delete functionality
    if len(df) > 0:
        with st.expander("🗑️ Manage Subscriptions"):
            subscription_to_delete = st.selectbox(
                "Select subscription to delete:",
                options=df.index,
                format_func=lambda x: f"{df.iloc[x]['Subscription']} - {df.iloc[x]['Amount']:.2f} {df.iloc[x]['Currency']}"
            )
            
            if st.button("Delete Selected Subscription", type="secondary"):
                try:
                    df_updated = df.drop(subscription_to_delete).reset_index(drop=True)
                    df_updated.to_csv(FILEPATH, index=False)
                    st.success("Subscription deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete subscription: {e}")

if __name__ == "__main__":
    main()
