from pydantic import BaseModel, Field
from typing import Optional

class TicketInfo(BaseModel):
    summary: str = Field(..., description="The title/summary of the JIRA ticket")
    description: str = Field(..., description="A detailed description of the issue")
    acceptance_criteria: Optional[list[str]] = Field(None, description="Testable acceptance criteria for the ticket")
    issue_type: str = Field(..., description="JIRA issue type (e.g., Bug, Task, Story)")
    priority: Optional[str] = Field(None, description="Priority level (Highest, High, Medium, Low, Lowest)")
    assignee: Optional[str] = Field(None, description="JIRA username of the assignee")
    labels: Optional[list[str]] = Field(None, description="List of labels to apply to the ticket")