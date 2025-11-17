"""
Insights service for analyzing child learning patterns.

This service processes messages to extract topics, learning behavior,
and generates insights for the parent dashboard.
"""
import re
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models import (
    Child,
    ChatSession,
    Message,
    MessageInsight,
    ChildTopicSummary,
    ChildWeeklyInsights,
    MessageRole,
)
from app.schemas.insights import (
    TopicInsight,
    LearningMetrics,
    WeeklyHighlight,
    ChildInsightsDashboard,
)


# Common topics for classification
TOPIC_KEYWORDS = {
    "Marine biology": ["ocean", "sea", "fish", "whale", "shark", "dolphin", "coral", "marine", "underwater", "octopus", "jellyfish", "seaweed"],
    "Space exploration": ["space", "planet", "star", "moon", "rocket", "astronaut", "galaxy", "universe", "mars", "jupiter", "saturn", "nasa"],
    "Dinosaurs": ["dinosaur", "t-rex", "fossil", "prehistoric", "jurassic", "cretaceous", "raptor", "triceratops", "brontosaurus"],
    "Animals": ["animal", "dog", "cat", "bird", "lion", "tiger", "elephant", "zoo", "pet", "mammal", "reptile"],
    "Science experiments": ["experiment", "chemical", "reaction", "lab", "hypothesis", "scientific", "test", "observe"],
    "Mathematics": ["math", "number", "equation", "multiply", "divide", "add", "subtract", "fraction", "geometry", "algebra"],
    "Creative writing": ["story", "write", "poem", "character", "plot", "narrative", "fiction", "author", "book"],
    "History": ["history", "ancient", "war", "civilization", "empire", "historical", "century", "medieval"],
    "Geography": ["country", "continent", "map", "mountain", "river", "climate", "geography", "capital", "population"],
    "Technology": ["computer", "robot", "coding", "program", "internet", "software", "digital", "ai", "machine"],
    "Music": ["music", "song", "instrument", "melody", "rhythm", "band", "piano", "guitar", "sing"],
    "Art": ["art", "paint", "draw", "color", "artist", "sculpture", "canvas", "creative"],
    "Sports": ["sport", "game", "ball", "team", "score", "player", "soccer", "basketball", "tennis"],
    "Nature": ["tree", "flower", "forest", "plant", "nature", "garden", "leaf", "grow"],
    "Weather": ["weather", "rain", "snow", "cloud", "sun", "storm", "climate", "temperature", "wind"],
    "Chess": ["chess", "checkmate", "bishop", "knight", "rook", "pawn", "strategy", "opening"],
    "Cooking": ["cook", "recipe", "food", "bake", "ingredient", "kitchen", "meal"],
    "Language": ["language", "word", "grammar", "vocabulary", "speak", "translate", "sentence"],
}

# Patterns indicating learning questions
LEARNING_QUESTION_PATTERNS = [
    r'\bwhy\b',
    r'\bhow\b',
    r'\bwhat makes\b',
    r'\bwhat causes\b',
    r'\bexplain\b',
    r'\bunderstand\b',
    r'\bwhat happens\b',
    r'\bwhat is the reason\b',
    r'\bwhat if\b',
    r'\bcould you explain\b',
    r'\bcan you explain\b',
    r'\btell me about\b',
    r'\bteach me\b',
    r'\bhelp me understand\b',
]


def extract_topic(message_content: str) -> Optional[str]:
    """
    Extract the main topic from a message.

    Args:
        message_content: The text content of the message

    Returns:
        The identified topic or None if no clear topic found
    """
    content_lower = message_content.lower()

    # Score each topic based on keyword matches
    topic_scores: Dict[str, int] = {}

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            topic_scores[topic] = score

    if topic_scores:
        # Return the topic with highest score
        return max(topic_scores, key=topic_scores.get)

    return None


def is_learning_question(message_content: str) -> bool:
    """
    Determine if a message is a learning question (why/how).

    Args:
        message_content: The text content of the message

    Returns:
        True if the message is a learning question
    """
    content_lower = message_content.lower()

    for pattern in LEARNING_QUESTION_PATTERNS:
        if re.search(pattern, content_lower):
            return True

    return False


