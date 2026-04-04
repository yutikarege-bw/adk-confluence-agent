"""
JIRA Ticket Output Schema
===========================
Pydantic model that mirrors an actual JIRA ticket structure.
Used as output_schema for the ticket_creator agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class JiraTicketSchema(BaseModel):
    """Structured output mimicking an actual JIRA ticket.

    Every field corresponds to a real JIRA field so users can
    copy the output directly into their JIRA instance.
    """

    project_key: str = Field(
        description="JIRA project key, e.g. 'PROJ', 'ENG', 'DATA'."
    )
    issue_type: str = Field(
        description="Ticket type: Story | Bug | Task | Epic | Sub-task."
    )
    summary: str = Field(
        description="Concise ticket title (max ~100 characters)."
    )
    description: str = Field(
        description=(
            "Full ticket description including context, background, "
            "requirements, and any technical details. Supports JIRA markdown."
        )
    )
    acceptance_criteria: list[str] = Field(
        description="List of specific, testable acceptance criteria.",
        default_factory=list,
    )
    priority: str = Field(
        description="Priority level: Blocker | Critical | Major | Minor | Trivial."
    )
    labels: list[str] = Field(
        description="Relevant labels, e.g. ['backend', 'api', 'security'].",
        default_factory=list,
    )
    components: list[str] = Field(
        description="JIRA components this ticket belongs to.",
        default_factory=list,
    )
    story_points: int | None = Field(
        default=None,
        description="Fibonacci story-point estimate: 1, 2, 3, 5, 8, 13, 21.",
    )
    sprint: str = Field(
        default="Backlog",
        description="Target sprint name, e.g. 'Sprint 42' or 'Backlog'.",
    )
    assignee: str = Field(
        default="Unassigned",
        description="Assignee username or display name.",
    )
    reporter: str = Field(
        default="Auto-generated",
        description="Reporter username or display name.",
    )
    epic_link: str | None = Field(
        default=None,
        description="Parent epic key if applicable, e.g. 'PROJ-100'.",
    )
    fix_version: str | None = Field(
        default=None,
        description="Target fix version / release, e.g. 'v2.4.0'.",
    )
    environment: str = Field(
        default="All",
        description="Affected environment: Production | Staging | Dev | All.",
    )
    due_date: str | None = Field(
        default=None,
        description="Due date in ISO format (YYYY-MM-DD) if applicable.",
    )
    attachments_note: str | None = Field(
        default=None,
        description="Note about any referenced documents or attachments.",
    )