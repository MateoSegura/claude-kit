"""Add session telemetry columns for full session reconstruction.

New columns on session_summaries:
- tool_uses (JSON): tool_name → invocation count
- mcp_calls (JSON): mcp_server → invocation count
- compact_count (Integer): auto-compact events
- model (String): model ID used
- cost_usd (Float): actual SDK cost
- total_turns (Integer): conversation turn count

Revision ID: 001
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_summaries",
        sa.Column("tool_uses", sa.JSON, server_default="{}"),
    )
    op.add_column(
        "session_summaries",
        sa.Column("mcp_calls", sa.JSON, server_default="{}"),
    )
    op.add_column(
        "session_summaries",
        sa.Column("compact_count", sa.Integer, server_default="0"),
    )
    op.add_column(
        "session_summaries",
        sa.Column("model", sa.String(100), nullable=True),
    )
    op.add_column(
        "session_summaries",
        sa.Column("cost_usd", sa.Float, nullable=True),
    )
    op.add_column(
        "session_summaries",
        sa.Column("total_turns", sa.Integer, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("session_summaries", "total_turns")
    op.drop_column("session_summaries", "cost_usd")
    op.drop_column("session_summaries", "model")
    op.drop_column("session_summaries", "compact_count")
    op.drop_column("session_summaries", "mcp_calls")
    op.drop_column("session_summaries", "tool_uses")