def estimate_engagement_time(message_content: str, response_content: str) -> int:
    """
    Estimate the time a child spent engaging with a topic in seconds.

    Based on:
    - Length of their question (thinking time)
    - Length of AI response (reading time)
    - Complexity of the topic

    Args:
        message_content: The child's message
        response_content: The AI's response

    Returns:
        Estimated engagement time in seconds
    """
    # Base time: 5 seconds per 10 words in question (thinking/typing)
    question_words = len(message_content.split())
    thinking_time = (question_words / 10) * 5

    # Reading time: 3 seconds per 10 words in response
    response_words = len(response_content.split())
    reading_time = (response_words / 10) * 3

    # Minimum 30 seconds, maximum 5 minutes per exchange
    total_time = int(thinking_time + reading_time)
    return max(30, min(300, total_time))


def process_message_for_insights(
    db: Session,
    message: Message,
    response: Optional[Message] = None
) -> None:
    """
    Process a message and create/update insights.

    Args:
        db: Database session
        message: The user message to process
        response: The AI response (optional)
    """
    # Skip if not a user message
    if message.role != MessageRole.USER:
        return

    # Skip if blocked
    if message.blocked:
        return

    # Skip if already processed
    existing = db.query(MessageInsight).filter(
        MessageInsight.message_id == message.id
    ).first()
    if existing:
        return

    # Extract insights
    topic = extract_topic(message.content)
    is_learning = is_learning_question(message.content)

    # Estimate engagement time (use response if available)
    response_content = response.content if response else ""
    engagement_time = estimate_engagement_time(message.content, response_content)

    # Create message insight
    insight = MessageInsight(
        message_id=message.id,
        topic=topic,
        is_learning_question=is_learning,
        estimated_time_seconds=engagement_time
    )
    db.add(insight)

    # Update topic summary if topic was identified
    if topic:
        update_topic_summary(db, message, topic, engagement_time)

    db.commit()


def update_topic_summary(
    db: Session,
    message: Message,
    topic: str,
    time_seconds: int
) -> None:
    """
    Update the aggregated topic summary for a child.

    Args:
        db: Database session
        message: The message
        topic: The identified topic
        time_seconds: Engagement time in seconds
    """
    # Get child_id from session
    session = db.query(ChatSession).filter(
        ChatSession.id == message.session_id
    ).first()

    if not session:
        return

    child_id = session.child_id

    # Find or create topic summary
    summary = db.query(ChildTopicSummary).filter(
        ChildTopicSummary.child_id == child_id,
        ChildTopicSummary.topic == topic
    ).first()

    if summary:
        summary.total_time_seconds += time_seconds
        summary.message_count += 1
        summary.last_accessed = datetime.utcnow()
    else:
        summary = ChildTopicSummary(
            child_id=child_id,
            topic=topic,
            total_time_seconds=time_seconds,
            message_count=1,
            last_accessed=datetime.utcnow()
        )
        db.add(summary)


def get_week_start(dt: datetime) -> date:
    """Get the Monday of the week for a given datetime."""
    return (dt - timedelta(days=dt.weekday())).date()


def get_child_insights_dashboard(
    db: Session,
    child: Child
) -> ChildInsightsDashboard:
    """
    Get the complete insights dashboard for a child.

    Args:
        db: Database session
        child: The child model

    Returns:
        Complete insights dashboard
    """
    # Get top 5 topics
    top_topics_query = db.query(ChildTopicSummary).filter(
        ChildTopicSummary.child_id == child.id
    ).order_by(desc(ChildTopicSummary.total_time_seconds)).limit(5).all()

    top_interests = [
        TopicInsight(
            topic=ts.topic,
            total_time_minutes=ts.total_time_seconds // 60,
            message_count=ts.message_count,
            last_accessed=ts.last_accessed
        )
        for ts in top_topics_query
    ]

    # Get learning metrics
    learning_metrics = calculate_learning_metrics(db, child.id)

    # Get weekly highlights
    weekly_highlights = get_weekly_highlights(db, child.id)

    # Get total sessions
    total_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.child_id == child.id
    ).scalar() or 0

    # Get total engagement time
    total_time = db.query(func.sum(ChildTopicSummary.total_time_seconds)).filter(
        ChildTopicSummary.child_id == child.id
    ).scalar() or 0

    # Get last activity
    last_message = db.query(Message.created_at).join(ChatSession).filter(
        ChatSession.child_id == child.id
    ).order_by(desc(Message.created_at)).first()

    last_activity = last_message[0] if last_message else None

    return ChildInsightsDashboard(
        child_id=child.id,
        child_name=child.name,
        top_interests=top_interests,
        learning_metrics=learning_metrics,
        weekly_highlights=weekly_highlights,
        total_sessions=total_sessions,
        total_engagement_minutes=total_time // 60,
        last_activity=last_activity
    )


