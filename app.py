# ==============================================================================
# app.py - Trading Tracker Web Application
# ==============================================================================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, datetime, time
from supabase import create_client, Client

st.set_page_config(page_title="AlphaPortfolio Trader", page_icon="📈", layout="wide")

# Custom UI Styling (Color-coded buttons & cards)
st.markdown("""
<style>
    /* Card headers */
    .metric-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-title { color: #94a3b8; font-size: 13px; text-transform: uppercase; }
    .metric-val { color: #f8fafc; font-size: 22px; font-weight: bold; }
    
    /* Green Button */
    div[data-testid="stButton"] button:has-text("➕ Purchase Record") {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
    }
    /* Red Button */
    div[data-testid="stButton"] button:has-text("➖ Sell Record") {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    /* Blue Buttons */
    div[data-testid="stButton"] button:has-text("📅 Weekly Summary"),
    div[data-testid="stButton"] button:has-text("🗓️ Monthly Summary"),
    div[data-testid="stButton"] button:has-text("🏆 Annual Performance"),
    div[data-testid="stButton"] button:has-text("📊 Capital Gain Tax") {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
    }
    /* Grey Button */
    div[data-testid="stButton"] button:has-text("✏️ Edit") {
        background-color: #64748b !important;
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Inject Unsaved Changes Browser Prompt
components.html("""
<script>
    const parentWin = window.parent;
    parentWin.addEventListener('beforeunload', (event) => {
        event.preventDefault();
        event.returnValue = '';
    });
</script>
""", height=0)

# ------------------------------------------------------------------------------
# 1. DATABASE CONNECTION
# ------------------------------------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ------------------------------------------------------------------------------
# 2. AUTHENTICATION (Login / Logout)
# ------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "market" not in st.session_state:
    st.session_state.market = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.authenticated = True
            st.session_state.user_email = res.user.email
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.session_state.market = None
    st.session_state.current_page = "Dashboard"
    st.rerun()

if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<h2 style='text-align: center;'>🔐 Trader Portal Login</h2>", unsafe_allow_html=True)
        st.write("<p style='text-align:center; color:gray;'>Enter your secure trading ledger credentials</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            email_in = st.text_input("Email")
            pass_in = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                login_user(email_in, pass_in)
    st.stop()

# ------------------------------------------------------------------------------
# 3. GLOBAL TOP BAR (Persistent Home & Logout)
# ------------------------------------------------------------------------------
top_c1, top_c2, top_c3 = st.columns([2, 5, 2])
with top_c1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.market = None
        st.session_state.current_page = "Dashboard"
        st.rerun()

with top_c2:
    market_badge = "🇵🇰 Pakistani Stocks" if st.session_state.market == "PK" else ("🌐 International Stocks" if st.session_state.market == "INTL" else "Select Portfolio")
    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:17px; margin-top:5px;'>Active Mode: {market_badge}</div>", unsafe_allow_html=True)

with top_c3:
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()

st.divider()

# ------------------------------------------------------------------------------
# 4. MARKET SELECTION SCREEN (Pakistani vs International)
# ------------------------------------------------------------------------------
if st.session_state.market is None:
    st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>Choose Trading Market</h2>", unsafe_allow_html=True)
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.info("### 🇵🇰 Pakistani Stocks\nTrack PSX equities, mutual lots, local cash flows, and FBR capital gain taxes.")
        if st.button("Enter Pakistani Stocks", use_container_width=True):
            st.session_state.market = "PK"
            st.session_state.current_page = "Dashboard"
            st.rerun()
    with m_col2:
        st.success("### 🌐 International Stocks\nTrack US/Global equities, country-tagged allocations, FX cash balances, and foreign CGT.")
        if st.button("Enter International Stocks", use_container_width=True):
            st.session_state.market = "INTL"
            st.session_state.current_page = "Dashboard"
            st.rerun()
    st.stop()

MARKET = st.session_state.market
CURRENCY = "PKR" if MARKET == "PK" else "USD"

# ------------------------------------------------------------------------------
# 5. SIDEBAR NAVIGATION & PC/MOBILE VIEWPORT TOGGLE
# ------------------------------------------------------------------------------
st.sidebar.markdown(f"**Mode:** {'Pakistan (PKR)' if MARKET == 'PK' else 'International (USD)'}")
device_mode = st.sidebar.radio("📱 Layout Viewport", ["🖥️ PC Full View", "📱 Mobile View (4 Core Options)"])

if device_mode == "📱 Mobile View (4 Core Options)":
    nav_options = ["➕ Purchase Record", "➖ Sell Record", "📥 Deposit", "📤 Withdrawal"]
else:
    nav_options = [
        "📊 Dashboard",
        "➕ Purchase Record",
        "➖ Sell Record",
        "📥 Deposit",
        "📤 Withdrawal",
        "📅 Weekly Summary",
        "🗓️ Monthly Summary",
        "🏆 Annual Performance",
        "📊 Capital Gain Tax",
        "✏️ Edit"
    ]

selected_nav = st.sidebar.selectbox("Go To Option:", nav_options, index=nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0)
st.session_state.current_page = selected_nav

# Helper: Load Data for active market
def load_buys():
    res = supabase.table("buy_orders").select("*").eq("market", MARKET).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def load_sells():
    res = supabase.table("sell_orders").select("*").eq("market", MARKET).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def load_cash():
    res = supabase.table("cash_flows").select("*").eq("market", MARKET).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# ------------------------------------------------------------------------------
# OPTION 0: DASHBOARD
# ------------------------------------------------------------------------------
if st.session_state.current_page == "📊 Dashboard":
    st.subheader(f"Portfolio Overview - {'Pakistan' if MARKET == 'PK' else 'International'}")

    buys_df = load_buys()
    sells_df = load_sells()
    cash_df = load_cash()

    tot_deposits = cash_df[cash_df["flow_type"] == "DEPOSIT"]["amount"].sum() if not cash_df.empty else 0.0
    tot_withdraws = cash_df[cash_df["flow_type"] == "WITHDRAWAL"]["amount"].sum() if not cash_df.empty else 0.0
    tot_invested_open = (buys_df["shares_remaining"] * buys_df["price_per_share"]).sum() if not buys_df.empty else 0.0
    realized_pnl = sells_df["net_pnl"].sum() if not sells_df.empty else 0.0
    tot_cgt = sells_df["cgt_tax"].sum() if not sells_df.empty else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"<div class='metric-card'><div class='metric-title'>Net Cash Injected</div><div class='metric-val'>{CURRENCY} {tot_deposits - tot_withdraws:,.2f}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><div class='metric-title'>Current Open Capital</div><div class='metric-val'>{CURRENCY} {tot_invested_open:,.2f}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><div class='metric-title'>Net Realized P&L</div><div class='metric-val' style='color:{'#10b981' if realized_pnl >= 0 else '#ef4444'};'>{CURRENCY} {realized_pnl:,.2f}</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='metric-card'><div class='metric-title'>Total CGT Paid</div><div class='metric-val'>{CURRENCY} {tot_cgt:,.2f}</div></div>", unsafe_allow_html=True)

    # Search Bar for Holdings
    st.write("#### 🔍 Active Holdings Explorer")
    search_sym = st.text_input("Search Stock Symbol", "").strip().upper()
    
    if not buys_df.empty:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        if search_sym:
            open_lots = open_lots[open_lots["symbol"].str.contains(search_sym, na=False)]
            if open_lots.empty:
                st.warning("⚠️ Ticker not available")
        
        if not open_lots.empty:
            cols_show = ["symbol", "stock_name", "purchase_date", "shares_bought", "shares_remaining", "price_per_share", "total_cost"]
            if MARKET == "INTL":
                cols_show.insert(2, "country")
            st.dataframe(open_lots[cols_show], use_container_width=True)
        else:
            st.info("No open stock positions currently held.")
    else:
        st.info("No purchase transactions recorded yet.")

# ------------------------------------------------------------------------------
# OPTION 1: PURCHASE RECORD
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "➕ Purchase Record":
    st.subheader(f"➕ Add Purchase Record ({'Pakistan' if MARKET == 'PK' else 'International'})")
    
    buys_df = load_buys()
    existing_syms = buys_df["symbol"].unique().tolist() if not buys_df.empty else []

    with st.form("purchase_form"):
        p_date = st.date_input("Purchase Date", value=date.today())
        country_val = "Pakistan"
        if MARKET == "INTL":
            country_val = st.text_input("Country", value="United States").strip()

        sym = st.text_input("Stock Symbol (e.g., SYS, OGDC, AAPL, TSLA)").strip().upper()
        s_name = st.text_input("Stock Name (e.g., Systems Ltd, Apple Inc.)").strip()
        
        # Check if already in holding to notify user
        if sym and sym in existing_syms:
            st.info(f"ℹ️ {sym} exists in your records. Additional lots will add to total holding under a separate lot entry.")

        col_a, col_b = st.columns(2)
        with col_a:
            shares = st.number_input("Number of Shares", min_value=0.0001, step=1.0, format="%.4f")
            price = st.number_input(f"Purchase Price per Share ({CURRENCY})", min_value=0.01, step=0.5, format="%.2f")
        with col_b:
            fees = st.number_input(f"Brokerage / Commission ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")
            taxes = st.number_input(f"Transaction Levies / Taxes ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")

        btn_save = st.form_submit_button("Save Purchase Changes")

        if btn_save:
            if not sym or not s_name:
                st.error("Please provide both Stock Symbol and Stock Name.")
            else:
                total_val = (shares * price) + fees + taxes
                payload = {
                    "market": MARKET,
                    "country": country_val,
                    "purchase_date": p_date.isoformat(),
                    "symbol": sym,
                    "stock_name": s_name,
                    "shares_bought": float(shares),
                    "price_per_share": float(price),
                    "fees": float(fees),
                    "taxes": float(taxes),
                    "total_cost": round(float(total_val), 2),
                    "shares_remaining": float(shares)
                }
                supabase.table("buy_orders").insert(payload).execute()
                st.success(f"✅ Purchase of {shares} shares of {sym} ({s_name}) recorded successfully!")

# ------------------------------------------------------------------------------
# OPTION 2: SELL RECORD
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "➖ Sell Record":
    st.subheader(f"➖ Execute Sell Record ({'Pakistan' if MARKET == 'PK' else 'International'})")
    
    buys_df = load_buys()
    if buys_df.empty:
        st.warning("No purchase inventory recorded.")
    else:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        
        # Search Filter
        s_search = st.text_input("🔍 Filter by Stock Symbol:", "").strip().upper()
        if s_search:
            open_lots = open_lots[open_lots["symbol"].str.contains(s_search, na=False)]
            if open_lots.empty:
                st.warning("⚠️ Ticker not available")

        if not open_lots.empty:
            lot_options = {
                f"Lot #{r['id']} | {r['symbol']} ({r['stock_name']}) | Avail: {r['shares_remaining']} shares | Bought: {r['purchase_date']} @ {r['price_per_share']}": r
                for _, r in open_lots.iterrows()
            }
            selected_label = st.selectbox("Select Purchased Lot to Sell From:", list(lot_options.keys()))
            chosen_lot = lot_options[selected_label]

            with st.form("sell_execution_form"):
                s_date = st.date_input("Sale Date", value=date.today())
                avail = float(chosen_lot["shares_remaining"])
                shares_to_sell = st.number_input(f"Shares to Sell (Available: {avail})", min_value=0.0001, max_value=avail, step=1.0, format="%.4f")
                sell_price = st.number_input(f"Selling Price per Share ({CURRENCY})", min_value=0.01, step=0.5, format="%.2f")
                sell_fees = st.number_input(f"Selling Brokerage Commission ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")
                cgt_pct = st.number_input("Capital Gain Tax (CGT) Rate %", min_value=0.0, max_value=100.0, value=15.0, step=0.5)

                btn_exec = st.form_submit_button("Record Sale Changes")

                if btn_exec:
                    # Enforce available shares check
                    if shares_to_sell > avail:
                        st.error("❌ Sale quantity cannot exceed available stock shares!")
                    else:
                        unit_cost = float(chosen_lot["total_cost"]) / float(chosen_lot["shares_bought"])
                        cost_sold = shares_to_sell * unit_cost
                        gross_rev = shares_to_sell * sell_price
                        gross_pnl = gross_rev - cost_sold - sell_fees
                        tax = (gross_pnl * (cgt_pct / 100.0)) if gross_pnl > 0 else 0.0
                        net_pnl = gross_pnl - tax

                        sell_payload = {
                            "buy_order_id": chosen_lot["id"],
                            "market": MARKET,
                            "country": chosen_lot.get("country", "Pakistan"),
                            "sale_date": s_date.isoformat(),
                            "symbol": chosen_lot["symbol"],
                            "stock_name": chosen_lot["stock_name"],
                            "shares_sold": float(shares_to_sell),
                            "buy_price": float(chosen_lot["price_per_share"]),
                            "buy_date": chosen_lot["purchase_date"],
                            "sale_price": float(sell_price),
                            "selling_fees": float(sell_fees),
                            "gross_pnl": round(gross_pnl, 2),
                            "cgt_rate": float(cgt_pct),
                            "cgt_tax": round(tax, 2),
                            "net_pnl": round(net_pnl, 2)
                        }
                        supabase.table("sell_orders").insert(sell_payload).execute()

                        # Update open lot remaining shares
                        new_rem = avail - shares_to_sell
                        supabase.table("buy_orders").update({"shares_remaining": new_rem}).eq("id", chosen_lot["id"]).execute()
                        st.success(f"✅ Sold {shares_to_sell} shares. Realized Net P&L: {CURRENCY} {net_pnl:,.2f} | Remaining in lot: {new_rem}")
        else:
            st.info("No shares available to sell for this criteria.")

# ------------------------------------------------------------------------------
# OPTION 3 & 4: CASH DEPOSITS & WITHDRAWALS
# ------------------------------------------------------------------------------
elif st.session_state.current_page in ["📥 Deposit", "📤 Withdrawal"]:
    flow_kind = "DEPOSIT" if st.session_state.current_page == "📥 Deposit" else "WITHDRAWAL"
    st.subheader(f"{st.session_state.current_page} Entry ({'Pakistan' if MARKET == 'PK' else 'International'})")

    with st.form("cash_flow_form"):
        e_date = st.date_input("Transaction Date", value=date.today())
        e_time = st.time_input("Transaction Time", value=time(12, 0))
        c_country = "Pakistan"
        if MARKET == "INTL":
            c_country = st.text_input("Origin / Destination Country", value="United States")
        amt = st.number_input(f"Amount ({CURRENCY})", min_value=0.01, step=100.0, format="%.2f")
        memo = st.text_input("Notes (Bank reference, broker wallet ID, etc.)")

        btn_cash = st.form_submit_button(f"Save {flow_kind}")

        if btn_cash:
            c_payload = {
                "market": MARKET,
                "country": c_country,
                "entry_date": e_date.isoformat(),
                "entry_time": e_time.strftime("%H:%M:%S"),
                "flow_type": flow_kind,
                "amount": float(amt),
                "notes": memo
            }
            supabase.table("cash_flows").insert(c_payload).execute()
            st.success(f"✅ {flow_kind} of {CURRENCY} {amt:,.2f} recorded.")

    st.write("#### Recent Cash Logs")
    cf_df = load_cash()
    if not cf_df.empty:
        st.dataframe(cf_df[cf_df["flow_type"] == flow_kind][["entry_date", "entry_time", "amount", "notes"]], use_container_width=True)

# ------------------------------------------------------------------------------
# OPTION 5: WEEKLY SUMMARY (Monday to Friday, Latest at Top)
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "📅 Weekly Summary":
    st.subheader("📅 Weekly Realized Trading Summary")
    
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        # Search Filter
        w_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if w_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(w_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            
            # Compute Monday to Friday range
            sells_df["Mon_Start"] = sells_df["sale_dt"].apply(lambda d: d - pd.Timedelta(days=d.weekday()))
            sells_df["Fri_End"] = sells_df["Mon_Start"].apply(lambda d: d + pd.Timedelta(days=4))
            sells_df["Week_Label"] = sells_df.apply(lambda r: f"Week: {r['Mon_Start'].strftime('%d %b %Y')} (Mon) to {r['Fri_End'].strftime('%d %b %Y')} (Fri)", axis=1)

            # Sort descending (latest week first)
            unique_weeks = sells_df.sort_values(by="Mon_Start", ascending=False)["Week_Label"].unique()
            selected_week = st.selectbox("Select Week Period (Latest first):", ["All Weeks"] + list(unique_weeks))

            target_df = sells_df if selected_week == "All Weeks" else sells_df[sells_df["Week_Label"] == selected_week]
            
            st.write("### Realized Trades Breakdown")
            for _, row in target_df.sort_values(by="sale_date", ascending=False).iterrows():
                emoji = "🟢 Profit" if row["net_pnl"] >= 0 else "🔴 Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Sold: {row['shares_sold']} shares | Buy: {row['buy_date']} @ {row['buy_price']} | Sold: {row['sale_date']} @ {row['sale_price']} | **Result:** {emoji} {CURRENCY} {row['net_pnl']:,.2f}")

# ------------------------------------------------------------------------------
# OPTION 6: MONTHLY SUMMARY (1st to Last Day, Latest at Top)
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "🗓️ Monthly Summary":
    st.subheader("🗓️ Monthly Realized Summary")
    
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        m_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if m_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(m_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            sells_df["Month_Sort"] = sells_df["sale_dt"].dt.to_period("M")
            sells_df["Month_Display"] = sells_df["sale_dt"].dt.strftime("%B %Y")

            unique_months = sells_df.sort_values(by="sale_dt", ascending=False)["Month_Display"].unique()
            picked_month = st.selectbox("Select Month (Latest on top):", ["All Months"] + list(unique_months))

            active_m = sells_df if picked_month == "All Months" else sells_df[sells_df["Month_Display"] == picked_month]

            for _, row in active_m.sort_values(by="sale_date", ascending=False).iterrows():
                p_icon = "💰 Profit" if row["net_pnl"] >= 0 else "🔻 Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Shares: {row['shares_sold']} | Buy: {row['buy_date']} @ {row['buy_price']} | Sell: {row['sale_date']} @ {row['sale_price']} | Net: {p_icon} {CURRENCY} {row['net_pnl']:,.2f}")

# ------------------------------------------------------------------------------
# OPTION 7: ANNUAL PERFORMANCE (Starting Jan 1)
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "🏆 Annual Performance":
    st.subheader("🏆 Annual Financial Performance")
    
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        y_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if y_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(y_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            years = sorted(sells_df["sale_dt"].dt.year.unique(), reverse=True)
            chosen_yr = st.selectbox("Select Financial Year:", years)

            yr_df = sells_df[sells_df["sale_dt"].dt.year == chosen_yr]
            
            y_gross = yr_df["gross_pnl"].sum()
            y_tax = yr_df["cgt_tax"].sum()
            y_net = yr_df["net_pnl"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric(f"Gross P&L (from Jan 1, {chosen_yr})", f"{CURRENCY} {y_gross:,.2f}")
            c2.metric("Total CGT Deducted", f"{CURRENCY} {y_tax:,.2f}")
            c3.metric("Net Realized Return", f"{CURRENCY} {y_net:,.2f}")

            st.write("#### Stocks Closed in this Year")
            for _, row in yr_df.sort_values(by="sale_date", ascending=False).iterrows():
                badge = "⭐ Profit" if row["net_pnl"] >= 0 else "❌ Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Shares: {row['shares_sold']} | Buy: {row['buy_date']} @ {row['buy_price']} | Sell: {row['sale_date']} @ {row['sale_price']} | Net: {badge} {CURRENCY} {row['net_pnl']:,.2f}")

# ------------------------------------------------------------------------------
# OPTION 8: CAPITAL GAIN TAX (Dedicated PC Analysis View)
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "📊 Capital Gain Tax":
    st.subheader("📊 Capital Gains Tax (CGT) Ledger")
    
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No tax records generated yet.")
    else:
        cgt_search = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if cgt_search:
            sells_df = sells_df[sells_df["symbol"].str.contains(cgt_search, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            cgt_cols = ["symbol", "stock_name", "buy_date", "buy_price", "sale_date", "sale_price", "shares_sold", "cgt_rate", "cgt_tax", "net_pnl"]
            cgt_display = sells_df[cgt_cols].copy()
            cgt_display.columns = ["Symbol", "Stock Name", "Buy Date", "Buy Price", "Sale Date", "Sale Price", "Shares", "CGT Rate %", "Tax Deducted", "Net P&L"]
            st.dataframe(cgt_display, use_container_width=True)

# ------------------------------------------------------------------------------
# OPTION 9: EDIT RECORDS (Explicit "Save Changes" enforcement)
# ------------------------------------------------------------------------------
elif st.session_state.current_page == "✏️ Edit":
    st.subheader("✏️ Edit Ledger Records")
    
    edit_choice = st.radio("Choose Record Type to Edit:", ["Edit Purchases", "Edit Sells", "Edit Cash Flows"], horizontal=True)

    # 1. EDIT PURCHASES
    if edit_choice == "Edit Purchases":
        buys = load_buys()
        if buys.empty:
            st.info("No purchase records found.")
        else:
            e_sym = st.text_input("🔍 Filter by Symbol", "").strip().upper()
            if e_sym:
                buys = buys[buys["symbol"].str.contains(e_sym, na=False)]
                if buys.empty:
                    st.warning("⚠️ Ticker not available")

            if not buys.empty:
                b_opts = {f"ID #{r['id']} | {r['symbol']} | Buy Date: {r['purchase_date']}": r for _, r in buys.iterrows()}
                b_pick = st.selectbox("Select Purchase Record to Modify:", list(b_opts.keys()))
                item = b_opts[b_pick]

                with st.form("edit_buy_form"):
                    st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                    ed_sym = st.text_input("Stock Symbol", value=item["symbol"]).strip().upper()
                    ed_name = st.text_input("Stock Name", value=item["stock_name"]).strip()
                    ed_date = st.date_input("Purchase Date", value=pd.to_datetime(item["purchase_date"]).date())
                    ed_shares = st.number_input("Shares Bought", value=float(item["shares_bought"]))
                    ed_price = st.number_input("Purchase Price", value=float(item["price_per_share"]))
                    ed_fees = st.number_input("Fees", value=float(item["fees"]))
                    ed_taxes = st.number_input("Taxes", value=float(item["taxes"]))
                    ed_rem = st.number_input("Shares Remaining in Holding", value=float(item["shares_remaining"]))

                    btn_update_buy = st.form_submit_button("Save Changes")

                    if btn_update_buy:
                        new_tot = (ed_shares * ed_price) + ed_fees + ed_taxes
                        up_payload = {
                            "symbol": ed_sym,
                            "stock_name": ed_name,
                            "purchase_date": ed_date.isoformat(),
                            "shares_bought": float(ed_shares),
                            "price_per_share": float(ed_price),
                            "fees": float(ed_fees),
                            "taxes": float(ed_taxes),
                            "total_cost": round(float(new_tot), 2),
                            "shares_remaining": float(ed_rem)
                        }
                        supabase.table("buy_orders").update(up_payload).eq("id", item["id"]).execute()
                        st.success(f"✅ Purchase Record #{item['id']} successfully updated!")

    # 2. EDIT SELLS
    elif edit_choice == "Edit Sells":
        sells = load_sells()
        if sells.empty:
            st.info("No sell records found.")
        else:
            s_filter = st.text_input("🔍 Filter by Symbol", "").strip().upper()
            if s_filter:
                sells = sells[sells["symbol"].str.contains(s_filter, na=False)]
                if sells.empty:
                    st.warning("⚠️ Ticker not available")

            if not sells.empty:
                s_opts = {f"ID #{r['id']} | {r['symbol']} | Sold on {r['sale_date']}": r for _, r in sells.iterrows()}
                s_pick = st.selectbox("Select Sale Record to Modify:", list(s_opts.keys()))
                s_item = s_opts[s_pick]

                with st.form("edit_sell_form"):
                    st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                    es_sym = st.text_input("Stock Symbol", value=s_item["symbol"]).strip().upper()
                    es_name = st.text_input("Stock Name", value=s_item["stock_name"]).strip()
                    es_sdate = st.date_input("Sale Date", value=pd.to_datetime(s_item["sale_date"]).date())
                    es_sold = st.number_input("Shares Sold", value=float(s_item["shares_sold"]))
                    es_sprice = st.number_input("Sale Price", value=float(s_item["sale_price"]))
                    es_bprice = st.number_input("Buy Price Basis", value=float(s_item["buy_price"]))
                    es_fees = st.number_input("Selling Fees", value=float(s_item["selling_fees"]))
                    es_rate = st.number_input("CGT Rate %", value=float(s_item["cgt_rate"]))

                    btn_update_sell = st.form_submit_button("Save Changes")

                    if btn_update_sell:
                        gross = (es_sold * es_sprice) - (es_sold * es_bprice) - es_fees
                        cgt = (gross * (es_rate / 100.0)) if gross > 0 else 0.0
                        net = gross - cgt

                        up_sell = {
                            "symbol": es_sym,
                            "stock_name": es_name,
                            "sale_date": es_sdate.isoformat(),
                            "shares_sold": float(es_sold),
                            "sale_price": float(es_sprice),
                            "buy_price": float(es_bprice),
                            "selling_fees": float(es_fees),
                            "gross_pnl": round(float(gross), 2),
                            "cgt_rate": float(es_rate),
                            "cgt_tax": round(float(cgt), 2),
                            "net_pnl": round(float(net), 2)
                        }
                        supabase.table("sell_orders").update(up_sell).eq("id", s_item["id"]).execute()
                        st.success(f"✅ Sale Record #{s_item['id']} successfully updated!")

    # 3. EDIT CASH FLOWS
    elif edit_choice == "Edit Cash Flows":
        cfs = load_cash()
        if cfs.empty:
            st.info("No cash flow entries found.")
        else:
            cf_opts = {f"ID #{r['id']} | {r['flow_type']} of {r['amount']} on {r['entry_date']}": r for _, r in cfs.iterrows()}
            cf_pick = st.selectbox("Select Cash Flow to Modify:", list(cf_opts.keys()))
            cf_item = cf_opts[cf_pick]

            with st.form("edit_cf_form"):
                st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                ec_type = st.selectbox("Type", ["DEPOSIT", "WITHDRAWAL"], index=0 if cf_item["flow_type"] == "DEPOSIT" else 1)
                ec_date = st.date_input("Date", value=pd.to_datetime(cf_item["entry_date"]).date())
                ec_amt = st.number_input("Amount", value=float(cf_item["amount"]))
                ec_memo = st.text_input("Notes", value=cf_item["notes"] or "")

                btn_update_cf = st.form_submit_button("Save Changes")

                if btn_update_cf:
                    up_cf = {
                        "flow_type": ec_type,
                        "entry_date": ec_date.isoformat(),
                        "amount": float(ec_amt),
                        "notes": ec_memo
                    }
                    supabase.table("cash_flows").update(up_cf).eq("id", cf_item["id"]).execute()
                    st.success(f"✅ Cash Flow #{cf_item['id']} successfully updated!")
