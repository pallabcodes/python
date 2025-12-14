"""
TUI Views for Peer Learning Features.

This module provides Textual-based user interfaces for:
- Code Review System
- Live Collaboration Sessions
- Implementation Showcase Gallery
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button, Input, Label, TextArea, Select, DataTable, Static,
    Tabs, Tab, Header, Footer, ListView, ListItem, OptionList
)
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message

from peer_learning.peer_learning_service import PeerLearningService
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class PeerLearningView(Container):
    """Main container for all peer learning features."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        with Tabs():
            with Tab("Code Review", id="code-review"):
                yield CodeReviewView(self.service, self.user_id)
            with Tab("Collaboration", id="collaboration"):
                yield CollaborationView(self.service, self.user_id)
            with Tab("Showcase", id="showcase"):
                yield ShowcaseGalleryView(self.service, self.user_id)


class CodeReviewView(Vertical):
    """TUI view for the code review system."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id
        self.current_submission = None
        self.available_reviews = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="review-sidebar"):
                yield Label("Code Review", classes="title")
                yield Button("Submit Code", id="submit-code-btn", variant="primary")
                yield Button("Available Reviews", id="available-reviews-btn")
                yield Button("My Reviews", id="my-reviews-btn")
                yield Button("AI Feedback", id="ai-feedback-btn")

            with Vertical(id="review-main"):
                yield ScrollableContainer(id="review-content")

    @on(Button.Pressed, "#submit-code-btn")
    async def show_submit_form(self) -> None:
        """Show code submission form."""
        form = CodeSubmissionForm(self.service, self.user_id)
        await self.app.push_screen(form)

    @on(Button.Pressed, "#available-reviews-btn")
    async def show_available_reviews(self) -> None:
        """Show available code reviews."""
        self.available_reviews = await self.service.get_available_reviews(self.user_id, 20)

        content = self.query_one("#review-content", ScrollableContainer)
        content.remove_children()

        if not self.available_reviews:
            content.mount(Label("No reviews available at this time."))
            return

        table = DataTable()
        table.add_columns("Title", "Language", "Difficulty", "Priority", "Action")
        table.zebra_stripes = True

        for review in self.available_reviews:
            table.add_row(
                review['title'],
                review['language'],
                review['difficulty_level'],
                f"{review['priority_score']:.1f}",
                Button("Start Review", id=f"start-review-{review['submission_id']}")
            )

        content.mount(table)

    @on(Button.Pressed, "#my-reviews-btn")
    async def show_my_reviews(self) -> None:
        """Show user's reviews."""
        given_reviews = await self.service.get_user_reviews(self.user_id, 'given', 10)
        received_reviews = await self.service.get_user_reviews(self.user_id, 'received', 10)

        content = self.query_one("#review-content", ScrollableContainer)
        content.remove_children()

        with content:
            yield Label("Reviews Given", classes="subtitle")
            if given_reviews:
                given_table = DataTable()
                given_table.add_columns("Submission", "Rating", "Completed", "Status")
                given_table.zebra_stripes = True

                for review in given_reviews:
                    given_table.add_row(
                        review['submission_title'],
                        str(review['rating'] or 'Pending'),
                        review['completed_at'][:10] if review['completed_at'] else 'In Progress',
                        review['status']
                    )
                yield given_table
            else:
                yield Label("No reviews given yet.")

            yield Label("Reviews Received", classes="subtitle")
            if received_reviews:
                received_table = DataTable()
                received_table.add_columns("Submission", "Reviewer", "Rating", "Feedback")
                received_table.zebra_stripes = True

                for review in received_reviews:
                    received_table.add_row(
                        review['submission_title'],
                        f"User {review['reviewer_id']}",
                        str(review['rating'] or 'Pending'),
                        review['feedback_text'][:50] + "..." if review['feedback_text'] else 'No feedback'
                    )
                yield received_table
            else:
                yield Label("No reviews received yet.")

    @on(Button.Pressed, "#ai-feedback-btn")
    async def show_ai_feedback_form(self) -> None:
        """Show AI feedback form."""
        form = AIFeedbackForm(self.service, self.user_id)
        await self.app.push_screen(form)