def calculate_learning_metrics(db: Session, child_id: UUID) -> LearningMetrics:
    """
    Calculate learning behavior metrics for a child.

    Args:
        db: Database session
        child_id: The child's ID

    Returns:
        Learning metrics including question types and streak
    """
    # Get all insights for this child
    insights_query = db.query(MessageInsight).join(
        Message, MessageInsight.message_id == Message.id
    ).join(
        ChatSession, Message.session_id == ChatSession.id
    ).filter(
        ChatSession.child_id == child_id
    )

    total_questions = insights_query.count()
    learning_questions = insights_query.filter(
        MessageInsight.is_learning_question == True
    ).count()

    # Calculate percentage
    learning_percentage = 0.0
    if total_questions > 0:
        learning_percentage = round((learning_questions / total_questions) * 100, 1)

    # Calculate learning streak (days with activity)
    streak = calculate_learning_streak(db, child_id)

    return LearningMetrics(
        total_questions=total_questions,
        learning_questions=learning_questions,
        learning_percentage=learning_percentage,
        learning_streak_days=streak
    )


def calculate_learning_streak(db: Session, child_id: UUID) -> int:
    """
    Calculate the number of consecutive days with learning activity.

    Args:
        db: Database session
        child_id: The child's ID

    Returns:
        Number of consecutive days
    """
    # Get unique dates with activity (ordered by date descending)
    activity_dates = db.query(
        func.date(Message.created_at).label('activity_date')
    ).join(
        ChatSession, Message.session_id == ChatSession.id
    ).filter(
        ChatSession.child_id == child_id
    ).distinct().order_by(desc('activity_date')).all()

    if not activity_dates:
        return 0

    # Convert to date objects
    dates = [d[0] for d in activity_dates]

    # Check if most recent activity was today or yesterday
    today = datetime.utcnow().date()
    if dates[0] < today - timedelta(days=1):
        return 0  # Streak broken

    # Count consecutive days
    streak = 1
    for i in range(1, len(dates)):
        if dates[i-1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break

    return streak


def get_weekly_highlights(db: Session, child_id: UUID) -> Optional[WeeklyHighlight]:
    """
    Get weekly highlights for a child.

    Args:
        db: Database session
        child_id: The child's ID

    Returns:
        Weekly highlight data or None if no activity this week
    """
    # Get current week start
    current_week_start = get_week_start(datetime.utcnow())

    # Check if we have cached weekly insights
    cached = db.query(ChildWeeklyInsights).filter(
        ChildWeeklyInsights.child_id == child_id,
        ChildWeeklyInsights.week_start == current_week_start
    ).first()

    if cached:
        # Convert cached data to WeeklyHighlight
        top_interests = []
        for topic_data in cached.top_topics[:2]:  # Top 2 for highlights
            topic_summary = db.query(ChildTopicSummary).filter(
                ChildTopicSummary.child_id == child_id,
                ChildTopicSummary.topic == topic_data.get('topic')
            ).first()

            if topic_summary:
                top_interests.append(TopicInsight(
                    topic=topic_summary.topic,
                    total_time_minutes=topic_data.get('time_seconds', 0) // 60,
                    message_count=topic_summary.message_count,
                    last_accessed=topic_summary.last_accessed
                ))

        new_curiosity = cached.new_curiosities[0] if cached.new_curiosities else None
        needs_support = None
        if cached.needs_support_topics:
            needs_support = f"{cached.needs_support_topics[0].get('topic')} (asked {cached.needs_support_topics[0].get('count')}x)"

        return WeeklyHighlight(
            week_start=cached.week_start,
            top_interests=top_interests,
            academic_focus=None,  # Could be calculated from topics
            new_curiosity=new_curiosity,
            needs_support=needs_support,
            suggested_dinner_topic=cached.suggested_discussion_topic
        )

    # Generate weekly highlights on the fly
    return generate_weekly_highlights(db, child_id, current_week_start)


def generate_weekly_highlights(
    db: Session,
    child_id: UUID,
    week_start: date
) -> Optional[WeeklyHighlight]:
    """
    Generate weekly highlights for a child.

    Args:
        db: Database session
        child_id: The child's ID
        week_start: Start of the week

    Returns:
        Generated weekly highlights or None
    """
    week_end = week_start + timedelta(days=7)

    # Get messages from this week
    week_insights = db.query(MessageInsight).join(
        Message, MessageInsight.message_id == Message.id
    ).join(
        ChatSession, Message.session_id == ChatSession.id
    ).filter(
        ChatSession.child_id == child_id,
        Message.created_at >= datetime.combine(week_start, datetime.min.time()),
        Message.created_at < datetime.combine(week_end, datetime.min.time())
    ).all()

    if not week_insights:
        return None

    # Calculate topic times this week
    topic_times: Dict[str, int] = {}
    for insight in week_insights:
        if insight.topic:
            topic_times[insight.topic] = topic_times.get(insight.topic, 0) + insight.estimated_time_seconds

    # Get top topics
    sorted_topics = sorted(topic_times.items(), key=lambda x: x[1], reverse=True)
    top_interests = []

    for topic, time_seconds in sorted_topics[:2]:
        topic_summary = db.query(ChildTopicSummary).filter(
            ChildTopicSummary.child_id == child_id,
            ChildTopicSummary.topic == topic
        ).first()

        if topic_summary:
            top_interests.append(TopicInsight(
                topic=topic,
                total_time_minutes=time_seconds // 60,
                message_count=topic_summary.message_count,
                last_accessed=topic_summary.last_accessed
            ))

    # Find new curiosities (topics first accessed this week)
    new_curiosity = None
    for insight in week_insights:
        if insight.topic:
            topic_summary = db.query(ChildTopicSummary).filter(
                ChildTopicSummary.child_id == child_id,
                ChildTopicSummary.topic == insight.topic
            ).first()

            if topic_summary and topic_summary.message_count <= 3:
                # This might be a new curiosity
                new_curiosity = f"Started exploring {insight.topic.lower()}"
                break

    # Find topics needing support (asked multiple times)
    topic_counts: Dict[str, int] = {}
    for insight in week_insights:
        if insight.topic:
            topic_counts[insight.topic] = topic_counts.get(insight.topic, 0) + 1

    needs_support = None
    for topic, count in topic_counts.items():
        if count >= 4:  # Asked about same topic 4+ times
            needs_support = f"{topic} (asked {count}x)"
            break

    # Generate suggested dinner topic
    suggested_topic = None
    if sorted_topics:
        top_topic = sorted_topics[0][0]
        suggested_topic = f"Ask about their {top_topic.lower()} research!"

    return WeeklyHighlight(
        week_start=week_start,
        top_interests=top_interests,
        academic_focus=None,
        new_curiosity=new_curiosity,
        needs_support=needs_support,
        suggested_dinner_topic=suggested_topic
    )


def process_existing_messages(db: Session, child_id: UUID) -> int:
    """
    Process existing messages that don't have insights yet.

    Args:
        db: Database session
        child_id: The child's ID

    Returns:
        Number of messages processed
    """
    # Get unprocessed user messages
    unprocessed = db.query(Message).join(
        ChatSession, Message.session_id == ChatSession.id
    ).outerjoin(
        MessageInsight, Message.id == MessageInsight.message_id
    ).filter(
        ChatSession.child_id == child_id,
        Message.role == MessageRole.USER,
        Message.blocked == False,
        MessageInsight.id == None
    ).all()

    processed_count = 0

    for message in unprocessed:
        # Find the next assistant message for response context
        next_response = db.query(Message).filter(
            Message.session_id == message.session_id,
            Message.role == MessageRole.ASSISTANT,
            Message.created_at > message.created_at
        ).order_by(Message.created_at.asc()).first()

        process_message_for_insights(db, message, next_response)
        processed_count += 1

    return processed_count
