import math
import random
from dataclasses import dataclass, asdict

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


# =========================
# Inventory Decision Game
# Streamlit single-file app
# =========================

TOTAL_ROUNDS = 16
MIN_DEMAND = 1
MAX_DEMAND = 100
ORDERING_COST = 2      # per ordered unit
HOLDING_COST = 5       # per ending inventory unit
SELLING_PRICE = 20     # per sold unit


@dataclass
class RoundResult:
    round_no: int
    beginning_inventory: int
    order_units: int
    available_units: int
    demand: int
    sold_units: int
    ending_inventory: int
    revenue: int
    ordering_cost: int
    holding_cost: int
    profit: int
    cumulative_profit: int


st.set_page_config(page_title="Inventory Decision Game", layout="wide")
st.title("Inventory Decision Game")
st.caption("16 rounds · demand is a random integer from 1 to 100")


# ---------- Session state initialization ----------
def init_game():
    st.session_state.started = True
    st.session_state.current_round = 1
    st.session_state.current_inventory = 0
    st.session_state.results = []
    st.session_state.demands = [random.randint(MIN_DEMAND, MAX_DEMAND) for _ in range(TOTAL_ROUNDS)]
    st.session_state.game_over = False


def reset_game():
    for key in [
        "started", "current_round", "current_inventory",
        "results", "demands", "game_over"
    ]:
        if key in st.session_state:
            del st.session_state[key]
    init_game()


if "started" not in st.session_state:
    st.session_state.started = False


# ---------- Sidebar ----------
st.sidebar.header("Game Settings")
st.sidebar.write(f"Total rounds: {TOTAL_ROUNDS}")
st.sidebar.write(f"Demand range: {MIN_DEMAND} to {MAX_DEMAND}")
st.sidebar.write(f"Selling price: ${SELLING_PRICE} / unit")
st.sidebar.write(f"Ordering cost: ${ORDERING_COST} / unit")
st.sidebar.write(f"Inventory cost: ${HOLDING_COST} / unit")

col_start1, col_start2 = st.columns([1, 1])
with col_start1:
    if not st.session_state.started:
        if st.button("Start New Game", use_container_width=True):
            init_game()
            st.rerun()
with col_start2:
    if st.session_state.started:
        if st.button("Reset Game", use_container_width=True):
            reset_game()
            st.rerun()


if not st.session_state.started:
    st.info("Press 'Start New Game' to begin.")
    st.stop()


# ---------- Helper data ----------
df = pd.DataFrame([asdict(r) for r in st.session_state.results]) if st.session_state.results else pd.DataFrame()
completed_rounds = len(st.session_state.results)


# ---------- Status summary ----------
status_col1, status_col2, status_col3, status_col4 = st.columns(4)
with status_col1:
    st.metric("Current Round", f"{st.session_state.current_round} / {TOTAL_ROUNDS}" if not st.session_state.game_over else f"{TOTAL_ROUNDS} / {TOTAL_ROUNDS}")
with status_col2:
    st.metric("Current Inventory", st.session_state.current_inventory)
with status_col3:
    total_profit = int(df["profit"].sum()) if not df.empty else 0
    st.metric("Cumulative Profit", f"${total_profit}")
with status_col4:
    total_sold = int(df["sold_units"].sum()) if not df.empty else 0
    st.metric("Total Sold Units", total_sold)


