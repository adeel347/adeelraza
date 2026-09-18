import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, time
from supabase import create_client, Client

st.set_page_config(page_title="AlphaPortfolio Tracker", page_icon="📈", layout="wide")

# ------------------------------------------------------------------------------
# RESPONSIVE CSS & COLOR-CODED BUTTON STYLING
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    /* Metric Cards */
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

    /* Green Purchase Button */
    div[data-testid="stButton"] button:has-text("➕ Purchase Record") {
        background-color: #10b981 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 3.5rem !important;
    }
    /* Red Sell Button */
    div[data-testid="stButton"] button:has-text("➖ Sell Record") {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 3.5rem !important;
    }
    /* Blue Analytics Buttons */
    div[data-testid="stButton"] button:has-text("📅 Weekly Summary"),
    div[data-testid="stButton"] button:has-text("🗓️ Monthly Summary"),
    div[data-testid="stButton"] button:has-text("🏆 Annual Performance"),
    div[data-testid="stButton"] button:has-text("📊 Capital Gain Tax"),
    div[data-testid="stButton"] button:has-text("📥 Deposit"),
    div[data-testid="stButton"] button:has-text("📤 Withdrawal") {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 3.5rem !important;
    }
    /* Grey Edit & Setting Buttons */
    div[data-testid="stButton"] button:has-text("✏️ Edit"),
    div[data-testid="stButton"] button:has-text("🔑 Change Password") {
        background-color: #64748b !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        height: 3.5rem !important;
    }

    /* Automatic Responsive Layout: Hide Desktop-only modules on mobile (<768px) */
    @media (max-width: 768px) {
        .pc-only-module {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Unsaved changes browser prompt
components.html("""
<script>
    window.parent.addEventListener('beforeunload', (event) => {
        event.preventDefault();
        event.returnValue = '';
    });
</script>
""", height=0)

# ------------------------------------------------------------------------------
# DATABASE CONNECTION
# ------------------------------------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Failed to initialize Supabase: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# STATE MANAGEMENT
# ------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "market" not in st.session_state:
    st.session_state.market = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "MAIN_MENU"
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "LOGIN"

# ------------------------------------------------------------------------------
# AUTHENTICATION (Login, Forgot Password)
# ------------------------------------------------------------------------------
if not st.session_state.authenticated:
    _, auth_box, _ = st.columns([1, 1.3, 1])

    with auth_box:
        if st.session_state.auth_view == "LOGIN":
            st.markdown("<h2 style='text-align: center;'>🔐 Trader Portal Login</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                email_in = st.text_input("Email")
                pass_in = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_in, "password": pass_in})
                        if res.user:
                            st.session_state.authenticated = True
                            st.session_state.user_email = res.user.email
                            st.session_state.market = None
                            st.session_state.current_page = "MAIN_MENU"
                            st.rerun()
                    except Exception as e:
                        st.error(f"Sign in failed: {str(e)}")

            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.auth_view = "FORGOT"
                st.rerun()

        elif st.session_state.auth_view == "FORGOT":
            st.markdown("<h2 style='text-align: center;'>🔑 Reset Password</h2>", unsafe_allow_html=True)
            st.write("Enter your registered email address to receive password reset instructions.")
            with st.form("forgot_form"):
                reset_email = st.text_input("Email Address")
                reset_submit = st.form_submit_button("Send Password Reset Email", use_container_width=True)
                if reset_submit:
                    try:
                        supabase.auth.reset_password_for_email(reset_email)
                        st.success("Recovery instructions sent to your email address.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_view = "LOGIN"
                st.rerun()

    st.stop()

# ------------------------------------------------------------------------------
# PERSISTENT HEADER (Home & Logout at All Pages)
# ------------------------------------------------------------------------------
h_col1, h_col2, h_col3 = st.columns([2, 5, 2])
with h_col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.market = None
        st.session_state.current_page = "MAIN_MENU"
        st.rerun()

with h_col2:
    badge = "🇵🇰 Pakistani Stocks" if st.session_state.market == "PK" else ("🌐 International Stocks" if st.session_state.market == "INTL" else "Market Selection")
    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:18px; margin-top:8px;'>{badge}</div>", unsafe_allow_html=True)

with h_col3:
    if st.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.market = None
        st.session_state.current_page = "MAIN_MENU"
        st.rerun()

st.divider()

# ------------------------------------------------------------------------------
# LEVEL 1: MARKET SELECTION SCREEN
# ------------------------------------------------------------------------------
if st.session_state.market is None:
    st.markdown("<h2 style='text-align:center; margin-bottom: 25px;'>Select Investment Market</h2>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        st.info("### 🇵🇰 Pakistani Stocks\nTrack PSX shares, domestic cash flows, and FBR capital gain taxes.")
        if st.button("Open Pakistani Portfolio", use_container_width=True):
            st.session_state.market = "PK"
            st.session_state.current_page = "MAIN_MENU"
            st.rerun()
    with m2:
        st.success("### 🌐 International Stocks\nTrack global equities with foreign country tags, multi-currency flows, and tax rates.")
        if st.button("Open International Portfolio", use_container_width=True):
            st.session_state.market = "INTL"
            st.session_state.current_page = "MAIN_MENU"
            st.rerun()
    st.stop()

MARKET = st.session_state.market
CURRENCY = "PKR" if MARKET == "PK" else "USD"

# Safe Data Fetchers
def load_buys():
    try:
        res = supabase.table("buy_orders").select("*").eq("market", MARKET).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def load_sells():
    try:
        res = supabase.table("sell_orders").select("*").eq("market", MARKET).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def load_cash():
    try:
        res = supabase.table("cash_flows").select("*").eq("market", MARKET).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ------------------------------------------------------------------------------
# LEVEL 2: ACTION MENU HUB (Displayed When a Market is Selected)
# ------------------------------------------------------------------------------
if st.session_state.current_page == "MAIN_MENU":
    st.markdown("<h2 style='text-align:center;'>Management Actions</h2>", unsafe_allow_html=True)
    
    # 4 Primary Mobile & Desktop Buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Purchase Record", use_container_width=True):
            st.session_state.current_page = "PURCHASE"
            st.rerun()
        if st.button("📥 Deposit", use_container_width=True):
            st.session_state.current_page = "DEPOSIT"
            st.rerun()
    with c2:
        if st.button("➖ Sell Record", use_container_width=True):
            st.session_state.current_page = "SELL"
            st.rerun()
        if st.button("📤 Withdrawal", use_container_width=True):
            st.session_state.current_page = "WITHDRAWAL"
            st.rerun()

    # Reporting & PC Options
    st.markdown('<div class="pc-only-module">', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("📅 Weekly Summary", use_container_width=True):
            st.session_state.current_page = "WEEKLY"
            st.rerun()
    with r2:
        if st.button("🗓️ Monthly Summary", use_container_width=True):
            st.session_state.current_page = "MONTHLY"
            st.rerun()
    with r3:
        if st.button("🏆 Annual Performance", use_container_width=True):
            st.session_state.current_page = "ANNUAL"
            st.rerun()

    p1, p2, p3 = st.columns(3)
    with p1:
        if st.button("📊 Capital Gain Tax", use_container_width=True):
            st.session_state.current_page = "CGT"
            st.rerun()
    with p2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.current_page = "EDIT"
            st.rerun()
    with p3:
        if st.button("🔑 Change Password", use_container_width=True):
            st.session_state.current_page = "CHANGE_PW"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Active Holdings Search
    st.write("---")
    st.subheader("🔍 Holdings Explorer")
    buys_df = load_buys()
    search_sym = st.text_input("Search Stock Symbol:", "").strip().upper()
    if not buys_df.empty:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        if search_sym:
            open_lots = open_lots[open_lots["symbol"].str.contains(search_sym, na=False)]
            if open_lots.empty:
                st.warning("⚠️ Ticker not available")
        if not open_lots.empty:
            cols = ["symbol", "stock_name", "purchase_date", "shares_bought", "shares_remaining", "price_per_share", "total_cost"]
            if MARKET == "INTL":
                cols.insert(2, "country")
            st.dataframe(open_lots[cols], use_container_width=True)
        else:
            st.info("No active holdings found.")
    else:
        st.info("No purchases recorded yet.")
    st.stop()

# Back to menu action bar
b_col, _ = st.columns([2, 8])
with b_col:
    if st.button("⬅️ Back to Menu", use_container_width=True):
        st.session_state.current_page = "MAIN_MENU"
        st.rerun()

# ------------------------------------------------------------------------------
# LEVEL 3: DEDICATED PAGE VIEWS
# ------------------------------------------------------------------------------

# PAGE 1: PURCHASE RECORD
if st.session_state.current_page == "PURCHASE":
    st.header("➕ Purchase Record Entry")
    buys_df = load_buys()
    existing_symbols = buys_df["symbol"].unique().tolist() if not buys_df.empty else []

    with st.form("purchase_form"):
        st.warning("⚠️ Changes are NOT saved until you click 'Save Purchase Changes' below.")
        p_date = st.date_input("Purchase Date", value=date.today())
        country_val = "Pakistan"
        if MARKET == "INTL":
            country_val = st.text_input("Country", value="United States").strip()

        sym = st.text_input("Stock Symbol (e.g., SYS, OGDC, AAPL)").strip().upper()
        s_name = st.text_input("Stock Name (e.g., Systems Limited, Apple Inc.)").strip()

        if sym and sym in existing_symbols:
            st.info(f"ℹ️ {sym} exists in your holdings. This entry will create a new tracking lot and expand your position.")

        col1, col2 = st.columns(2)
        with col1:
            shares = st.number_input("Number of Shares", min_value=0.0001, step=1.0, format="%.4f")
            price = st.number_input(f"Purchase Price per Share ({CURRENCY})", min_value=0.01, step=0.5, format="%.2f")
        with col2:
            fees = st.number_input(f"Brokerage Commission ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")
            taxes = st.number_input(f"Levies / Taxes ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")

        save_p = st.form_submit_button("Save Purchase Changes")
        if save_p:
            if not sym or not s_name:
                st.error("Please enter both Stock Symbol and Stock Name.")
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
                st.success(f"✅ Purchase of {shares} shares of {sym} recorded!")

# PAGE 2: SELL RECORD
elif st.session_state.current_page == "SELL":
    st.header("➖ Sell Record Entry")
    buys_df = load_buys()
    if buys_df.empty:
        st.warning("No purchase inventory available.")
    else:
        open_lots = buys_df[buys_df["shares_remaining"] > 0].copy()
        s_sym = st.text_input("🔍 Search Stock Symbol:", "").strip().upper()
        if s_sym:
            open_lots = open_lots[open_lots["symbol"].str.contains(s_sym, na=False)]
            if open_lots.empty:
                st.warning("⚠️ Ticker not available")

        if not open_lots.empty:
            lot_options = {
                f"Lot #{r['id']} | {r['symbol']} ({r['stock_name']}) | Avail: {r['shares_remaining']} sh | Bought: {r['purchase_date']} @ {r['price_per_share']}": r
                for _, r in open_lots.iterrows()
            }
            chosen_label = st.selectbox("Select Purchased Lot to Sell From:", list(lot_options.keys()))
            lot = lot_options[chosen_label]

            with st.form("sell_form"):
                st.warning("⚠️ Changes are NOT saved until you click 'Save Sell Changes' below.")
                s_date = st.date_input("Sale Date", value=date.today())
                avail = float(lot["shares_remaining"])
                shares_to_sell = st.number_input(f"Shares to Sell (Available: {avail})", min_value=0.0001, max_value=avail, step=1.0, format="%.4f")
                sell_price = st.number_input(f"Selling Price per Share ({CURRENCY})", min_value=0.01, step=0.5, format="%.2f")
                sell_fees = st.number_input(f"Selling Fees ({CURRENCY})", min_value=0.0, step=1.0, format="%.2f")
                cgt_rate = st.number_input("Capital Gain Tax %", min_value=0.0, max_value=100.0, value=15.0, step=0.5)

                save_s = st.form_submit_button("Save Sell Changes")
                if save_s:
                    if shares_to_sell > avail:
                        st.error("❌ Sale quantity exceeds available shares!")
                    else:
                        unit_cost = float(lot["total_cost"]) / float(lot["shares_bought"])
                        cost_sold = shares_to_sell * unit_cost
                        gross_rev = shares_to_sell * sell_price
                        gross_pnl = gross_rev - cost_sold - sell_fees
                        tax = (gross_pnl * (cgt_rate / 100.0)) if gross_pnl > 0 else 0.0
                        net_pnl = gross_pnl - tax

                        sell_payload = {
                            "buy_order_id": lot["id"],
                            "market": MARKET,
                            "country": lot.get("country", "Pakistan"),
                            "sale_date": s_date.isoformat(),
                            "symbol": lot["symbol"],
                            "stock_name": lot["stock_name"],
                            "shares_sold": float(shares_to_sell),
                            "buy_price": float(lot["price_per_share"]),
                            "buy_date": lot["purchase_date"],
                            "sale_price": float(sell_price),
                            "selling_fees": float(sell_fees),
                            "gross_pnl": round(gross_pnl, 2),
                            "cgt_rate": float(cgt_rate),
                            "cgt_tax": round(tax, 2),
                            "net_pnl": round(net_pnl, 2)
                        }
                        supabase.table("sell_orders").insert(sell_payload).execute()
                        supabase.table("buy_orders").update({"shares_remaining": avail - shares_to_sell}).eq("id", lot["id"]).execute()
                        st.success(f"✅ Sale logged! Net P&L: {CURRENCY} {net_pnl:,.2f} (Remaining: {avail - shares_to_sell})")
        else:
            st.info("No available shares found for this symbol.")

# PAGE 3 & 4: DEPOSIT & WITHDRAWAL
elif st.session_state.current_page in ["DEPOSIT", "WITHDRAWAL"]:
    flow_kind = st.session_state.current_page
    st.header(f"{'📥 Cash Deposit' if flow_kind == 'DEPOSIT' else '📤 Cash Withdrawal'}")

    with st.form("cash_flow_form"):
        st.warning("⚠️ Changes are NOT saved until you click 'Save Transaction' below.")
        e_date = st.date_input("Transaction Date", value=date.today())
        e_time = st.time_input("Transaction Time", value=time(12, 0))
        c_country = "Pakistan"
        if MARKET == "INTL":
            c_country = st.text_input("Origin/Destination Country", value="United States")
        amt = st.number_input(f"Amount ({CURRENCY})", min_value=0.01, step=100.0, format="%.2f")
        memo = st.text_input("Notes (Bank reference, wallet ID, etc.)")

        save_c = st.form_submit_button("Save Transaction")
        if save_c:
            payload = {
                "market": MARKET,
                "country": c_country,
                "entry_date": e_date.isoformat(),
                "entry_time": e_time.strftime("%H:%M:%S"),
                "flow_type": flow_kind,
                "amount": float(amt),
                "notes": memo
            }
            supabase.table("cash_flows").insert(payload).execute()
            st.success(f"✅ {flow_kind} of {CURRENCY} {amt:,.2f} recorded.")

    st.write("#### Recent Transactions")
    cf_df = load_cash()
    if not cf_df.empty:
        st.dataframe(cf_df[cf_df["flow_type"] == flow_kind][["entry_date", "entry_time", "amount", "notes"]], use_container_width=True)

# PAGE 5: WEEKLY SUMMARY
elif st.session_state.current_page == "WEEKLY":
    st.header("📅 Weekly Summary (Monday – Friday)")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No closed sales records found.")
    else:
        w_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if w_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(w_sym, na=False)]
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

            for _, row in target.sort_values(by="sale_date", ascending=False).iterrows():
                emoji = "🟢 Profit" if row["net_pnl"] >= 0 else "🔴 Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Shares: {row['shares_sold']} | Bought: {row['buy_date']} @ {row['buy_price']} | Sold: {row['sale_date']} @ {row['sale_price']} | **Result:** {emoji} {CURRENCY} {row['net_pnl']:,.2f}")

# PAGE 6: MONTHLY SUMMARY
elif st.session_state.current_page == "MONTHLY":
    st.header("🗓️ Monthly Summary (1st to Last Day)")
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
            sells_df["Month_Display"] = sells_df["sale_dt"].dt.strftime("%B %Y")
            months = sells_df.sort_values(by="sale_dt", ascending=False)["Month_Display"].unique()
            chosen_m = st.selectbox("Select Month (Latest on top):", ["All Months"] + list(months))
            target_m = sells_df if chosen_m == "All Months" else sells_df[sells_df["Month_Display"] == chosen_m]

            for _, row in target_m.sort_values(by="sale_date", ascending=False).iterrows():
                icon = "💰 Profit" if row["net_pnl"] >= 0 else "🔻 Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Shares: {row['shares_sold']} | Bought: {row['buy_date']} @ {row['buy_price']} | Sold: {row['sale_date']} @ {row['sale_price']} | **Result:** {icon} {CURRENCY} {row['net_pnl']:,.2f}")

# PAGE 7: ANNUAL PERFORMANCE
elif st.session_state.current_page == "ANNUAL":
    st.header("🏆 Annual Performance (From Jan 1)")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No sales records available.")
    else:
        y_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if y_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(y_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            sells_df["sale_dt"] = pd.to_datetime(sells_df["sale_date"])
            years = sorted(sells_df["sale_dt"].dt.year.unique(), reverse=True)
            chosen_y = st.selectbox("Select Calendar Year:", years)
            yr_df = sells_df[sells_df["sale_dt"].dt.year == chosen_y]

            c1, c2, c3 = st.columns(3)
            c1.metric(f"Gross P&L (Jan 1 – Dec 31, {chosen_y})", f"{CURRENCY} {yr_df['gross_pnl'].sum():,.2f}")
            c2.metric("Total CGT Deducted", f"{CURRENCY} {yr_df['cgt_tax'].sum():,.2f}")
            c3.metric("Net Realized Gain/Loss", f"{CURRENCY} {yr_df['net_pnl'].sum():,.2f}")

            st.write("#### Closed Lots")
            for _, row in yr_df.sort_values(by="sale_date", ascending=False).iterrows():
                badge = "⭐ Profit" if row["net_pnl"] >= 0 else "❌ Loss"
                st.markdown(f"**{row['symbol']}** ({row['stock_name']}) | Shares: {row['shares_sold']} | Bought: {row['buy_date']} @ {row['buy_price']} | Sold: {row['sale_date']} @ {row['sale_price']} | **Result:** {badge} {CURRENCY} {row['net_pnl']:,.2f}")

# PAGE 8: CAPITAL GAIN TAX
elif st.session_state.current_page == "CGT":
    st.header("📊 Capital Gains Tax Ledger")
    sells_df = load_sells()
    if sells_df.empty:
        st.info("No tax records logged.")
    else:
        t_sym = st.text_input("🔍 Search Stock Symbol", "").strip().upper()
        if t_sym:
            sells_df = sells_df[sells_df["symbol"].str.contains(t_sym, na=False)]
            if sells_df.empty:
                st.warning("⚠️ Ticker not available")

        if not sells_df.empty:
            cols = ["symbol", "buy_price", "sale_price", "buy_date", "sale_date", "cgt_rate", "cgt_tax", "net_pnl"]
            cgt_df = sells_df[cols].copy()
            cgt_df.columns = ["Stock Symbol", "Buy Price", "Sell Price", "Buy Date", "Sell Date", "% Tax Deduction", "Capital Gain Tax", "Net P&L"]
            st.dataframe(cgt_df, use_container_width=True)

# PAGE 9: EDIT RECORDS
elif st.session_state.current_page == "EDIT":
    st.header("✏️ Edit Ledger Records")
    sub_edit = st.radio("Choose Record Category:", ["Edit Purchases", "Edit Sells", "Edit Cash Flows"], horizontal=True)

    if sub_edit == "Edit Purchases":
        buys = load_buys()
        if not buys.empty:
            e_sym = st.text_input("🔍 Search Symbol", "").strip().upper()
            if e_sym:
                buys = buys[buys["symbol"].str.contains(e_sym, na=False)]
                if buys.empty:
                    st.warning("⚠️ Ticker not available")

            if not buys.empty:
                opts = {f"ID #{r['id']} | {r['symbol']} | Bought on {r['purchase_date']}": r for _, r in buys.iterrows()}
                chosen_b = st.selectbox("Select Record to Edit:", list(opts.keys()))
                item = opts[chosen_b]

                with st.form("edit_buy_form"):
                    st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                    sym_val = st.text_input("Stock Symbol", value=item["symbol"]).strip().upper()
                    name_val = st.text_input("Stock Name", value=item["stock_name"]).strip()
                    date_val = st.date_input("Purchase Date", value=pd.to_datetime(item["purchase_date"]).date())
                    sh_val = st.number_input("Shares Bought", value=float(item["shares_bought"]))
                    pr_val = st.number_input("Price per Share", value=float(item["price_per_share"]))
                    fe_val = st.number_input("Fees", value=float(item["fees"]))
                    tx_val = st.number_input("Taxes", value=float(item["taxes"]))
                    rem_val = st.number_input("Shares Remaining", value=float(item["shares_remaining"]))

                    up_b = st.form_submit_button("Save Changes")
                    if up_b:
                        new_tot = (sh_val * pr_val) + fe_val + tx_val
                        payload = {
                            "symbol": sym_val,
                            "stock_name": name_val,
                            "purchase_date": date_val.isoformat(),
                            "shares_bought": float(sh_val),
                            "price_per_share": float(pr_val),
                            "fees": float(fe_val),
                            "taxes": float(tx_val),
                            "total_cost": round(float(new_tot), 2),
                            "shares_remaining": float(rem_val)
                        }
                        supabase.table("buy_orders").update(payload).eq("id", item["id"]).execute()
                        st.success("✅ Purchase updated successfully!")
        else:
            st.info("No purchase records found.")

    elif sub_edit == "Edit Sells":
        sells = load_sells()
        if not sells.empty:
            s_filter = st.text_input("🔍 Search Symbol", "").strip().upper()
            if s_filter:
                sells = sells[sells["symbol"].str.contains(s_filter, na=False)]
                if sells.empty:
                    st.warning("⚠️ Ticker not available")

            if not sells.empty:
                opts_s = {f"ID #{r['id']} | {r['symbol']} | Sold on {r['sale_date']}": r for _, r in sells.iterrows()}
                chosen_s = st.selectbox("Select Sale to Edit:", list(opts_s.keys()))
                s_item = opts_s[chosen_s]

                with st.form("edit_sell_form"):
                    st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                    ss_sym = st.text_input("Stock Symbol", value=s_item["symbol"]).strip().upper()
                    ss_name = st.text_input("Stock Name", value=s_item["stock_name"]).strip()
                    ss_date = st.date_input("Sale Date", value=pd.to_datetime(s_item["sale_date"]).date())
                    ss_sh = st.number_input("Shares Sold", value=float(s_item["shares_sold"]))
                    ss_sp = st.number_input("Sale Price", value=float(s_item["sale_price"]))
                    ss_bp = st.number_input("Buy Price Basis", value=float(s_item["buy_price"]))
                    ss_fe = st.number_input("Selling Fees", value=float(s_item["selling_fees"]))
                    ss_rt = st.number_input("CGT Rate %", value=float(s_item["cgt_rate"]))

                    up_s = st.form_submit_button("Save Changes")
                    if up_s:
                        gross = (ss_sh * ss_sp) - (ss_sh * ss_bp) - ss_fe
                        cgt = (gross * (ss_rt / 100.0)) if gross > 0 else 0.0
                        net = gross - cgt
                        payload = {
                            "symbol": ss_sym,
                            "stock_name": ss_name,
                            "sale_date": ss_date.isoformat(),
                            "shares_sold": float(ss_sh),
                            "sale_price": float(ss_sp),
                            "buy_price": float(ss_bp),
                            "selling_fees": float(ss_fe),
                            "gross_pnl": round(float(gross), 2),
                            "cgt_rate": float(ss_rt),
                            "cgt_tax": round(float(cgt), 2),
                            "net_pnl": round(float(net), 2)
                        }
                        supabase.table("sell_orders").update(payload).eq("id", s_item["id"]).execute()
                        st.success("✅ Sell record updated successfully!")
        else:
            st.info("No sell records found.")

    elif sub_edit == "Edit Cash Flows":
        cfs = load_cash()
        if not cfs.empty:
            opts_c = {f"ID #{r['id']} | {r['flow_type']} {r['amount']} on {r['entry_date']}": r for _, r in cfs.iterrows()}
            chosen_c = st.selectbox("Select Cash Flow:", list(opts_c.keys()))
            c_item = opts_c[chosen_c]

            with st.form("edit_cash_form"):
                st.warning("⚠️ Changes are NOT saved until you click 'Save Changes' below.")
                t_kind = st.selectbox("Type", ["DEPOSIT", "WITHDRAWAL"], index=0 if c_item["flow_type"] == "DEPOSIT" else 1)
                t_date = st.date_input("Date", value=pd.to_datetime(c_item["entry_date"]).date())
                t_amt = st.number_input("Amount", value=float(c_item["amount"]))
                t_memo = st.text_input("Notes", value=c_item["notes"] or "")

                up_c = st.form_submit_button("Save Changes")
                if up_c:
                    payload = {
                        "flow_type": t_kind,
                        "entry_date": t_date.isoformat(),
                        "amount": float(t_amt),
                        "notes": t_memo
                    }
                    supabase.table("cash_flows").update(payload).eq("id", c_item["id"]).execute()
                    st.success("✅ Cash flow record updated successfully!")
        else:
            st.info("No cash flow entries found.")

# PAGE 10: CHANGE PASSWORD
elif st.session_state.current_page == "CHANGE_PW":
    st.header("🔑 Change Password")
    with st.form("change_password_form"):
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        update_btn = st.form_submit_button("Update Password")

        if update_btn:
            if not new_pw or len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                try:
                    supabase.auth.update_user({"password": new_pw})
                    st.success("✅ Password successfully changed!")
                except Exception as e:
                    st.error(f"Failed to update password: {str(e)}")