class CodeSubmissionForm(Static):
    """Form for submitting code for review."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Submit Code for Review", classes="title")
            yield Input(placeholder="Title", id="title-input")
            yield TextArea(placeholder="Description", id="description-input")
            yield TextArea(placeholder="Code", id="code-input", classes="code-editor")
            yield Select(
                [("python", "Python"), ("javascript", "JavaScript"), ("java", "Java"), ("cpp", "C++")],
                id="language-select",
                prompt="Select Language"
            )
            yield Select(
                [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                id="difficulty-select",
                prompt="Select Difficulty"
            )
            yield Input(placeholder="Topics (comma-separated)", id="topics-input")
            with Horizontal():
                yield Button("Submit", id="submit-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#submit-btn")
    async def submit_code(self) -> None:
        """Submit the code for review."""
        title = self.query_one("#title-input", Input).value
        description = self.query_one("#description-input", TextArea).value
        code = self.query_one("#code-input", TextArea).value
        language = self.query_one("#language-select", Select).value
        difficulty = self.query_one("#difficulty-select", Select).value
        topics = [t.strip() for t in self.query_one("#topics-input", Input).value.split(",") if t.strip()]

        if not title or not code:
            self.notify("Title and code are required", severity="error")
            return

        try:
            result = await self.service.submit_code_for_review(self.user_id, {
                'title': title,
                'description': description,
                'code_content': code,
                'language': language,
                'difficulty_level': difficulty,
                'topics': topics
            })

            self.notify(f"Code submitted successfully! Submission ID: {result['submission_id']}", severity="success")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Submission failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_submission(self) -> None:
        """Cancel the submission."""
        self.app.pop_screen()


class AIFeedbackForm(Static):
    """Form for requesting AI feedback on code."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Get AI Feedback", classes="title")
            yield Input(placeholder="Submission ID", id="submission-id-input")
            yield Button("Generate Feedback", id="generate-btn", variant="primary")
            yield Button("Cancel", id="cancel-btn")
            yield ScrollableContainer(id="feedback-content")

    @on(Button.Pressed, "#generate-btn")
    async def generate_feedback(self) -> None:
        """Generate AI feedback."""
        submission_id_str = self.query_one("#submission-id-input", Input).value

        try:
            submission_id = int(submission_id_str)
        except ValueError:
            self.notify("Invalid submission ID", severity="error")
            return

        try:
            feedback = await self.service.generate_ai_feedback(submission_id)

            content = self.query_one("#feedback-content", ScrollableContainer)
            content.remove_children()

            if feedback.get('ai_generated'):
                with content:
                    yield Label(f"Rating: {feedback['feedback']['overall_rating']}/5")
                    yield Label("AI Feedback:")
                    yield TextArea(
                        f"Summary: {feedback['feedback']['feedback_summary']}\n\n"
                        f"Strengths: {', '.join(feedback['feedback']['strengths'])}\n\n"
                        f"Issues: {', '.join(feedback['feedback']['issues'])}\n\n"
                        f"Suggestions: {', '.join(feedback['feedback']['suggestions'])}",
                        read_only=True
                    )
            else:
                content.mount(Label("AI feedback temporarily unavailable"))

        except Exception as e:
            self.notify(f"Failed to generate feedback: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_feedback(self) -> None:
        """Cancel feedback request."""
        self.app.pop_screen()


class CollaborationView(Vertical):
    """TUI view for live collaboration sessions."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id
        self.active_sessions = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="collab-sidebar"):
                yield Label("Live Collaboration", classes="title")
                yield Button("Create Session", id="create-session-btn", variant="primary")
                yield Button("Join Session", id="join-session-btn")
                yield Button("Active Sessions", id="active-sessions-btn")
                yield Button("My Sessions", id="my-sessions-btn")

            with Vertical(id="collab-main"):
                yield ScrollableContainer(id="collab-content")

    @on(Button.Pressed, "#create-session-btn")
    async def show_create_form(self) -> None:
        """Show session creation form."""
        form = CreateSessionForm(self.service, self.user_id)
        await self.app.push_screen(form)

    @on(Button.Pressed, "#join-session-btn")
    async def show_join_form(self) -> None:
        """Show join session form."""
        form = JoinSessionForm(self.service, self.user_id)
        await self.app.push_screen(form)

    @on(Button.Pressed, "#active-sessions-btn")
    async def show_active_sessions(self) -> None:
        """Show active collaboration sessions."""
        self.active_sessions = await self.service.get_active_sessions()

        content = self.query_one("#collab-content", ScrollableContainer)
        content.remove_children()

        if not self.active_sessions:
            content.mount(Label("No active sessions at this time."))
            return

        for session in self.active_sessions:
            session_card = SessionCard(session, self.service, self.user_id)
            content.mount(session_card)

    @on(Button.Pressed, "#my-sessions-btn")
    async def show_my_sessions(self) -> None:
        """Show user's collaboration sessions."""
        sessions = await self.service.get_user_sessions(self.user_id, True)

        content = self.query_one("#collab-content", ScrollableContainer)
        content.remove_children()

        if not sessions:
            content.mount(Label("No collaboration sessions found."))
            return

        table = DataTable()
        table.add_columns("Title", "Role", "Status", "Started", "Duration")
        table.zebra_stripes = True

        for session in sessions:
            duration = "N/A"
            if session.get('left_at') and session.get('joined_at'):
                try:
                    left = datetime.fromisoformat(session['left_at'])
                    joined = datetime.fromisoformat(session['joined_at'])
                    duration = f"{(left - joined).total_seconds() / 3600:.1f}h"
                except:
                    pass

            table.add_row(
                session['title'],
                session['role'],
                session['status'],
                session['joined_at'][:10] if session.get('joined_at') else 'Not started',
                duration
            )

        content.mount(table)


class CreateSessionForm(Static):
    """Form for creating a collaboration session."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Create Collaboration Session", classes="title")
            yield Input(placeholder="Session Title", id="title-input")
            yield TextArea(placeholder="Description", id="description-input")
            yield Select(
                [("pair_programming", "Pair Programming"), ("code_review", "Code Review"),
                 ("debugging", "Debugging"), ("learning", "Learning")],
                id="type-select",
                prompt="Session Type"
            )
            yield Input(placeholder="Max Participants (2-10)", id="max-participants-input")
            yield Input(placeholder="Topics (comma-separated)", id="topics-input")
            with Horizontal():
                yield Button("Create", id="create-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#create-btn")
    async def create_session(self) -> None:
        """Create the collaboration session."""
        title = self.query_one("#title-input", Input).value
        description = self.query_one("#description-input", TextArea).value
        session_type = self.query_one("#type-select", Select).value

        max_participants_str = self.query_one("#max-participants-input", Input).value
        try:
            max_participants = int(max_participants_str) if max_participants_str else 2
        except ValueError:
            max_participants = 2

        topics = [t.strip() for t in self.query_one("#topics-input", Input).value.split(",") if t.strip()]

        if not title:
            self.notify("Title is required", severity="error")
            return

        try:
            result = await self.service.create_collaboration_session(self.user_id, {
                'title': title,
                'description': description,
                'session_type': session_type,
                'max_participants': min(max(2, max_participants), 10),
                'topics': topics,
                'is_public': True
            })

            self.notify(f"Session created! Session ID: {result['session_id']}", severity="success")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Session creation failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_creation(self) -> None:
        """Cancel session creation."""
        self.app.pop_screen()


class JoinSessionForm(Static):
    """Form for joining a collaboration session."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Join Collaboration Session", classes="title")
            yield Input(placeholder="Session ID", id="session-id-input")
            with Horizontal():
                yield Button("Join", id="join-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#join-btn")
    async def join_session(self) -> None:
        """Join the collaboration session."""
        session_id_str = self.query_one("#session-id-input", Input).value

        try:
            session_id = int(session_id_str)
        except ValueError:
            self.notify("Invalid session ID", severity="error")
            return

        try:
            result = await self.service.join_session(self.user_id, session_id)
            self.notify(f"Joined session successfully! Participant ID: {result['participant_id']}", severity="success")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Failed to join session: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_join(self) -> None:
        """Cancel joining session."""
        self.app.pop_screen()


