import streamlit as st
import pandas as pd
import plotly.express as px
from auth import init_auth
import database as db

# Configure the page
st.set_page_config(
    page_title="EcoHabit - Sustainability Tracker",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #4a5d23;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #e6f0e6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.title("🌿 EcoHabit")
st.subheader("5C Competitive Sustainability Tracker")

# Check authentication
if not init_auth():
    st.stop()

# Display user info
user = st.session_state.user
st.sidebar.markdown(f"### Welcome, {user['name']}")
st.sidebar.markdown(f"**Campus:** {user['campus']}")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Log Activities", "Leaderboard", "My Badges"])

# Get user stats for the sidebar
user_stats = db.get_user_stats(user['user_id'])
st.sidebar.markdown("---")
st.sidebar.markdown("### Your Stats")
st.sidebar.markdown(f"**Total Points:** {user_stats['total_points'] or 0}")
st.sidebar.markdown(f"**Activities Logged:** {user_stats['total_activities'] or 0}")
st.sidebar.markdown(f"**Badges Earned:** {user_stats['badges_count'] or 0}")

# Logout button in sidebar
from auth import logout_user
st.sidebar.markdown("---")
logout_user()

# Dashboard page
if page == "Dashboard":
    st.header("Your Sustainability Dashboard")
    
    # Create two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Recent activities
        st.subheader("Recent Activities")
        recent_activities = db.get_user_recent_activities(user['user_id'])
        
        if recent_activities.empty:
            st.info("You haven't logged any activities yet. Start by logging some sustainable actions!")
        else:
            for _, activity in recent_activities.iterrows():
                with st.container():
                    cols = st.columns([1, 3, 1, 1])
                    with cols[0]:
                        st.markdown(f"### {activity['icon']}")
                    with cols[1]:
                        st.markdown(f"**{activity['name']}**")
                    with cols[2]:
                        st.markdown(f"+{activity['points']} pts")
                    with cols[3]:
                        st.markdown(f"{activity['timestamp'].strftime('%b %d')}")
                    st.markdown("---")
    
    with col2:
        # Badges section
        st.subheader("Your Badges")
        badges = db.get_user_badges(user['user_id'])
        
        if badges.empty:
            st.info("You haven't earned any badges yet. Keep up the good work!")
        else:
            for _, badge in badges.iterrows():
                st.markdown(f"### {badge['icon']} {badge['name']}")
                st.caption(f"{badge['description']}")
                st.markdown("---")
        
        # Link to leaderboard
        st.markdown("[View Leaderboard →](#leaderboard)")

# Activities page
elif page == "Log Activities":
    st.header("Log Sustainable Activities")
    
    # Get all activities
    activities = db.get_activities()
    
    # Create categories
    categories = activities['category'].unique()
    
    for category in categories:
        st.subheader(f"{category.capitalize()} Activities")
        category_activities = activities[activities['category'] == category]
        
        cols = st.columns(3)
        for i, (_, activity) in enumerate(category_activities.iterrows()):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"### {activity['icon']} {activity['name']}")
                    st.markdown(f"**+{activity['points']} points**")
                    if st.button(f"Log Activity", key=f"log_{activity['activity_id']}"):
                        db.log_activity(user['user_id'], activity['activity_id'])
                        st.success(f"Logged {activity['name']} (+{activity['points']} points)")
                        # Refresh the page to show updated points
                        st.rerun()
                st.markdown("---")

# Leaderboard page
elif page == "Leaderboard":
    st.header("Sustainability Leaderboard")
    
    tab1, tab3 = st.tabs(["Individual", "Campus"])
    
    with tab1:
        individual_leaders = db.get_individual_leaderboard()
        st.subheader("Top Sustainable Individuals")
        
        # Highlight the current user
        individual_leaders['highlight'] = individual_leaders['name'] == user['name']
        
        # Create a bar chart
        fig = px.bar(
            individual_leaders,
            x='name',
            y='total_points',
            color='highlight',
            color_discrete_map={True: '#4CAF50', False: '#90EE90'},
            labels={'total_points': 'Points', 'name': 'User'},
            title="Individual Leaderboard"
        )
        st.plotly_chart(fig)
        
        # Show table
        st.dataframe(
            individual_leaders[['name', 'campus', 'total_points']],
            column_config={
                "name": "Name",
                "campus": "Campus",
                "total_points": st.column_config.NumberColumn("Points", format="%d")
            },
            hide_index=True
        )
    
    
    with tab3:
        campus_leaders = db.get_campus_leaderboard()
        st.subheader("Campus Rankings")
        
        # Highlight the user's campus
        campus_leaders['highlight'] = campus_leaders['campus'] == user['campus']
        
        # Create a bar chart
        fig = px.bar(
            campus_leaders,
            x='campus',
            y='total_points',
            color='highlight',
            color_discrete_map={True: '#4CAF50', False: '#90EE90'},
            labels={'total_points': 'Points', 'campus': 'Campus'},
            title="Campus Leaderboard"
        )
        st.plotly_chart(fig)
        
        # Show table
        st.dataframe(
            campus_leaders,
            column_config={
                "campus": "Campus",
                "total_points": st.column_config.NumberColumn("Total Points", format="%d")
            },
            hide_index=True
        )

# Badges page
elif page == "My Badges":
    st.header("My Sustainability Badges")
    
    # Get user badges
    user_badges = db.get_user_badges(user['user_id'])
    
    if user_badges.empty:
        st.info("You haven't earned any badges yet. Start logging activities to earn badges!")
    else:
        # Display badges in a grid
        cols = st.columns(3)
        for i, (_, badge) in enumerate(user_badges.iterrows()):
            with cols[i % 3]:
                st.markdown(f"## {badge['icon']}")
                st.markdown(f"### {badge['name']}")
                st.markdown(f"{badge['description']}")
                st.caption(f"Earned on: {badge['earned_date'].strftime('%b %d, %Y')}")
                st.markdown("---")
    
    # Show available badges
    st.subheader("Available Badges")
    st.markdown("Keep logging activities to earn these badges:")
    
    # Get all badges
    all_badges_query = "SELECT * FROM badges"
    all_badges = pd.read_sql(all_badges_query, db.engine)
    
    # Find badges the user doesn't have yet
    if not user_badges.empty:
        earned_badge_ids = user_badges['badge_id'].tolist()
        available_badges = all_badges[~all_badges['badge_id'].isin(earned_badge_ids)]
    else:
        available_badges = all_badges
    
    # Display available badges
    cols = st.columns(3)
    for i, (_, badge) in enumerate(available_badges.iterrows()):
        with cols[i % 3]:
            st.markdown(f"## {badge['icon']}")
            st.markdown(f"### {badge['name']}")
            st.markdown(f"{badge['description']}")
            st.caption(f"Requirement: {badge['requirement']}")
            st.markdown("---")