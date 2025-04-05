import sqlalchemy as sa
import pandas as pd
import uuid
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import streamlit as st

# Database connection string - adjust as needed
DATABASE_URL = "mysql+pymysql://username:password@localhost/ecohabit"

# Create engine and session
engine = sa.create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

# User Functions
def create_user(username, password, name, campus):
    """Create a new user."""
    user_id = str(uuid.uuid4())
    with get_session() as session:
        query = sa.text("""
            INSERT INTO users (user_id, username, password, name, campus)
            VALUES (:user_id, :username, :password, :name, :campus)
        """)
        try:
            session.execute(query, {
                'user_id': user_id,
                'username': username,
                'password': password,  # Would use hashing in production
                'name': name,
                'campus': campus
            })
            return user_id
        except sa.exc.IntegrityError:
            return None

def validate_user(username, password):
    """Validate user credentials."""
    with get_session() as session:
        query = sa.text("""
            SELECT user_id, name, campus
            FROM users
            WHERE username = :username AND password = :password
        """)
        result = session.execute(query, {'username': username, 'password': password}).fetchone()
        if result:
            return {
                'user_id': result[0],
                'name': result[1],
                'campus': result[2]
            }
        return None

# Activity Functions
def get_activities():
    """Get all available activities."""
    return pd.read_sql("SELECT * FROM activities", engine)

def log_activity(user_id, activity_id):
    """Log a user activity and update points."""
    with get_session() as session:
        # Get activity points
        points_query = sa.text("SELECT points FROM activities WHERE activity_id = :activity_id")
        points = session.execute(points_query, {'activity_id': activity_id}).scalar()
        
        # Insert activity log
        log_query = sa.text("""
            INSERT INTO user_activities (user_id, activity_id)
            VALUES (:user_id, :activity_id)
        """)
        session.execute(log_query, {'user_id': user_id, 'activity_id': activity_id})
        
        # Update user points
        update_query = sa.text("""
            UPDATE users
            SET total_points = total_points + :points
            WHERE user_id = :user_id
        """)
        session.execute(update_query, {'user_id': user_id, 'points': points})
        
        # Check for badges
        check_badges(session, user_id)

# Badge Functions
def check_badges(session, user_id):
    """Check and award badges if criteria are met."""
    # Check total activities (for badges 1 and 2)
    count_query = sa.text("""
        SELECT COUNT(*) FROM user_activities WHERE user_id = :user_id
    """)
    activity_count = session.execute(count_query, {'user_id': user_id}).scalar()
    
    if activity_count >= 1:
        award_badge_if_not_exists(session, user_id, 1)  # First Step badge
    
    if activity_count >= 10:
        award_badge_if_not_exists(session, user_id, 2)  # Eco Warrior badge
    
    # Check category-specific badges
    categories = {'water': 3, 'energy': 4, 'waste': 5}
    for category, badge_id in categories.items():
        category_query = sa.text("""
            SELECT COUNT(*) FROM user_activities ua
            JOIN activities a ON ua.activity_id = a.activity_id
            WHERE ua.user_id = :user_id AND a.category = :category
        """)
        category_count = session.execute(category_query, 
                                         {'user_id': user_id, 'category': category}).scalar()
        if category_count >= 5:
            award_badge_if_not_exists(session, user_id, badge_id)

def award_badge_if_not_exists(session, user_id, badge_id):
    """Award a badge to a user if they don't already have it."""
    check_query = sa.text("""
        SELECT COUNT(*) FROM user_badges
        WHERE user_id = :user_id AND badge_id = :badge_id
    """)
    has_badge = session.execute(check_query, 
                               {'user_id': user_id, 'badge_id': badge_id}).scalar() > 0
    
    if not has_badge:
        award_query = sa.text("""
            INSERT INTO user_badges (user_id, badge_id)
            VALUES (:user_id, :badge_id)
        """)
        session.execute(award_query, {'user_id': user_id, 'badge_id': badge_id})

def get_user_badges(user_id):
    """Get all badges earned by a user."""
    query = """
        SELECT b.badge_id, b.name, b.description, b.icon, ub.earned_date
        FROM badges b
        JOIN user_badges ub ON b.badge_id = ub.badge_id
        WHERE ub.user_id = :user_id
    """
    return pd.read_sql(query, engine, params={'user_id': user_id})

# Leaderboard Functions
def get_individual_leaderboard():
    """Get top users by points."""
    query = """
        SELECT name, campus, total_points
        FROM users
        ORDER BY total_points DESC
        LIMIT 10
    """
    return pd.read_sql(query, engine)

def get_campus_leaderboard():
    """Get top campuses by points."""
    query = """
        SELECT campus, SUM(total_points) as total_points
        FROM users
        GROUP BY campus
        ORDER BY total_points DESC
    """
    return pd.read_sql(query, engine)

def get_user_recent_activities(user_id, limit=5):
    """Get a user's recent activities."""
    query = """
        SELECT a.name, a.points, a.category, a.icon, ua.timestamp
        FROM user_activities ua
        JOIN activities a ON ua.activity_id = a.activity_id
        WHERE ua.user_id = :user_id
        ORDER BY ua.timestamp DESC
        LIMIT :limit
    """
    return pd.read_sql(query, engine, params={'user_id': user_id, 'limit': limit})

def get_user_stats(user_id):
    """Get a user's activity statistics."""
    query = """
        SELECT 
            COUNT(*) as total_activities,
            SUM(a.points) as total_points,
            (SELECT COUNT(DISTINCT badge_id) FROM user_badges WHERE user_id = :user_id) as badges_count
        FROM user_activities ua
        JOIN activities a ON ua.activity_id = a.activity_id
        WHERE ua.user_id = :user_id
    """
    return pd.read_sql(query, engine, params={'user_id': user_id}).iloc[0]