class SessionCard(Static):
    """Card displaying a collaboration session."""

    def __init__(self, session_data: Dict[str, Any], service: PeerLearningService, user_id: int):
        super().__init__()
        self.session_data = session_data
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        with Vertical(classes="session-card"):
            yield Label(self.session_data['title'], classes="session-title")
            yield Label(f"Host: User {self.session_data['host_user_id']}")
            yield Label(f"Type: {self.session_data['session_type'].replace('_', ' ').title()}")
            yield Label(f"Participants: {self.session_data['current_participants']}/{self.session_data['max_participants']}")
            yield Label(f"Topics: {', '.join(self.session_data['topics'])}")
            yield Button("Join Session", id="join-session-card-btn", variant="primary")


class ShowcaseGalleryView(Vertical):
    """TUI view for the implementation showcase gallery."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id
        self.current_showcases = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="showcase-sidebar"):
                yield Label("Showcase Gallery", classes="title")
                yield Button("Submit Showcase", id="submit-showcase-btn", variant="primary")
                yield Button("Browse Gallery", id="browse-gallery-btn")
                yield Button("My Showcases", id="my-showcases-btn")
                yield Button("Featured", id="featured-btn")

            with Vertical(id="showcase-main"):
                yield ScrollableContainer(id="showcase-content")

    @on(Button.Pressed, "#submit-showcase-btn")
    async def show_submit_form(self) -> None:
        """Show showcase submission form."""
        form = ShowcaseSubmissionForm(self.service, self.user_id)
        await self.app.push_screen(form)

    @on(Button.Pressed, "#browse-gallery-btn")
    async def browse_gallery(self) -> None:
        """Browse the showcase gallery."""
        self.current_showcases = await self.service.get_gallery_showcases(limit=20)

        content = self.query_one("#showcase-content", ScrollableContainer)
        content.remove_children()

        if not self.current_showcases:
            content.mount(Label("No showcases in the gallery yet."))
            return

        for showcase in self.current_showcases:
            showcase_card = ShowcaseCard(showcase, self.service, self.user_id)
            content.mount(showcase_card)

    @on(Button.Pressed, "#my-showcases-btn")
    async def show_my_showcases(self) -> None:
        """Show user's submitted showcases."""
        showcases = await self.service.get_user_showcases(self.user_id)

        content = self.query_one("#showcase-content", ScrollableContainer)
        content.remove_children()

        if not showcases:
            content.mount(Label("You haven't submitted any showcases yet."))
            return

        table = DataTable()
        table.add_columns("Title", "Status", "Upvotes", "Views", "Submitted")
        table.zebra_stripes = True

        for showcase in showcases:
            table.add_row(
                showcase['title'],
                showcase['status'],
                str(showcase['upvotes']),
                str(showcase['views']),
                showcase['submitted_at'][:10]
            )

        content.mount(table)

    @on(Button.Pressed, "#featured-btn")
    async def show_featured(self) -> None:
        """Show featured showcases."""
        featured = await self.service.get_featured_showcases(10)

        content = self.query_one("#showcase-content", ScrollableContainer)
        content.remove_children()

        if not featured:
            content.mount(Label("No featured showcases at this time."))
            return

        for showcase in featured:
            showcase_card = ShowcaseCard(showcase, self.service, self.user_id, featured=True)
            content.mount(showcase_card)


