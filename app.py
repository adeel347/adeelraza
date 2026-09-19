import streamlit as st
import pandas as pd
from datetime import date, time
from supabase import create_client, Client

st.set_page_config(page_title="Stock Trading Tracker", page_icon="📈", layout="centered")

# ------------------------------------------------------------------------------
# 1. MOBILE HARDWARE BACK-BUTTON INTERCEPTOR & UNSAVED ALERT
# ------------------------------------------------------------------------------
st.html("""
<script>
    const parentWin = window.parent;
    parentWin.addEventListener('beforeunload', (event) => {
        event.preventDefault();
        event.returnValue = '';
    });

    if (!parentWin.history.state || parentWin.history.state.page !== 'trading_app') {
        parentWin.history.pushState({ page: 'trading_app', step: 1 }, '', '');
    }

    parentWin.onpopstate = function(event) {
        parentWin.history.pushState({ page: 'trading_app', step: 2 }, '', '');
        const backBtn = parentWin.document.querySelector('button:has-text("⬅️ Back")');
        if (backBtn) {
            backBtn.click();
        }
    };
</script>
""")

# ------------------------------------------------------------------------------
# 2. CSS STYLING
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Persistent Sticky Top Header */
    .sticky-header-container {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 9999;
        background-color: #0e1117;
        padding-top: 8px;
        padding-bottom: 8px;
        margin-bottom: 12px;
        border-bottom: 1px solid #262730;
    }

    .sticky-header-container div[data-testid="stButton"] button {
        width: 100% !important;
        height: 38px !important;
        font-size: 13px !important;
        margin: 0 !important;
        padding: 0px 4px !important;
    }

    /* Menu container holding half-screen action buttons */
    .menu-button-box div[data-testid="stButton"] button {
        height: 52px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        margin: 6px 0px !important;
        border-radius: 8px !important;
    }

    .login-form-box div[data-testid="stFormSubmitButton"] button {
        width: 160px !important;
        height: 42px !important;
        font-size: 15px !important;
        margin: 10px auto !important;
        display: block !important;
        border-radius: 6px !important;
    }

    /* Market Selector Buttons */
    div[data-testid="stButton"] button:has-text("Pakistani Stocks") {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
        height: 56px !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }
    div[data-testid="stButton"] button:has-text("International Stocks") {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        height: 56px !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* Green Purchase Button */
    div[data-testid="stButton"] button:has-text("➕ Purchase Record") {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
    }
    /* Red Sell Button */
    div[data-testid="stButton"] button:has-text("➖ Sell Record") {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    /* Blue Analytics and Cash Buttons */
    div[data-testid="stButton"] button:has-text("📅 Weekly Summary"),
    div[data-testid="stButton"] button:has-text("🗓️ Monthly Summary"),
    div[data-testid="stButton"] button:has-text("🏆 Annual Performance"),
    div[data-testid="stButton"] button:has-text("📊 Capital Gain Tax"),
    div[data-testid="stButton"] button:has-text("📥 Deposit"),
    div[data-testid="stButton"] button:has-text("📤 Withdrawal") {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
    }

    /* Dual Metric Banner */
    .metric-banner {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 16px;
    }
    .metric-card-box {
        flex: 1;
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #3b82f6;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .metric-title-txt {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-val-txt {
        color: #f8fafc;
        font-size: 24px;
        font-weight: 800;
        margin-top: 4px;
    }

    @media (max-width: 768px) {
        .pc-only-module {
            display: none !important;
        }
        .metric-banner {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. SUPABASE CLIENT INITIALIZATION
# ------------------------------------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# 4. NAVIGATION STATE MANAGEMENT
# ------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "market" not in st.session_state:
    st.session_state.market = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "HOME"
if "nav_stack" not in st.session_state:
    st.session_state.nav_stack = []
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "LOGIN"
if "active_editing_id" not in st.session_state:
    st.session_state.active_editing_id = None

def navigate_to(page, market=None):
    st.session_state.nav_stack.append((st.session_state.market, st.session_state.current_page))
    if market is not None:
        st.session_state.market = market
    st.session_state.current_page = page
    st.session_state.active_editing_id = None
    st.rerun()

def go_back():
    if st.session_state.nav_stack:
        prev_market, prev_page = st.session_state.nav_stack.pop()
        st.session_state.market = prev_market
        st.session_state.current_page = prev_page
    else:
        st.session_state.market = None
        st.session_state.current_page = "HOME"
    st.session_state.active_editing_id = None
    st.rerun()

# ------------------------------------------------------------------------------
# 5. AUTHENTICATION (Login & Forgot Password)
# ------------------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🔐 Trader Portal Login</h2>", unsafe_allow_html=True)
    if st.session_state.auth_view == "LOGIN":
        st.markdown('<div class="login-form-box">', unsafe_allow_html=True)
        with st.form("login_form"):
            email_in = st.text_input("Email", value="")
            pass_in = st.text_input("Password", type="password", value="")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_in, "password": pass_in})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_email = res.user.email
                        st.session_state.market = None
                        st.session_state.current_page = "HOME"
                        st.session_state.nav_stack = []
                        st.rerun()
                except Exception as e:
                    st.error(f"Sign in failed: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

        _, f_col, _ = st.columns([1, 2, 1])
        with f_col:
            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.auth_view = "FORGOT"
                st.rerun()

    elif st.session_state.auth_view == "FORGOT":
        st.write("Enter your email to receive recovery instructions.")
        with st.form("forgot_form"):
            reset_email = st.text_input("Email Address", value="")
            reset_submit = st.form_submit_button("Send Recovery Email", use_container_width=True)
            if reset_submit:
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Recovery email sent!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        _, b_col, _ = st.columns([1, 2, 1])
        with b_col:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "LOGIN"
                st.rerun()

    st.stop()

# ------------------------------------------------------------------------------
# 6. PERSISTENT STICKY TOP BAR
# ------------------------------------------------------------------------------
st.markdown('<div class="sticky-header-container">', unsafe_allow_html=True)
is_home_page = (st.session_state.current_page == "HOME" or st.session_state.market is None)

if is_home_page:
    col_home, col_title, col_pw, col_out = st.columns([1.5, 3.5, 2.5, 1.5])
    with col_home:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.market = None
            st.session_state.current_page = "HOME"
            st.session_state.nav_stack = []
            st.rerun()
    with col_title:
        st.markdown("<div style='text-align:center; font-weight:bold; font-size:16px; margin-top:6px;'>Portfolio Selection</div>", unsafe_allow_html=True)
    with col_pw:
        if st.button("🔑 Change Password", use_container_width=True):
            navigate_to("CHANGE_PW")
    with col_out:
        if st.button("🚪 Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.session_state.market = None
            st.session_state.current_page = "HOME"
            st.session_state.nav_stack = []
            st.rerun()
else:
    col_home, col_back, col_title, col_stat, col_out = st.columns([1.2, 1.2, 3.8, 1.8, 1.4])
    with col_home:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.market = None
            st.session_state.current_page = "HOME"
            st.session_state.nav_stack = []
            st.rerun()
    with col_back:
        if st.button("⬅️ Back", use_container_width=True):
            go_back()
    with col_title:
        badge = "Pakistani Stocks" if st.session_state.market == "PK" else "International Stocks"
        st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:16px; margin-top:6px;'>{badge}</div>", unsafe_allow_html=True)
    with col_stat:
        st.button("🔐 Logged In", disabled=True, use_container_width=True)
    with col_out:
        if st.button("🚪 Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.session_state.market = None
            st.session_state.current_page = "HOME"
            st.session_state.nav_stack = []
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. CHANGE PASSWORD VIEW
# ------------------------------------------------------------------------------
if st.session_state.current_page == "CHANGE_PW":
    st.header("🔑 Change Password")
    with st.form("change_pw_form"):
        st.write(f"Logged in user: **{st.session_state.user_email}**")
        new_pw = st.text_input("New Password", type="password", value="")
        conf_pw = st.text_input("Confirm New Password", type="password", value="")
        submit_pw = st.form_submit_button("Update Password", use_container_width=True)

        if submit_pw:
            if not new_pw or len(new_pw) < 6:
                st.error("Password must be at least 6 characters long.")
            elif new_pw != conf_pw:
                st.error("Passwords do not match.")
            else:
                try:
                    supabase.auth.update_user({"password": new_pw})
                    st.success("✅ Password updated successfully!")
                except Exception as e:
                    st.error(f"Failed to update password: {str(e)}")

    _, ret_col, _ = st.columns([1, 2, 1])
    with ret_col:
        if st.button("⬅️ Return to Home", use_container_width=True):
            st.session_state.market = None
            st.session_state.current_page = "HOME"
            st.rerun()
    st.stop()

# ------------------------------------------------------------------------------
# 8. HOME: MARKET SELECTION SCREEN
# ------------------------------------------------------------------------------
if st.session_state.current_page == "HOME" or st.session_state.market is None:
    st.markdown("<h2 style='text-align:center; margin-bottom: 25px;'>Choose Your Portfolio</h2>", unsafe_allow_html=True)

    _, center_box, _ = st.columns([1, 2, 1])
    with center_box:
        st.markdown('<div class="menu-button-box">', unsafe_allow_html=True)
        if st.button("Pakistani Stocks", use_container_width=True):
            navigate_to("MARKET_MENU", market="PK")

        st.write("")

        if st.button("International Stocks", use_container_width=True):
            navigate_to("MARKET_MENU", market="INTL")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

MARKET = st.session_state.market
CURRENCY = "PKR" if MARKET == "PK" else "USD"

def load_buys():
    try:
        res = supabase.table("buy_orders").select("*").eq("market", MARKET).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def load_sells():
    try:
        res = supabase.table("sell_orders").select("*").eq("market", MARKET).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def load_cash():
    try:
        res = supabase.table("cash_flows").select("*").eq("market", MARKET).order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# Helper: Compute Free Cash & Total Portfolio Equity
def calculate_financials():
    cash_df = load_cash()
    buys_df = load_buys()
    sells_df = load_sells()

    total_dep = cash_df[cash_df["flow_type"] == "DEPOSIT"]["amount"].sum() if not cash_df.empty else 0.0
    total_wth = cash_df[cash_df["flow_type"] == "WITHDRAWAL"]["amount"].sum() if not cash_df.empty else 0.0

    total_buy_spend = buys_df["total_cost"].sum() if not buys_df.empty else 0.0
    total_sell_revenue = ((sells_df["shares_sold"] * sells_df["sale_price"]) - sells_df["selling_fees"] - sells_df["cgt_tax"]).sum() if not sells_df.empty else 0.0

    free_cash = (total_dep - total_wth) - total_buy_spend + total_sell_revenue
    open_holdings_val = (buys_df["shares_remaining"] * buys_df["price_per_share"]).sum() if not buys_df.empty else 0.0
    total_equity = free_cash + open_holdings_val

    return free_cash, total_equity

# ------------------------------------------------------------------------------
# 9. DEDICATED MARKET OPTIONS MENU PAGE
# ------------------------------------------------------------------------------
if st.session_state.current_page == "MARKET_MENU":
    free_cash, total_equity = calculate_financials()

    st.markdown(f"""
    <div class="metric-banner">
        <div class="metric-card-box">
            <div class="metric-title-txt">Total Equity</div>
            <div class="metric-val-txt">{CURRENCY} {total_equity:,.2f}</div>
        </div>
        <div class="metric-card-box">
            <div class="metric-title-txt">Free Cash (Liquid)</div>
            <div class="metric-val-txt" style="color: #10b981;">{CURRENCY} {free_cash:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, btn_center_col, _ = st.columns([1, 2, 1])
    with btn_center_col:
        st.markdown('<div class="menu-button-box">', unsafe_allow_html=True)

        if st.button("➕ Purchase Record", use_container_width=True):
            navigate_to("PURCHASE")

        if st.button("➖ Sell Record", use_container_width=True):
            navigate_to("SELL")

        if st.button("📥 Deposit", use_container_width=True):
            navigate_to("DEPOSIT")

        if st.button("📤 Withdrawal", use_container_width=True):
            navigate_to("WITHDRAWAL")

        st.markdown('<div class="pc-only-module">', unsafe_allow_html=True)

        if st.button("📅 Weekly Summary", use_container_width=True):
            navigate_to("WEEKLY")

        if st.button("🗓️ Monthly Summary", use_container_width=True):
            navigate_to("MONTHLY")

        if st.button("🏆 Annual Performance", use_container_width=True):
            navigate_to("ANNUAL")

        if st.button("📊 Capital Gain Tax", use_container_width=True):
            navigate_to("CGT")

        st.markdown('</div></div>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("🔍 Current Open Holdings")
    buys_df = load_buys()
    search_sym = st.text_input("Search Stock Symbol:", value="").strip().upper()
    
    if not buys_df.empty:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        if search_sym:
            open_lots = open_lots[open_lots["symbol"].str.startswith(search_sym, na=False)]
            if open_lots.empty:
                st.warning("⚠️ Ticker not available")
        
        if not open_lots.empty:
            open_lots["lot_value"] = open_lots["shares_remaining"] * open_lots["price_per_share"]
            
            agg_dict = {
                "id": "max",
                "stock_name": "first",
                "shares_remaining": "sum",
                "lot_value": "sum"
            }
            if MARKET == "INTL":
                agg_dict["country"] = "first"

            grouped = open_lots.groupby("symbol", as_index=False).agg(agg_dict)
            grouped["avg_price"] = grouped["lot_value"] / grouped["shares_remaining"]
            grouped = grouped.sort_values(by="id", ascending=False).reset_index(drop=True)

            grouped["#"] = range(1, len(grouped) + 1)
            grouped["shares_remaining"] = grouped["shares_remaining"].apply(lambda v: f"{v:,.2f}")
            grouped["avg_price"] = grouped["avg_price"].apply(lambda v: f"{v:,.2f}")
            grouped["lot_value"] = grouped["lot_value"].apply(lambda v: f"{v:,.2f}")

            cols_order = ["#", "symbol", "stock_name", "shares_remaining", "avg_price", "lot_value"]
            col_labels = ["#", "Symbol", "Stock Name", "Total Shares", f"Avg Buy Price ({CURRENCY})", f"Total Value ({CURRENCY})"]

            if MARKET == "INTL":
                cols_order.insert(3, "country")
                col_labels.insert(3, "Country")

            display_grouped = grouped[cols_order].copy()
            display_grouped.columns = col_labels
            st.dataframe(display_grouped, use_container_width=True, hide_index=True)
        else:
            st.info("No active open shares currently held.")
    else:
        st.info("No purchases recorded yet.")
    st.stop()

# ------------------------------------------------------------------------------
# 10. ENTRY SUBPAGES
# ------------------------------------------------------------------------------

# PURCHASE ENTRY
if st.session_state.current_page == "PURCHASE":
    st.header("➕ Purchase Record Entry")
    free_cash, _ = calculate_financials()
    st.caption(f"Available Free Cash: **{CURRENCY} {free_cash:,.2f}**")

    buys_df = load_buys()
    existing_symbols = buys_df["symbol"].unique().tolist() if not buys_df.empty else []

    with st.form("purchase_form"):
        st.warning("⚠️ Changes are NOT saved until you click 'Save Purchase Changes' below.")
        p_date = st.date_input("Purchase Date", value=date.today())
        
        country_val = "Pakistan"
        if MARKET == "INTL":
            country_val = st.text_input("Country", value="", placeholder="e.g., United States")

        sym = st.text_input("Stock Symbol", value="", placeholder="e.g., SYS, OGDC, AAPL")
        s_name = st.text_input("Stock Name", value="", placeholder="e.g., Systems Limited, Apple Inc.")

        if sym and sym.strip().upper() in existing_symbols:
            st.info(f"ℹ️ {sym.strip().upper()} exists in your holdings. This entry adds to your total shares.")

        # Correct blank inputs: value=None with placeholder for numbers
        shares = st.number_input("Number of Shares", min_value=0.0, value=None, step=1.0, format="%.4f", placeholder="Enter number of shares")
        price = st.number_input(f"Purchase Price per Share ({CURRENCY})", min_value=0.0, value=None, step=0.5, format="%.2f", placeholder="Enter purchase price")
        fees = st.number_input(f"Brokerage Commission ({CURRENCY})", min_value=0.0, value=None, step=1.0, format="%.2f", placeholder="Enter fees (if any)")
        taxes = st.number_input(f"Levies / Taxes ({CURRENCY})", min_value=0.0, value=None, step=1.0, format="%.2f", placeholder="Enter taxes (if any)")

        save_p = st.form_submit_button("Save Purchase Changes", use_container_width=True)
        if save_p:
            clean_sym = sym.strip().upper() if sym else ""
            clean_name = s_name.strip() if s_name else ""
            clean_country = country_val.strip() if country_val else "Pakistan"
            val_shares = float(shares) if shares is not None else 0.0
            val_price = float(price) if price is not None else 0.0
            val_fees = float(fees) if fees is not None else 0.0
            val_taxes = float(taxes) if taxes is not None else 0.0

            if not clean_sym or not clean_name:
                st.error("Please enter both Stock Symbol and Stock Name.")
            elif val_shares <= 0 or val_price <= 0:
                st.error("Please enter a valid number of shares and price per share.")
            else:
                total_val = (val_shares * val_price) + val_fees + val_taxes

                if total_val > free_cash:
                    st.error(f"❌ Insufficient Free Cash! Available: {CURRENCY} {free_cash:,.2f} | Required: {CURRENCY} {total_val:,.2f}. Free cash cannot go negative.")
                else:
                    payload = {
                        "market": str(MARKET),
                        "country": clean_country,
                        "purchase_date": p_date.strftime("%Y-%m-%d"),
                        "symbol": clean_sym,
                        "stock_name": clean_name,
                        "shares_bought": val_shares,
                        "price_per_share": val_price,
                        "fees": val_fees,
                        "taxes": val_taxes,
                        "total_cost": round(float(total_val), 2),
                        "shares_remaining": val_shares
                    }
                    try:
                        supabase.table("buy_orders").insert(payload).execute()
                        st.success(f"✅ Purchase of {val_shares} shares of {clean_sym} recorded!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error saving purchase: {err}")

    st.write("---")
    st.subheader("📜 Recorded Purchases")
    search_p = st.text_input("🔍 Search Purchase by Symbol (e.g., B, BA):", key="search_p_sym", value="").strip().upper()
    
    buys_all = load_buys()
    if not buys_all.empty:
        display_buys = buys_all.sort_values(by="id", ascending=False).reset_index(drop=True)
        if search_p:
            display_buys = display_buys[display_buys["symbol"].str.startswith(search_p, na=False)].reset_index(drop=True)
            if display_buys.empty:
                st.warning("⚠️ No matching stock symbol found")

        h1, h2, h3, h4, h5, h6, h7 = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.3, 0.8])
        h1.markdown("**#**")
        h2.markdown("**Symbol**")
        h3.markdown("**Date**")
        h4.markdown("**Shares**")
        h5.markdown("**Price**")
        h6.markdown("**Total Cost**")
        h7.markdown("**Action**")

        for idx, item in display_buys.iterrows():
            item_id = item["id"]
            seq_num = idx + 1
            c1, c2, c3, c4, c5, c6, c7 = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.3, 0.8])
            c1.write(f"{seq_num}")
            c2.write(f"{item['symbol']}")
            c3.write(f"{item['purchase_date']}")
            c4.write(f"{item['shares_bought']:,.2f}")
            c5.write(f"{item['price_per_share']:,.2f}")
            c6.write(f"{item['total_cost']:,.2f}")
            with c7:
                with st.popover("⋮"):
                    if st.button("✏️ Edit", key=f"btn_edit_buy_{item_id}", use_container_width=True):
                        st.session_state.active_editing_id = item_id
                    if st.button("🗑️ Delete", key=f"btn_del_buy_{item_id}", use_container_width=True):
                        supabase.table("buy_orders").delete().eq("id", item_id).execute()
                        st.success(f"Deleted Purchase Record #{seq_num}")
                        st.rerun()

            if st.session_state.active_editing_id == item_id:
                with st.form(f"edit_form_buy_{item_id}"):
                    st.write(f"Editing Purchase Record #{seq_num}")
                    sym_val = st.text_input("Stock Symbol", value=item["symbol"]).strip().upper()
                    name_val = st.text_input("Stock Name", value=item["stock_name"]).strip()
                    date_val = st.date_input("Purchase Date", value=pd.to_datetime(item["purchase_date"]).date())
                    sh_val = st.number_input("Shares Bought", value=float(item["shares_bought"]), min_value=0.0001)
                    pr_val = st.number_input("Price per Share", value=float(item["price_per_share"]), min_value=0.01)
                    fe_val = st.number_input("Fees", value=float(item["fees"]), min_value=0.0)
                    tx_val = st.number_input("Taxes", value=float(item["taxes"]), min_value=0.0)

                    if st.form_submit_button("Save Changes", use_container_width=True):
                        new_tot = (sh_val * pr_val) + fe_val + tx_val
                        old_tot = float(item["total_cost"])
                        delta_cost = new_tot - old_tot
                        curr_free_cash, _ = calculate_financials()

                        if delta_cost > curr_free_cash:
                            st.error(f"❌ Insufficient Free Cash! Extra cost: {CURRENCY} {delta_cost:,.2f} | Available: {CURRENCY} {curr_free_cash:,.2f}. Free cash cannot go negative.")
                        else:
                            sold_shares = float(item["shares_bought"]) - float(item["shares_remaining"])
                            new_remaining = max(0.0, sh_val - sold_shares)

                            payload = {
                                "symbol": sym_val,
                                "stock_name": name_val,
                                "purchase_date": date_val.strftime("%Y-%m-%d"),
                                "shares_bought": float(sh_val),
                                "price_per_share": float(pr_val),
                                "fees": float(fe_val),
                                "taxes": float(tx_val),
                                "total_cost": round(float(new_tot), 2),
                                "shares_remaining": float(new_remaining)
                            }
                            supabase.table("buy_orders").update(payload).eq("id", item_id).execute()
                            st.session_state.active_editing_id = None
                            st.success("✅ Purchase updated successfully!")
                            st.rerun()
    else:
        st.info("No purchases recorded yet.")

# SELL ENTRY
elif st.session_state.current_page == "SELL":
    st.header("➖ Sell Record Entry")
    buys_df = load_buys()
    if buys_df.empty:
        st.warning("No purchase inventory available.")
    else:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        unique_symbols = sorted(open_lots["symbol"].unique().tolist()) if not open_lots.empty else []

        if unique_symbols:
            selected_symbol = st.selectbox(
                "Select Stock Symbol to Sell:",
                options=unique_symbols,
                help="Type to search your available stock symbols"
            )

            symbol_lots = open_lots[open_lots["symbol"] == selected_symbol].sort_values(by="purchase_date").copy()
            total_avail_shares = float(symbol_lots["shares_remaining"].sum())
            first_lot = symbol_lots.iloc[0]

            with st.form("sell_form"):
                st.warning("⚠️ Changes are NOT saved until you click 'Save Sell Changes' below.")
                st.info(f"Selected: **{selected_symbol}** ({first_lot['stock_name']}) | Total Available: **{total_avail_shares:,.2f}** shares")
                s_date = st.date_input("Sale Date", value=date.today())

                shares_to_sell = st.number_input(f"Shares to Sell (Max: {total_avail_shares:,.2f})", min_value=0.0, max_value=total_avail_shares, value=None, step=1.0, format="%.4f", placeholder="Enter shares to sell")
                sell_price = st.number_input(f"Selling Price per Share ({CURRENCY})", min_value=0.0, value=None, step=0.5, format="%.2f", placeholder="Enter selling price")
                sell_fees = st.number_input(f"Selling Fees ({CURRENCY})", min_value=0.0, value=None, step=1.0, format="%.2f", placeholder="Enter selling fees (if any)")
                cgt_rate = st.number_input("Capital Gain Tax %", min_value=0.0, max_value=100.0, value=None, step=0.5, placeholder="Enter CGT rate % (if any)")

                save_s = st.form_submit_button("Save Sell Changes", use_container_width=True)
                if save_s:
                    val_shares_sell = float(shares_to_sell) if shares_to_sell is not None else 0.0
                    val_sell_price = float(sell_price) if sell_price is not None else 0.0
                    val_sell_fees = float(sell_fees) if sell_fees is not None else 0.0
                    val_cgt_rate = float(cgt_rate) if cgt_rate is not None else 0.0

                    if val_shares_sell <= 0 or val_sell_price <= 0:
                        st.error("Please enter a valid number of shares and selling price.")
                    elif val_shares_sell > total_avail_shares:
                        st.error("❌ Sale quantity exceeds available shares!")
                    else:
                        remaining_to_sell = val_shares_sell
                        total_net_pnl = 0.0

                        for _, lot_row in symbol_lots.iterrows():
                            if remaining_to_sell <= 0:
                                break
                            
                            lot_avail = float(lot_row["shares_remaining"])
                            shares_from_lot = min(remaining_to_sell, lot_avail)
                            unit_cost = float(lot_row["total_cost"]) / float(lot_row["shares_bought"])
                            cost_basis = shares_from_lot * unit_cost
                            gross_rev = shares_from_lot * val_sell_price
                            
                            allocated_fee = (shares_from_lot / val_shares_sell) * val_sell_fees
                            lot_gross_pnl = gross_rev - cost_basis - allocated_fee
                            lot_tax = (lot_gross_pnl * (val_cgt_rate / 100.0)) if lot_gross_pnl > 0 else 0.0
                            lot_net_pnl = lot_gross_pnl - lot_tax

                            sell_payload = {
                                "buy_order_id": int(lot_row["id"]),
                                "market": str(MARKET),
                                "country": str(lot_row.get("country", "Pakistan")),
                                "sale_date": s_date.strftime("%Y-%m-%d"),
                                "symbol": str(selected_symbol),
                                "stock_name": str(lot_row["stock_name"]),
                                "shares_sold": float(shares_from_lot),
                                "buy_price": float(lot_row["price_per_share"]),
                                "buy_date": str(lot_row["purchase_date"]),
                                "sale_price": float(val_sell_price),
                                "selling_fees": round(float(allocated_fee), 2),
                                "gross_pnl": round(float(lot_gross_pnl), 2),
                                "cgt_rate": float(val_cgt_rate),
                                "cgt_tax": round(float(lot_tax), 2),
                                "net_pnl": round(float(lot_net_pnl), 2)
                            }
                            supabase.table("sell_orders").insert(sell_payload).execute()
                            supabase.table("buy_orders").update({"shares_remaining": lot_avail - shares_from_lot}).eq("id", lot_row["id"]).execute()

                            remaining_to_sell -= shares_from_lot
                            total_net_pnl += lot_net_pnl

                        st.success(f"✅ Sale logged for {val_shares_sell} shares of {selected_symbol}! Total Net P&L: {CURRENCY} {total_net_pnl:,.2f}")
                        st.rerun()
        else:
            st.info("No open stock positions currently available to sell.")

    st.write("---")
    st.subheader("📜 Recorded Sales")
    search_s = st.text_input("🔍 Search Sold Records by Symbol (e.g., B, BA):", key="search_s_sym", value="").strip().upper()
    
    sells_all = load_sells()
    if not sells_all.empty:
        display_sells = sells_all.sort_values(by="id", ascending=False).reset_index(drop=True)
        if search_s:
            display_sells = display_sells[display_sells["symbol"].str.startswith(search_s, na=False)].reset_index(drop=True)
            if display_sells.empty:
                st.warning("⚠️ No matching stock symbol found")

        sh1, sh2, sh3, sh4, sh5, sh6, sh7 = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.3, 0.8])
        sh1.markdown("**#**")
        sh2.markdown("**Symbol**")
        sh3.markdown("**Date**")
        sh4.markdown("**Shares**")
        sh5.markdown("**Price**")
        sh6.markdown("**Net P&L**")
        sh7.markdown("**Action**")

        for idx, item in display_sells.iterrows():
            item_id = item["id"]
            seq_num = idx + 1
            sc1, sc2, sc3, sc4, sc5, sc6, sc7 = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.3, 0.8])
            sc1.write(f"{seq_num}")
            sc2.write(f"{item['symbol']}")
            sc3.write(f"{item['sale_date']}")
            sc4.write(f"{item['shares_sold']:,.2f}")
            sc5.write(f"{item['sale_price']:,.2f}")
            sc6.write(f"{item['net_pnl']:,.2f}")
            with sc7:
                with st.popover("⋮"):
                    if st.button("✏️ Edit", key=f"btn_edit_sell_{item_id}", use_container_width=True):
                        st.session_state.active_editing_id = item_id
                    if st.button("🗑️ Delete", key=f"btn_del_sell_{item_id}", use_container_width=True):
                        supabase.table("sell_orders").delete().eq("id", item_id).execute()
                        st.success(f"Deleted Sell Record #{seq_num}")
                        st.rerun()

            if st.session_state.active_editing_id == item_id:
                with st.form(f"edit_form_sell_{item_id}"):
                    st.write(f"Editing Sell Record #{seq_num}")
                    ss_sym = st.text_input("Stock Symbol", value=item["symbol"]).strip().upper()
                    ss_name = st.text_input("Stock Name", value=item["stock_name"]).strip()
                    ss_date = st.date_input("Sale Date", value=pd.to_datetime(item["sale_date"]).date())
                    ss_sh = st.number_input("Shares Sold", value=float(item["shares_sold"]))
                    ss_sp = st.number_input("Sale Price", value=float(item["sale_price"]))
                    ss_bp = st.number_input("Buy Price Basis", value=float(item["buy_price"]))
                    ss_fe = st.number_input("Selling Fees", value=float(item["selling_fees"]))
                    ss_rt = st.number_input("CGT Rate %", value=float(item["cgt_rate"]))

                    if st.form_submit_button("Save Changes", use_container_width=True):
                        gross = (ss_sh * ss_sp) - (ss_sh * ss_bp) - ss_fe
                        cgt = (gross * (ss_rt / 100.0)) if gross > 0 else 0.0
                        net = gross - cgt
                        payload = {
                            "symbol": ss_sym,
                            "stock_name": ss_name,
                            "sale_date": ss_date.strftime("%Y-%m-%d"),
                            "shares_sold": float(ss_sh),
                            "sale_price": float(ss_sp),
                            "buy_price": float(ss_bp),
                            "selling_fees": float(ss_fe),
                            "gross_pnl": round(float(gross), 2),
                            "cgt_rate": float(ss_rt),
                            "cgt_tax": round(float(cgt), 2),
                            "net_pnl": round(float(net), 2)
                        }
                        supabase.table("sell_orders").update(payload).eq("id", item_id).execute()
                        st.session_state.active_editing_id = None
                        st.success("✅ Sell record updated!")
                        st.rerun()
    else:
        st.info("No completed sales recorded yet.")

# DEPOSIT & WITHDRAWAL ENTRY
elif st.session_state.current_page in ["DEPOSIT", "WITHDRAWAL"]:
    flow_kind = st.session_state.current_page
    st.header(f"{'📥 Cash Deposit' if flow_kind == 'DEPOSIT' else '📤 Cash Withdrawal'}")
    free_cash, _ = calculate_financials()
    st.caption(f"Available Free Cash: **{CURRENCY} {free_cash:,.2f}**")

    with st.form("cash_flow_form"):
        st.warning("⚠️ Changes are NOT saved until you click 'Save Transaction' below.")
        e_date = st.date_input("Transaction Date", value=date.today())
        e_time = st.time_input("Transaction Time", value=time(12, 0))
        
        c_country = "Pakistan"
        if MARKET == "INTL":
            # Fix: Use value="" instead of value=None to avoid AttributeError[cite: 7, 10]
            c_country = st.text_input("Origin/Destination Country", value="", placeholder="e.g., United States")

        amt = st.number_input(f"Amount ({CURRENCY})", min_value=0.0, value=None, step=100.0, format="%.2f", placeholder="Enter amount")
        memo = st.text_input("Notes (Bank reference, wallet ID, etc.)", value="", placeholder="Optional notes")

        save_c = st.form_submit_button("Save Transaction", use_container_width=True)
        if save_c:
            val_amt = float(amt) if amt is not None else 0.0
            clean_c_country = c_country.strip() if c_country else "Pakistan"
            if val_amt <= 0:
                st.error("Please enter a valid amount greater than 0.")
            elif flow_kind == "WITHDRAWAL" and val_amt > free_cash:
                st.error(f"❌ Insufficient Free Cash! Available: {CURRENCY} {free_cash:,.2f} | Requested: {CURRENCY} {val_amt:,.2f}. Free cash cannot go negative.")
            else:
                payload = {
                    "market": str(MARKET),
                    "country": clean_c_country,
                    "entry_date": e_date.strftime("%Y-%m-%d"),
                    "entry_time": e_time.strftime("%H:%M:%S"),
                    "flow_type": str(flow_kind),
                    "amount": val_amt,
                    "notes": str(memo).strip() if memo else None
                }
                try:
                    supabase.table("cash_flows").insert(payload).execute()
                    st.success(f"✅ {flow_kind} of {CURRENCY} {val_amt:,.2f} recorded successfully!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Failed to record transaction: {err}")

    st.write("---")
    st.subheader(f"📜 Recorded {flow_kind.capitalize()}s")
    search_cf = st.text_input(f"🔍 Search by Amount or Date (e.g., 15, 2026-09):", key="search_cf_txt", value="").strip()

    cf_df = load_cash()
    if not cf_df.empty:
        filtered_cf = cf_df[cf_df["flow_type"] == flow_kind].sort_values(by="id", ascending=False).reset_index(drop=True)
        if search_cf:
            filtered_cf = filtered_cf[
                filtered_cf["amount"].astype(str).str.contains(search_cf, na=False) |
                filtered_cf["entry_date"].astype(str).str.contains(search_cf, na=False)
            ].reset_index(drop=True)
            if filtered_cf.empty:
                st.warning("⚠️ No matching cash transactions found")

        ch1, ch2, ch3, ch4, ch5 = st.columns([0.8, 1.5, 1.5, 2, 0.8])
        ch1.markdown("**#**")
        ch2.markdown("**Date**")
        ch3.markdown("**Amount**")
        ch4.markdown("**Notes**")
        ch5.markdown("**Action**")

        for idx, item in filtered_cf.iterrows():
            item_id = item["id"]
            seq_num = idx + 1
            cc1, cc2, cc3, cc4, cc5 = st.columns([0.8, 1.5, 1.5, 2, 0.8])
            cc1.write(f"{seq_num}")
            cc2.write(f"{item['entry_date']}")
            cc3.write(f"{item['amount']:,.2f}")
            cc4.write(f"{item['notes'] or '-'}")
            with cc5:
                with st.popover("⋮"):
                    if st.button("✏️ Edit", key=f"btn_edit_cf_{item_id}", use_container_width=True):
                        st.session_state.active_editing_id = item_id
                    if st.button("🗑️ Delete", key=f"btn_del_cf_{item_id}", use_container_width=True):
                        if item["flow_type"] == "DEPOSIT" and float(item["amount"]) > free_cash:
                            st.error(f"❌ Cannot delete this deposit! Free cash would become negative ({CURRENCY} {free_cash - float(item['amount']):,.2f}).")
                        else:
                            supabase.table("cash_flows").delete().eq("id", item_id).execute()
                            st.success(f"Deleted {flow_kind.capitalize()} Record #{seq_num}")
                            st.rerun()

            if st.session_state.active_editing_id == item_id:
                with st.form(f"edit_form_cf_{item_id}"):
                    t_date = st.date_input("Date", value=pd.to_datetime(item["entry_date"]).date())
                    t_amt = st.number_input("Amount", value=float(item["amount"]), min_value=0.01)
                    t_memo = st.text_input("Notes", value=item["notes"] or "")

                    if st.form_submit_button("Save Changes", use_container_width=True):
                        live_free_cash, _ = calculate_financials()
                        new_amt = float(t_amt)
                        old_amt = float(item["amount"])

                        if flow_kind == "WITHDRAWAL" and (new_amt - old_amt) > live_free_cash:
                            st.error(f"❌ Cannot increase withdrawal! Additional amount exceeds available Free Cash ({CURRENCY} {live_free_cash:,.2f}).")
                        elif flow_kind == "DEPOSIT" and (old_amt - new_amt) > live_free_cash:
                            st.error(f"❌ Cannot decrease deposit! Free cash would drop below zero ({CURRENCY} {live_free_cash - (old_amt - new_amt):,.2f}).")
                        else:
                            payload = {
                                "entry_date": t_date.strftime("%Y-%m-%d"),
                                "amount": new_amt,
                                "notes": t_memo
                            }
                            supabase.table("cash_flows").update(payload).eq("id", item_id).execute()
                            st.session_state.active_editing_id = None
                            st.success(f"✅ {flow_kind.capitalize()} updated!")
                            st.rerun()
    else:
        st.info(f"No {flow_kind.lower()} transactions recorded yet.")

# ------------------------------------------------------------------------------
# 11. REPORTING PAGES
# ------------------------------------------------------------------------------

# WEEKLY SUMMARY
elif st.session_state.current_page == "WEEKLY":
    st.header("📅 Weekly Summary (Monday – Friday)")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        w_sym = st.text_input("🔍 Search Stock Symbol by Prefix:", value="").strip().upper()
        if w_sym:
            sells_df = sells_df[sells_df["symbol"].str.startswith(w_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            sells_df["Mon_Start"] = sells_df["sale_dt"].apply(lambda d: d - pd.Timedelta(days=d.weekday()))
            sells_df["Fri_End"] = sells_df["Mon_Start"].apply(lambda d: d + pd.Timedelta(days=4))
            sells_df["Week_Label"] = sells_df.apply(lambda r: f"Week: {r['Mon_Start'].strftime('%d %b %Y')} to {r['Fri_End'].strftime('%d %b %Y')}", axis=1)

            weeks = sells_df.sort_values(by="Mon_Start", ascending=False)["Week_Label"].unique()
            chosen_w = st.selectbox("Select Week Period (Latest first):", ["All Weeks"] + list(weeks))
            target = sells_df if chosen_w == "All Weeks" else sells_df[sells_df["Week_Label"] == chosen_w]
            target = target.sort_values(by="id", ascending=False).reset_index(drop=True)

            tot_wk_gross = target["gross_pnl"].sum()
            tot_wk_tax = target["cgt_tax"].sum()
            tot_wk_net = target["net_pnl"].sum()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Gross P&L", f"{CURRENCY} {tot_wk_gross:,.2f}")
            kpi2.metric("CGT Deducted", f"{CURRENCY} {tot_wk_tax:,.2f}")
            kpi3.metric("Net Realized Gain/Loss", f"{CURRENCY} {tot_wk_net:,.2f}")

            st.write("---")

            report_df = pd.DataFrame()
            report_df["#"] = range(1, len(target) + 1)
            report_df["Symbol"] = target["symbol"]
            report_df["Stock Name"] = target["stock_name"]
            report_df["Shares"] = target["shares_sold"].apply(lambda v: f"{v:,.2f}")
            report_df["Buy (Date @ Price)"] = target.apply(lambda r: f"{r['buy_date']} @ {r['buy_price']:,.2f}", axis=1)
            report_df["Sell (Date @ Price)"] = target.apply(lambda r: f"{r['sale_date']} @ {r['sale_price']:,.2f}", axis=1)
            report_df[f"Net Result ({CURRENCY})"] = target["net_pnl"].apply(lambda v: f"{'🟢' if v >= 0 else '🔴'} {v:,.2f}")

            st.dataframe(report_df, use_container_width=True, hide_index=True)

# MONTHLY SUMMARY
elif st.session_state.current_page == "MONTHLY":
    st.header("🗓️ Monthly Summary (1st to Last Day)")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        m_sym = st.text_input("🔍 Search Stock Symbol by Prefix:", value="").strip().upper()
        if m_sym:
            sells_df = sells_df[sells_df["symbol"].str.startswith(m_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            sells_df["Month_Display"] = sells_df["sale_dt"].dt.strftime("%B %Y")
            months = sells_df.sort_values(by="sale_dt", ascending=False)["Month_Display"].unique()
            chosen_m = st.selectbox("Select Month (Latest on top):", ["All Months"] + list(months))
            target_m = sells_df if chosen_m == "All Months" else sells_df[sells_df["Month_Display"] == chosen_m]
            target_m = target_m.sort_values(by="id", ascending=False).reset_index(drop=True)

            m_gross = target_m["gross_pnl"].sum()
            m_tax = target_m["cgt_tax"].sum()
            m_net = target_m["net_pnl"].sum()

            mk1, mk2, mk3 = st.columns(3)
            mk1.metric("Gross P&L", f"{CURRENCY} {m_gross:,.2f}")
            mk2.metric("CGT Deducted", f"{CURRENCY} {m_tax:,.2f}")
            mk3.metric("Net Realized Gain/Loss", f"{CURRENCY} {m_net:,.2f}")

            st.write("---")

            report_df = pd.DataFrame()
            report_df["#"] = range(1, len(target_m) + 1)
            report_df["Symbol"] = target_m["symbol"]
            report_df["Stock Name"] = target_m["stock_name"]
            report_df["Shares"] = target_m["shares_sold"].apply(lambda v: f"{v:,.2f}")
            report_df["Buy (Date @ Price)"] = target_m.apply(lambda r: f"{r['buy_date']} @ {r['buy_price']:,.2f}", axis=1)
            report_df["Sell (Date @ Price)"] = target_m.apply(lambda r: f"{r['sale_date']} @ {r['sale_price']:,.2f}", axis=1)
            report_df[f"Net Result ({CURRENCY})"] = target_m["net_pnl"].apply(lambda v: f"{'🟢' if v >= 0 else '🔴'} {v:,.2f}")

            st.dataframe(report_df, use_container_width=True, hide_index=True)

# ANNUAL PERFORMANCE
elif st.session_state.current_page == "ANNUAL":
    st.header("🏆 Annual Performance (From Jan 1)")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No sales records available.")
    else:
        y_sym = st.text_input("🔍 Search Stock Symbol by Prefix:", value="").strip().upper()
        if y_sym:
            sells_df = sells_df[sells_df["symbol"].str.startswith(y_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            years = sorted(sells_df["sale_dt"].dt.year.unique(), reverse=True)
            chosen_y = st.selectbox("Select Calendar Year:", years)
            yr_df = sells_df[sells_df["sale_dt"].dt.year == chosen_y].sort_values(by="id", ascending=False).reset_index(drop=True)

            c1, c2, c3 = st.columns(3)
            c1.metric(f"Gross P&L (Jan 1 – Dec 31, {chosen_y})", f"{CURRENCY} {yr_df['gross_pnl'].sum():,.2f}")
            c2.metric("Total CGT Deducted", f"{CURRENCY} {yr_df['cgt_tax'].sum():,.2f}")
            c3.metric("Net Realized Gain/Loss", f"{CURRENCY} {yr_df['net_pnl'].sum():,.2f}")

            st.write("---")

            report_df = pd.DataFrame()
            report_df["#"] = range(1, len(yr_df) + 1)
            report_df["Symbol"] = yr_df["symbol"]
            report_df["Stock Name"] = yr_df["stock_name"]
            report_df["Shares"] = yr_df["shares_sold"].apply(lambda v: f"{v:,.2f}")
            report_df["Buy (Date @ Price)"] = yr_df.apply(lambda r: f"{r['buy_date']} @ {r['buy_price']:,.2f}", axis=1)
            report_df["Sell (Date @ Price)"] = yr_df.apply(lambda r: f"{r['sale_date']} @ {r['sale_price']:,.2f}", axis=1)
            report_df[f"Net Result ({CURRENCY})"] = yr_df["net_pnl"].apply(lambda v: f"{'🟢' if v >= 0 else '🔴'} {v:,.2f}")

            st.dataframe(report_df, use_container_width=True, hide_index=True)

# CAPITAL GAIN TAX
elif st.session_state.current_page == "CGT":
    st.header("📊 Capital Gains Tax Ledger")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No tax records logged.")
    else:
        t_sym = st.text_input("🔍 Search Stock Symbol by Prefix:", value="").strip().upper()
        if t_sym:
            sells_df = sells_df[sells_df["symbol"].str.startswith(t_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            cgt_data = sells_df.sort_values(by="id", ascending=False).reset_index(drop=True)
            cgt_df = pd.DataFrame()
            cgt_df["#"] = range(1, len(cgt_data) + 1)
            cgt_df["Stock Symbol"] = cgt_data["symbol"]
            cgt_df[f"Buy Price ({CURRENCY})"] = cgt_data["buy_price"].apply(lambda v: f"{v:,.2f}")
            cgt_df[f"Sell Price ({CURRENCY})"] = cgt_data["sale_price"].apply(lambda v: f"{v:,.2f}")
            cgt_df["Buy Date"] = cgt_data["buy_date"]
            cgt_df["Sell Date"] = cgt_data["sale_date"]
            cgt_df["% Tax Deduction"] = cgt_data["cgt_rate"].apply(lambda v: f"{v}%")
            cgt_df[f"Capital Gain Tax ({CURRENCY})"] = cgt_data["cgt_tax"].apply(lambda v: f"{v:,.2f}")
            cgt_df[f"Net P&L ({CURRENCY})"] = cgt_data["net_pnl"].apply(lambda v: f"{'🟢' if v >= 0 else '🔴'} {v:,.2f}")

            st.dataframe(cgt_df, use_container_width=True, hide_index=True)