# ---------- Current round panel ----------
if not st.session_state.game_over:
    st.subheader(f"Round {st.session_state.current_round}")

    current_round_index = st.session_state.current_round - 1
    beginning_inventory = st.session_state.current_inventory

    input_col1, input_col2 = st.columns([1, 2])

    with input_col1:
        st.write("### Round Information")
        st.write(f"Beginning inventory units: **{beginning_inventory}**")
        st.write("Enter how many additional units to order.")

        order_units = st.number_input(
            "Order units",
            min_value=0,
            step=1,
            value=0,
            key=f"order_input_round_{st.session_state.current_round}"
        )

        if st.button("Submit Round", type="primary", use_container_width=True):
            demand = st.session_state.demands[current_round_index]
            available_units = beginning_inventory + int(order_units)
            sold_units = min(available_units, demand)
            ending_inventory = available_units - sold_units

            revenue = sold_units * SELLING_PRICE
            ordering_cost_total = int(order_units) * ORDERING_COST
            holding_cost_total = ending_inventory * HOLDING_COST
            profit = revenue - ordering_cost_total - holding_cost_total
            cumulative_profit = profit + (st.session_state.results[-1].cumulative_profit if st.session_state.results else 0)

            result = RoundResult(
                round_no=st.session_state.current_round,
                beginning_inventory=beginning_inventory,
                order_units=int(order_units),
                available_units=available_units,
                demand=demand,
                sold_units=sold_units,
                ending_inventory=ending_inventory,
                revenue=revenue,
                ordering_cost=ordering_cost_total,
                holding_cost=holding_cost_total,
                profit=profit,
                cumulative_profit=cumulative_profit,
            )

            st.session_state.results.append(result)
            st.session_state.current_inventory = ending_inventory

            if st.session_state.current_round >= TOTAL_ROUNDS:
                st.session_state.game_over = True
            else:
                st.session_state.current_round += 1

            st.rerun()

    with input_col2:
        st.write("### Current Progress")
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.plot(df["round_no"], df["beginning_inventory"], marker="o", label="Beginning Inventory")
            ax.plot(df["round_no"], df["ending_inventory"], marker="o", label="Ending Inventory")
            ax.plot(df["round_no"], df["sold_units"], marker="o", label="Sold Units")
            ax.set_xlabel("Round")
            ax.set_ylabel("Units")
            ax.set_xticks(range(1, completed_rounds + 1))
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("The graph will appear after the first round is submitted.")


# ---------- Round-by-round result highlight ----------
if not df.empty:
    last = df.iloc[-1]
    st.subheader("Latest Round Result")
    rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns(5)
    with rcol1:
        st.metric("Demand", int(last["demand"]))
    with rcol2:
        st.metric("Sold Units", int(last["sold_units"]))
    with rcol3:
        st.metric("Revenue", f"${int(last['revenue'])}")
    with rcol4:
        st.metric("Round Profit", f"${int(last['profit'])}")
    with rcol5:
        st.metric("Ending Inventory", int(last["ending_inventory"]))


# ---------- Final result ----------
if st.session_state.game_over:
    st.success("Game complete. All 16 rounds have been played.")

    if not df.empty:
        final_profit = int(df["profit"].sum())
        avg_profit = round(df["profit"].mean(), 2)
        total_revenue = int(df["revenue"].sum())
        total_ordering_cost = int(df["ordering_cost"].sum())
        total_holding_cost = int(df["holding_cost"].sum())
        stockout_rounds = int((df["demand"] > df["available_units"]).sum())

        f1, f2, f3, f4, f5 = st.columns(5)
        f1.metric("Final Profit", f"${final_profit}")
        f2.metric("Average Profit / Round", f"${avg_profit}")
        f3.metric("Total Revenue", f"${total_revenue}")
        f4.metric("Total Ordering Cost", f"${total_ordering_cost}")
        f5.metric("Total Holding Cost", f"${total_holding_cost}")

        st.write(f"Stockout rounds: **{stockout_rounds}**")

        fig2, ax2 = plt.subplots(figsize=(10, 4.5))
        ax2.plot(df["round_no"], df["cumulative_profit"], marker="o")
        ax2.set_xlabel("Round")
        ax2.set_ylabel("Cumulative Profit ($)")
        ax2.set_xticks(range(1, TOTAL_ROUNDS + 1))
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)


# ---------- Full table ----------
st.subheader("Game Table")

if not df.empty:
    display_df = df.copy()
    display_df.columns = [
        "Round",
        "Beginning Inventory",
        "Order Units",
        "Available Units",
        "Demand",
        "Sold Units",
        "Ending Inventory",
        "Revenue",
        "Ordering Cost",
        "Holding Cost",
        "Profit",
        "Cumulative Profit",
    ]
    st.dataframe(display_df, use_container_width=True)

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Results as CSV",
        data=csv_data,
        file_name="inventory_decision_game_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No rounds have been completed yet.")


# ---------- Formula explanation ----------
with st.expander("How profit is calculated"):
    st.markdown(
        f"""
        For each round:

        - Revenue = Sold Units × ${SELLING_PRICE}
        - Ordering Cost = Ordered Units × ${ORDERING_COST}
        - Inventory Cost = Ending Inventory × ${HOLDING_COST}
        - Profit = Revenue - Ordering Cost - Inventory Cost

        Notes:
        - Demand is randomly generated in advance for each of the 16 rounds.
        - Unsold inventory carries over to the next round.
        - Lost sales are not backordered.
        """
    )
