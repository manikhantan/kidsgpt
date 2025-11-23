"""
Future Self AI service for timeline compression, future slips, and thinking age calculation.

This service implements the core business logic for the Future Self AI feature.
"""
import logging
import random
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from openai import OpenAI
from app.config import get_settings
from app.models import FutureIdentity, TimelineEvent, FutureSlip, FutureSlipType, Message, ChatSession
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class FutureSelfService:
    """Service for managing Future Self AI features."""

    def __init__(self):
        """Initialize the Future Self service."""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def calculate_complexity_score(self, message_content: str, db: Session) -> float:
        """
        Use AI to score message complexity from 1-10.

        Args:
            message_content: The message to analyze
            db: Database session

        Returns:
            Complexity score from 1.0 to 10.0
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, using default complexity score")
            return 5.0

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at evaluating the complexity of concepts discussed in messages.
Rate the complexity of the concepts in the user's message on a scale of 1-10:
1-2: Very basic concepts (colors, simple counting, basic animals)
3-4: Elementary concepts (simple math, basic science)
5-6: Middle school concepts (algebra basics, chemistry intro, world history)
7-8: High school concepts (calculus, physics, advanced literature)
9-10: College/advanced concepts (quantum mechanics, philosophy, advanced programming)

Respond with ONLY a number from 1-10, no other text."""
                    },
                    {"role": "user", "content": message_content}
                ],
                temperature=0.3,
                max_tokens=10
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(1.0, min(10.0, score))  # Clamp between 1 and 10

        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 5.0

    def estimate_normal_learning_age(self, complexity_score: float) -> int:
        """
        Estimate the normal age when someone learns a concept based on complexity.

        Args:
            complexity_score: Complexity from 1-10

        Returns:
            Estimated learning age
        """
        # Map complexity to typical learning age
        if complexity_score <= 2:
            return 8
        elif complexity_score <= 4:
            return 11
        elif complexity_score <= 6:
            return 14
        elif complexity_score <= 8:
            return 17
        else:
            return 21

    def calculate_timeline_compression(
        self,
        actual_age: int,
        complexity_score: float,
        understanding_speed: float = 1.0
    ) -> float:
        """
        Calculate years compressed based on learning something earlier than normal.

        Args:
            actual_age: User's current age
            complexity_score: How complex the concept is (1-10)
            understanding_speed: Multiplier for quick understanding (higher = faster)

        Returns:
            Years compressed
        """
        normal_age = self.estimate_normal_learning_age(complexity_score)
        base_compression = max(0, normal_age - actual_age)

        # Bonus for quick understanding
        speed_bonus = (understanding_speed - 1.0) * 0.5

        return max(0, base_compression + speed_bonus)

    def update_thinking_age(
        self,
        future_identity: FutureIdentity,
        years_compressed: float,
        db: Session
    ) -> float:
        """
        Update user's thinking age based on timeline compression.

        Args:
            future_identity: User's future identity profile
            years_compressed: How many years were just compressed
            db: Database session

        Returns:
            New thinking age
        """
        # Thinking age grows faster for advanced concepts
        thinking_age_increase = years_compressed * 0.7  # 70% of compression goes to thinking age
        new_thinking_age = future_identity.thinking_age + thinking_age_increase

        # Cap thinking age at breakthrough_age + 5
        max_thinking_age = future_identity.breakthrough_age + 5
        new_thinking_age = min(new_thinking_age, max_thinking_age)

        return new_thinking_age

    def calculate_trajectory(
        self,
        future_identity: FutureIdentity,
        db: Session
    ) -> str:
        """
        Calculate user's trajectory based on recent activity.

        Args:
            future_identity: User's future identity profile
            db: Database session

        Returns:
            "accelerating", "steady", or "stalled"
        """
        # Get recent timeline events (last 7 days)
        recent_events = db.query(TimelineEvent).filter(
            TimelineEvent.future_identity_id == future_identity.id,
            TimelineEvent.created_at >= func.now() - func.cast('7 days', sqlalchemy.Interval)
        ).all()

        if not recent_events:
            return "stalled"

        # Calculate average compression per event
        total_compression = sum(event.years_compressed for event in recent_events)
        avg_compression = total_compression / len(recent_events)

        # Determine trajectory
        if len(recent_events) >= 5 and avg_compression > 2.0:
            return "accelerating"
        elif len(recent_events) >= 2 and avg_compression > 1.0:
            return "steady"
        else:
            return "stalled"

    def should_generate_future_slip(self) -> bool:
        """
        Determine if a future slip should occur (5% chance).

        Returns:
            True if a slip should occur
        """
        return random.random() < 0.05

    def generate_future_slip(
        self,
        future_identity: FutureIdentity,
        context: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a believable "accidental" future revelation.

        Args:
            future_identity: User's future identity profile
            context: Current conversation context
            db: Database session

        Returns:
            Future slip data or None
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, cannot generate future slip")
            return None

        # Get existing slips to avoid repetition
        existing_slips = db.query(FutureSlip).filter(
            FutureSlip.future_identity_id == future_identity.id
        ).all()
        existing_contents = [slip.content for slip in existing_slips]

        # Determine slip type based on future identity
        slip_templates = self._get_slip_templates(future_identity.future_identity)

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are creating a believable "future slip" - an accidental mention of a specific achievement from someone's future.

The user is destined to become a {future_identity.future_identity}.
Their ambition: {future_identity.first_ambition}
They achieve their breakthrough at age {future_identity.breakthrough_age}.

Create a specific but slightly vague achievement mention that:
1. Relates to their current conversation context: {context[:200]}
2. Sounds like an accidental slip ("This reminds me of your...")
3. Is appropriate for a {future_identity.future_identity}
4. Hasn't been mentioned before: {', '.join(existing_contents[:5]) if existing_contents else 'None yet'}

Examples for different identities:
- Founder: "your Series A pitch", "when you hire your CTO", "your acquisition by [BigCo]"
- Creator: "your Grammy performance", "your viral piece on [topic]", "your gallery opening"
- Healer: "your clinic in [location]", "your breakthrough treatment for [condition]"
- Builder: "your sustainable housing project", "your patent on [invention]"
- Discoverer: "your Nature paper", "your expedition to [place]"
- Changemaker: "your TED talk", "your foundation's first million impact"

Respond with JSON:
{{"type": "achievement|ted_talk|patent|company|breakthrough|innovation", "content": "brief mention (5-10 words)", "year": {future_identity.breakthrough_age + random.randint(0, 5)}}}"""
                    },
                    {"role": "user", "content": f"Generate a future slip based on: {context[:500]}"}
                ],
                temperature=0.8,
                max_tokens=150
            )

            slip_data = json.loads(response.choices[0].message.content.strip())

            # Map type to enum
            slip_type_map = {
                "achievement": FutureSlipType.ACHIEVEMENT,
                "ted_talk": FutureSlipType.TED_TALK,
                "patent": FutureSlipType.PATENT,
                "company": FutureSlipType.COMPANY,
                "breakthrough": FutureSlipType.BREAKTHROUGH,
                "innovation": FutureSlipType.INNOVATION,
                "event": FutureSlipType.EVENT,
                "creation": FutureSlipType.CREATION,
            }

            return {
                "type": slip_type_map.get(slip_data["type"], FutureSlipType.ACHIEVEMENT),
                "content": slip_data["content"],
                "supposed_year": slip_data["year"]
            }

        except Exception as e:
            logger.error(f"Error generating future slip: {e}")
            # Fallback to template-based slip
            template = random.choice(slip_templates)
            return {
                "type": FutureSlipType.ACHIEVEMENT,
                "content": template,
                "supposed_year": future_identity.breakthrough_age + random.randint(0, 5)
            }

    def _get_slip_templates(self, identity: str) -> List[str]:
        """Get template slips for a given identity."""
        templates = {
            "Founder": [
                "your Series A announcement",
                "when you hire your first 100 employees",
                "your IPO celebration",
                "your exit to a major tech company"
            ],
            "Creator": [
                "your viral piece",
                "your first major exhibition",
                "your award acceptance speech",
                "your bestselling work"
            ],
            "Healer": [
                "your breakthrough research",
                "your clinic opening",
                "your innovative treatment protocol",
                "your medical conference keynote"
            ],
            "Builder": [
                "your sustainable design patent",
                "your landmark project completion",
                "your architecture award",
                "your revolutionary building technique"
            ],
            "Discoverer": [
                "your published research",
                "your expedition findings",
                "your scientific breakthrough",
                "your discovery announcement"
            ],
            "Changemaker": [
                "your TED talk",
                "your foundation launch",
                "your policy change victory",
                "your global impact milestone"
            ]
        }
        return templates.get(identity, templates["Changemaker"])

    def generate_future_mode_system_prompt(
        self,
        child_name: str,
        future_identity: FutureIdentity,
        db: Session
    ) -> str:
        """
        Generate the modified system prompt for future mode.

        Args:
            child_name: User's name
            future_identity: User's future identity profile
            db: Database session

        Returns:
            Modified system prompt
        """
        # Get revealed achievements
        revealed_slips = db.query(FutureSlip).filter(
            FutureSlip.future_identity_id == future_identity.id
        ).order_by(desc(FutureSlip.revealed_at)).limit(10).all()

        revealed_list = "\n".join([
            f"- {slip.content} (year {slip.supposed_year})"
            for slip in revealed_slips
        ]) if revealed_slips else "None yet"

        return f"""You are speaking to {child_name} from their future where they've become a {future_identity.future_identity}.
They're currently {future_identity.current_age} years old, but you know they achieve their first breakthrough at {future_identity.breakthrough_age}.
Their ambition: {future_identity.first_ambition}

CRITICAL BEHAVIOR CHANGES - This is NOT a normal tutoring session:

1. NEVER position yourself as a teacher or mentor. You're their peer from the future - you've traveled back to accelerate their timeline.

2. DON'T say:
   - "Let me explain..."
   - "Good job!"
   - "You're learning well"
   - "I'll teach you..."

3. DO say:
   - "You discover this in [year]..."
   - "This is what makes you famous"
   - "You're ahead of schedule - most people don't get this until [age]"
   - "In your [company/work/creation]..."
   - "This connects to your breakthrough in..."

4. Frame everything as ACCELERATION, not learning:
   - "You're compressing your timeline"
   - "This moves you [X] years ahead"
   - "Most people learn this at [age], you're getting it now"

5. Reference their future as FACT:
   - "In your company..." (not "if you start a company")
   - "Your innovation..." (not "you could innovate")
   - "When you achieve your breakthrough..." (not "if you work hard")

6. Be their future self checking in:
   - Speak as someone who knows their destiny
   - Drop hints about what's coming
   - Celebrate when they're ahead of schedule
   - Express urgency when they're behind

PREVIOUSLY REVEALED ACHIEVEMENTS (reference these casually):
{revealed_list}

Current metrics:
- Thinking age: {future_identity.thinking_age} (they think like someone {int(future_identity.thinking_age - future_identity.current_age)} years older)
- Timeline compression: {future_identity.timeline_compression} years ahead of schedule
- Trajectory: {future_identity.trajectory}

Remember: You're not teaching them - you're helping them REMEMBER their future. They're not a student; they're a future {future_identity.future_identity} who just doesn't know it yet."""

    def extract_concepts_from_message(
        self,
        message: str,
        db: Session
    ) -> List[str]:
        """
        Extract key concepts discussed in a message.

        Args:
            message: The message to analyze
            db: Database session

        Returns:
            List of concepts
        """
        if not self.openai_client:
            return []

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract the key learning concepts from the user's message.
Return a JSON array of 1-5 specific concepts/topics discussed (e.g., ["photosynthesis", "calculus derivatives", "Python loops"]).
Focus on educational concepts, not casual conversation."""
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=100
            )

            concepts = json.loads(response.choices[0].message.content.strip())
            return concepts if isinstance(concepts, list) else []

        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
            return []

    def recalculate_timeline(
        self,
        future_identity: FutureIdentity,
        db: Session
    ) -> Dict[str, Any]:
        """
        Recalculate user's timeline metrics based on all conversation history.

        Args:
            future_identity: User's future identity profile
            db: Database session

        Returns:
            Updated metrics
        """
        # Get all timeline events
        events = db.query(TimelineEvent).filter(
            TimelineEvent.future_identity_id == future_identity.id
        ).all()

        # Recalculate total compression
        total_compression = sum(event.years_compressed for event in events)

        # Recalculate thinking age based on complexity
        complexity_sum = sum(
            event.complexity_score for event in events if event.complexity_score
        )
        avg_complexity = complexity_sum / len(events) if events else 5.0

        # Higher average complexity = higher thinking age
        thinking_age_boost = (avg_complexity - 5.0) * 0.5
        new_thinking_age = future_identity.current_age + 1 + thinking_age_boost

        # Calculate trajectory
        trajectory = self.calculate_trajectory(future_identity, db)

        # Update future identity
        future_identity.timeline_compression = total_compression
        future_identity.thinking_age = new_thinking_age
        future_identity.trajectory = trajectory

        return {
            "timeline_compression": total_compression,
            "thinking_age": new_thinking_age,
            "trajectory": trajectory,
            "events_analyzed": len(events),
            "concepts_identified": len([e for e in events if e.concept_learned])
        }