class ShowcaseSubmissionForm(Static):
    """Form for submitting an implementation to the showcase gallery."""

    def __init__(self, service: PeerLearningService, user_id: int):
        super().__init__()
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Submit to Showcase Gallery", classes="title")
            yield Input(placeholder="Title", id="title-input")
            yield TextArea(placeholder="Description", id="description-input")
            yield TextArea(placeholder="Code", id="code-input", classes="code-editor")
            yield Select(
                [("python", "Python"), ("javascript", "JavaScript"), ("java", "Java"), ("cpp", "C++")],
                id="language-select",
                prompt="Select Language"
            )
            yield Select(
                [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                id="difficulty-select",
                prompt="Select Difficulty"
            )
            yield Input(placeholder="Topics (comma-separated)", id="topics-input")
            yield TextArea(placeholder="Approach Description", id="approach-input")
            yield Input(placeholder="Key Insights (comma-separated)", id="insights-input")
            with Horizontal():
                yield Button("Submit", id="submit-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#submit-btn")
    async def submit_showcase(self) -> None:
        """Submit the showcase."""
        title = self.query_one("#title-input", Input).value
        description = self.query_one("#description-input", TextArea).value
        code = self.query_one("#code-input", TextArea).value
        language = self.query_one("#language-select", Select).value
        difficulty = self.query_one("#difficulty-select", Select).value
        topics = [t.strip() for t in self.query_one("#topics-input", Input).value.split(",") if t.strip()]
        approach = self.query_one("#approach-input", TextArea).value
        insights = [i.strip() for i in self.query_one("#insights-input", Input).value.split(",") if i.strip()]

        if not title or not code:
            self.notify("Title and code are required", severity="error")
            return

        try:
            result = await self.service.submit_showcase(self.user_id, {
                'title': title,
                'description': description,
                'code_content': code,
                'language': language,
                'difficulty_level': difficulty,
                'topics': topics,
                'approach_description': approach,
                'key_insights': insights,
                'performance_metrics': {}  # Can be added later
            })

            self.notify(f"Showcase submitted! Status: {result['status']}", severity="success")
            self.app.pop_screen()

        except Exception as e:
            self.notify(f"Submission failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#cancel-btn")
    def cancel_submission(self) -> None:
        """Cancel the submission."""
        self.app.pop_screen()


class ShowcaseCard(Static):
    """Card displaying a showcase implementation."""

    def __init__(self, showcase_data: Dict[str, Any], service: PeerLearningService,
                 user_id: int, featured: bool = False):
        super().__init__()
        self.showcase_data = showcase_data
        self.service = service
        self.user_id = user_id
        self.featured = featured

    def compose(self) -> ComposeResult:
        with Vertical(classes="showcase-card"):
            title_suffix = " ⭐" if self.featured else ""
            yield Label(f"{self.showcase_data['title']}{title_suffix}", classes="showcase-title")
            yield Label(f"By: {self.showcase_data['user_name']} ({self.showcase_data['difficulty_level'].title()})")
            yield Label(f"Language: {self.showcase_data['language']}")
            yield Label(f"Topics: {', '.join(self.showcase_data['topics'])}")
            yield Label(f"👍 {self.showcase_data['upvotes']} 👎 {self.showcase_data['downvotes']} 👁️ {self.showcase_data['views']}")
            yield Label(self.showcase_data['description'][:100] + "...")
            with Horizontal():
                yield Button("👍 Upvote", id="upvote-btn", variant="success")
                yield Button("👎 Downvote", id="downvote-btn", variant="error")
                yield Button("View Details", id="view-btn", variant="primary")

    @on(Button.Pressed, "#upvote-btn")
    async def upvote_showcase(self) -> None:
        """Upvote the showcase."""
        try:
            await self.service.vote_on_showcase(self.user_id, self.showcase_data['showcase_id'], 'upvote')
            self.notify("Upvoted!", severity="success")
        except Exception as e:
            self.notify(f"Vote failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#downvote-btn")
    async def downvote_showcase(self) -> None:
        """Downvote the showcase."""
        try:
            await self.service.vote_on_showcase(self.user_id, self.showcase_data['showcase_id'], 'downvote')
            self.notify("Downvoted!", severity="warning")
        except Exception as e:
            self.notify(f"Vote failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#view-btn")
    async def view_details(self) -> None:
        """View detailed showcase information."""
        details = ShowcaseDetailsView(self.showcase_data, self.service, self.user_id)
        await self.app.push_screen(details)


class ShowcaseDetailsView(Static):
    """Detailed view of a showcase implementation."""

    def __init__(self, showcase_data: Dict[str, Any], service: PeerLearningService, user_id: int):
        super().__init__()
        self.showcase_data = showcase_data
        self.service = service
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label(self.showcase_data['title'], classes="title")
            yield Label(f"By: {self.showcase_data['user_name']} • {self.showcase_data['submitted_at'][:10]}")
            yield Label(f"Difficulty: {self.showcase_data['difficulty_level'].title()} • Language: {self.showcase_data['language']}")

            if self.showcase_data.get('approach_description'):
                yield Label("Approach:", classes="subtitle")
                yield TextArea(self.showcase_data['approach_description'], read_only=True, classes="approach-text")

            if self.showcase_data.get('key_insights'):
                yield Label("Key Insights:", classes="subtitle")
                yield Label("• " + "\n• ".join(self.showcase_data['key_insights']))

            yield Label("Code:", classes="subtitle")
            yield TextArea(self.showcase_data['code_content'], read_only=True, classes="code-display")

            with Horizontal():
                yield Button("👍 Upvote", id="upvote-btn", variant="success")
                yield Button("👎 Downvote", id="downvote-btn", variant="error")
                yield Button("Add Comment", id="comment-btn", variant="primary")
                yield Button("Close", id="close-btn")

    @on(Button.Pressed, "#upvote-btn")
    async def upvote_showcase(self) -> None:
        """Upvote the showcase."""
        try:
            await self.service.vote_on_showcase(self.user_id, self.showcase_data['showcase_id'], 'upvote')
            self.notify("Upvoted!", severity="success")
        except Exception as e:
            self.notify(f"Vote failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#downvote-btn")
    async def downvote_showcase(self) -> None:
        """Downvote the showcase."""
        try:
            await self.service.vote_on_showcase(self.user_id, self.showcase_data['showcase_id'], 'downvote')
            self.notify("Downvoted!", severity="warning")
        except Exception as e:
            self.notify(f"Vote failed: {str(e)}", severity="error")

    @on(Button.Pressed, "#comment-btn")
    async def add_comment(self) -> None:
        """Add a comment to the showcase."""
        # Would implement comment form here
        self.notify("Comment feature coming soon!", severity="information")

    @on(Button.Pressed, "#close-btn")
    def close_details(self) -> None:
        """Close the details view."""
        self.app.pop_screen()
