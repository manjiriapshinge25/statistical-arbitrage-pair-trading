import streamlit as st


st.set_page_config(
    page_title="Pair Trading Dashboard",
    page_icon=":material/query_stats:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/overview.py",
            title="Overview",
            icon=":material/dashboard:",
        ),
        st.Page(
            "app_pages/pair_analysis.py",
            title="Pair analysis",
            icon=":material/query_stats:",
        ),
        st.Page(
            "app_pages/backtest.py",
            title="Backtest",
            icon=":material/assessment:",
        ),
        st.Page(
            "app_pages/forecasting.py",
            title="Forecasting",
            icon=":material/insights:",
        ),
    ],
    position="top",
)

page.run()
