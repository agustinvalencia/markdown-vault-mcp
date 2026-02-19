# Detailed Tool Specifications for Agent/MCP Optimization

## Overview

These specifications define agent-optimized tools that provide synthesis and insights rather than raw data. Each tool follows the design principles:
- **Synthesis over retrieval**
- **Actionable over informational**
- **Progressive discovery**
- **Context-aware**
- **Conversational state support**

---

## 1. Planning Tools

### 1.1 `suggest_next_action`

**Purpose**: Recommend what the user should work on next based on current context.

**MCP Tool Definition**:
```python
@mcp.tool()
def suggest_next_action(
    context: Literal["focus", "today", "general"] = "focus",
    time_available: str | None = None,  # "30m", "2h", "full-day"
    energy_level: Literal["low", "medium", "high"] | None = None,
    session_id: str | None = None
) -> dict:
    """Suggest what the user should work on next.

    Analyzes current vault state to provide intelligent task recommendations
    based on focus, priorities, dependencies, and user context.

    Args:
        context: Scope of recommendation
            - "focus": Tasks from active focus project only
            - "today": Tasks planned or relevant for today
            - "general": Consider all open tasks
        time_available: How much time user has (affects task selection)
        energy_level: User's current energy (affects task difficulty matching)
        session_id: Optional session ID for conversation continuity

    Returns:
        {
            "suggestion": {
                "task_id": "MCP-042",
                "title": "Implement OAuth flow",
                "project": "MCP",
                "priority": "high",
                "estimated_duration": "2h",
                "rationale": [
                    "Part of active focus project (MCP)",
                    "High priority with no blockers",
                    "Can be completed in available time",
                    "Prerequisite for MCP-043 and MCP-044"
                ],
                "context_needed": [
                    "OAuth documentation: docs/oauth-spec.md",
                    "Related task: MCP-041 (completed yesterday)"
                ]
            },
            "alternatives": [
                {
                    "task_id": "MCP-045",
                    "title": "Write unit tests",
                    "why_alternative": "Lower priority but good if low energy"
                },
                {
                    "task_id": "INB-012",
                    "title": "Review PR comments",
                    "why_alternative": "Quick win, 15-20 minutes"
                }
            ],
            "blockers": [
                {
                    "task_id": "MCP-043",
                    "issue": "Waiting on external API key",
                    "suggested_action": "Send reminder email"
                }
            ],
            "maintenance_opportunities": [
                {
                    "type": "orphan_notes",
                    "count": 3,
                    "suggestion": "5-10 minutes to link orphaned notes"
                }
            ]
        }
    """
```

**Implementation Details**:

**Data Sources**:
1. Current focus project (`.mdvault/state/context.toml`)
2. Task metadata from index (status, priority, due dates)
3. Activity log (recent completions, time patterns)
4. Task dependencies (from frontmatter or links)
5. Session state (if session_id provided)

**Scoring Algorithm**:
```python
def score_task(task: Task, context: Context) -> float:
    score = 0.0

    # Focus alignment (0-30 points)
    if task.project == context.active_focus:
        score += 30
    elif context.scope == "focus":
        return 0  # Exclude non-focus tasks

    # Priority (0-25 points)
    priority_scores = {"high": 25, "medium": 15, "low": 5}
    score += priority_scores.get(task.priority, 10)

    # Urgency/Due date (0-20 points)
    if task.due_date:
        days_until_due = (task.due_date - today).days
        if days_until_due <= 0:
            score += 20  # Overdue
        elif days_until_due <= 2:
            score += 15  # Due soon
        elif days_until_due <= 7:
            score += 10

    # Momentum (0-15 points)
    # Tasks in same project as recent completions get boost
    if task.project in context.recent_projects:
        score += 15

    # Time fit (0-10 points)
    if context.time_available:
        if task.estimated_duration <= context.time_available:
            score += 10
        else:
            score -= 20  # Penalize tasks that won't fit

    # Blockers (-50 points)
    if task.has_blockers:
        score -= 50

    # Energy match (0-10 points)
    if context.energy_level == "low" and task.complexity == "low":
        score += 10
    elif context.energy_level == "high" and task.complexity == "high":
        score += 10

    return score
```

**Rationale Generation**:
- Explain why this task was selected
- Reference focus project, priorities, dependencies
- Mention time constraints if applicable
- Note energy level match if applicable

**Fallback Behavior**:
- If no tasks match criteria: suggest maintenance tasks or note review
- If focus not set: suggest setting focus first
- If all tasks blocked: surface blockers prominently

---

### 1.2 `generate_daily_plan`

**Purpose**: Create structured plan for a day with realistic task allocation.

**MCP Tool Definition**:
```python
@mcp.tool()
def generate_daily_plan(
    date: str = "today",
    max_tasks: int = 3,
    include_maintenance: bool = True,
    include_learning: bool = False,
    session_id: str | None = None
) -> dict:
    """Generate structured plan for a specific day.

    Creates a realistic daily plan with primary focus, secondary tasks,
    and optional maintenance/learning time.

    Args:
        date: Date to plan (YYYY-MM-DD, "today", "tomorrow", date expression)
        max_tasks: Maximum number of tasks to include (default: 3)
        include_maintenance: Include quick maintenance tasks
        include_learning: Include learning/exploration time blocks
        session_id: Optional session ID for conversation continuity

    Returns:
        {
            "date": "2026-01-29",
            "day_of_week": "Wednesday",
            "context": {
                "active_focus": "MCP",
                "recent_activity": "Completed 2 tasks yesterday (MCP-041, MCP-042)",
                "continuation": "Building on OAuth implementation"
            },
            "plan": {
                "primary_focus": {
                    "task_id": "MCP-043",
                    "title": "Test OAuth integration",
                    "estimated_duration": "2-3h",
                    "time_block": "09:00-12:00",
                    "rationale": "Natural continuation of yesterday's work",
                    "prerequisites": ["Review OAuth docs", "Check API credentials"]
                },
                "secondary_tasks": [
                    {
                        "task_id": "MCP-044",
                        "title": "Update documentation",
                        "estimated_duration": "1h",
                        "time_block": "14:00-15:00",
                        "priority": "medium"
                    },
                    {
                        "task_id": "INB-015",
                        "title": "Quick bug fix",
                        "estimated_duration": "30m",
                        "time_block": "15:30-16:00",
                        "priority": "low"
                    }
                ],
                "maintenance": [
                    {
                        "type": "orphan_notes",
                        "description": "Link 3 orphaned notes",
                        "estimated_duration": "10m",
                        "time_block": "13:00-13:10"
                    },
                    {
                        "type": "stale_tasks",
                        "description": "Review 2 stale tasks",
                        "estimated_duration": "15m",
                        "time_block": "16:00-16:15"
                    }
                ],
                "learning": [
                    {
                        "topic": "OAuth security best practices",
                        "estimated_duration": "30m",
                        "time_block": "11:00-11:30",
                        "rationale": "Related to primary focus"
                    }
                ] if include_learning else []
            },
            "capacity_analysis": {
                "total_work_hours": 5.5,
                "primary_focus_hours": 3.0,
                "secondary_tasks_hours": 1.5,
                "maintenance_hours": 0.5,
                "learning_hours": 0.5,
                "buffer_hours": 2.5,
                "realistic": true,
                "notes": "Realistic for a focused work day with breaks"
            },
            "dependencies": [
                {
                    "task": "MCP-043",
                    "depends_on": "MCP-042 (completed)",
                    "status": "ready"
                }
            ],
            "risks": [
                {
                    "task": "MCP-043",
                    "risk": "May take longer if API issues occur",
                    "mitigation": "Have fallback task (MCP-044) ready"
                }
            ]
        }
    """
```

**Implementation Details**:

**Planning Algorithm**:
```python
def generate_plan(date: Date, constraints: Constraints) -> DailyPlan:
    # 1. Get context
    focus = get_active_focus()
    yesterday = get_context_day(date - 1)
    today_existing = get_context_day(date)

    # 2. Select primary focus task
    primary = select_primary_task(
        focus=focus,
        yesterday=yesterday,
        constraints=constraints
    )

    # 3. Select secondary tasks
    secondary = select_secondary_tasks(
        primary=primary,
        max_count=constraints.max_tasks - 1,
        total_time_budget=constraints.available_hours - primary.duration
    )

    # 4. Add maintenance tasks if requested
    maintenance = []
    if constraints.include_maintenance:
        maintenance = get_maintenance_opportunities(
            time_budget="30m",
            priority="quick-wins"
        )

    # 5. Add learning time if requested
    learning = []
    if constraints.include_learning:
        learning = suggest_learning_topics(
            related_to=primary.topic,
            duration="30m"
        )

    # 6. Analyze capacity
    capacity = analyze_capacity(
        tasks=[primary] + secondary,
        maintenance=maintenance,
        learning=learning
    )

    # 7. Check dependencies and risks
    dependencies = check_dependencies([primary] + secondary)
    risks = identify_risks([primary] + secondary)

    return DailyPlan(
        primary=primary,
        secondary=secondary,
        maintenance=maintenance,
        learning=learning,
        capacity=capacity,
        dependencies=dependencies,
        risks=risks
    )
```

**Primary Task Selection Criteria**:
1. Continuation from yesterday (if applicable)
2. Focus project alignment
3. Highest priority non-blocked task
4. Can be completed in one session (2-4 hours)

**Time Block Allocation**:
- Primary focus: Morning block (09:00-12:00)
- Secondary tasks: Afternoon blocks
- Maintenance: Between-task buffers
- Learning: Before/after lunch

**Capacity Analysis**:
- Calculate total estimated work hours
- Add 30% buffer for realistic planning
- Flag if over 6 hours of scheduled work (unrealistic)

---

### 1.3 `detect_stalled_work`

**Purpose**: Identify tasks and projects that haven't made progress recently.

**MCP Tool Definition**:
```python
@mcp.tool()
def detect_stalled_work(
    lookback_days: int = 14,
    include_recommendations: bool = True,
    severity_threshold: Literal["minor", "moderate", "severe"] = "moderate"
) -> dict:
    """Find tasks and projects without recent progress.

    Analyzes activity logs and note modifications to identify work that
    may be stuck, forgotten, or needs attention.

    Args:
        lookback_days: Days to look back for activity (default: 14)
        include_recommendations: Include suggested actions
        severity_threshold: Minimum severity to report
            - "minor": No activity for 7+ days
            - "moderate": No activity for 14+ days (default)
            - "severe": No activity for 30+ days

    Returns:
        {
            "summary": {
                "tasks_stalled": 5,
                "projects_stalled": 2,
                "total_severity_score": 23,
                "oldest_stall": "45 days"
            },
            "stalled_tasks": [
                {
                    "task_id": "MCP-039",
                    "title": "Migrate database schema",
                    "project": "MCP",
                    "status": "in-progress",
                    "last_activity": "2025-12-15",
                    "days_stalled": 45,
                    "severity": "severe",
                    "indicators": [
                        "Status is 'in-progress' but no activity for 45 days",
                        "No log entries in task note",
                        "Not mentioned in daily notes"
                    ],
                    "possible_reasons": [
                        "Blocked by external dependency",
                        "Lost in context switch",
                        "Complexity underestimated"
                    ],
                    "recommended_actions": [
                        "Review task and update status",
                        "Break into smaller sub-tasks",
                        "Close if no longer relevant"
                    ]
                },
                {
                    "task_id": "SIDE-003",
                    "title": "Research deployment options",
                    "project": "SIDE",
                    "status": "todo",
                    "last_activity": "2026-01-01",
                    "days_stalled": 28,
                    "severity": "moderate",
                    "indicators": [
                        "Created 28 days ago, never started",
                        "No links to/from other notes"
                    ],
                    "possible_reasons": [
                        "Lower priority",
                        "Unclear scope"
                    ],
                    "recommended_actions": [
                        "Define clearer scope and acceptance criteria",
                        "Re-prioritize or defer"
                    ]
                }
            ],
            "stalled_projects": [
                {
                    "project_id": "SIDE",
                    "title": "Side Project",
                    "status": "active",
                    "last_activity": "2025-12-20",
                    "days_stalled": 40,
                    "severity": "severe",
                    "indicators": [
                        "No tasks completed in 40 days",
                        "3 open tasks, all stalled",
                        "Project status still 'active'"
                    ],
                    "recommended_actions": [
                        "Review project viability",
                        "Update status to 'paused' or 'archived'",
                        "Close or delegate stalled tasks"
                    ]
                }
            ],
            "patterns": [
                {
                    "pattern": "Research tasks often stall",
                    "evidence": "3/5 stalled tasks are research-type",
                    "suggestion": "Consider time-boxing research tasks"
                },
                {
                    "pattern": "SIDE project consistently deprioritized",
                    "evidence": "Multiple stalls in SIDE project",
                    "suggestion": "Formally pause or archive project"
                }
            ]
        }
    """
```

**Implementation Details**:

**Stall Detection Algorithm**:
```python
def detect_stalled_task(task: Task, lookback_days: int) -> Optional[StalledTask]:
    # Get activity for this task
    task_activity = get_task_activity(task.id, lookback_days)

    # Check various staleness indicators
    days_since_created = (today - task.created_date).days
    days_since_last_activity = (today - task_activity.last_activity).days if task_activity else days_since_created

    # Severity classification
    severity = None
    if days_since_last_activity >= 30:
        severity = "severe"
    elif days_since_last_activity >= 14:
        severity = "moderate"
    elif days_since_last_activity >= 7:
        severity = "minor"
    else:
        return None  # Not stalled

    # Gather indicators
    indicators = []
    if task.status == "in-progress" and days_since_last_activity > 14:
        indicators.append(f"Status is 'in-progress' but no activity for {days_since_last_activity} days")

    if task_activity.log_entries == 0:
        indicators.append("No log entries in task note")

    if task_activity.daily_mentions == 0:
        indicators.append("Not mentioned in daily notes")

    # Generate recommendations
    recommendations = generate_stall_recommendations(task, severity, indicators)

    return StalledTask(
        task=task,
        days_stalled=days_since_last_activity,
        severity=severity,
        indicators=indicators,
        recommendations=recommendations
    )
```

**Pattern Detection**:
- Identify common characteristics of stalled tasks
- Detect project-level stalling patterns
- Suggest systemic improvements

---

### 1.4 `analyze_task_priority`

**Purpose**: Re-rank tasks based on multiple priority factors.

**MCP Tool Definition**:
```python
@mcp.tool()
def analyze_task_priority(
    project: str | None = None,
    criteria: dict[str, float] | None = None,
    limit: int = 10
) -> dict:
    """Analyze and rank tasks by priority considering multiple factors.

    Uses weighted scoring to re-prioritize tasks beyond simple high/medium/low.

    Args:
        project: Optional project ID to limit scope
        criteria: Optional custom criteria weights
            {
                "urgency": 0.3,      # Due date, time sensitivity
                "importance": 0.25,  # Business value, user-facing metadata
                "momentum": 0.2,     # Related to recent work
                "effort": 0.15,      # Lower effort = higher priority
                "blockers": 0.1      # Blocking other tasks = higher priority
            }
        limit: Maximum number of tasks to return

    Returns:
        {
            "analysis": {
                "total_tasks_analyzed": 25,
                "criteria_used": {
                    "urgency": 0.3,
                    "importance": 0.25,
                    "momentum": 0.2,
                    "effort": 0.15,
                    "blockers": 0.1
                },
                "score_range": {"min": 12, "max": 89}
            },
            "ranked_tasks": [
                {
                    "rank": 1,
                    "task_id": "MCP-043",
                    "title": "Test OAuth integration",
                    "project": "MCP",
                    "priority_score": 89,
                    "breakdown": {
                        "urgency": {"score": 28, "reason": "Due in 2 days"},
                        "importance": {"score": 23, "reason": "Blocks 3 other tasks"},
                        "momentum": {"score": 18, "reason": "Builds on yesterday's work"},
                        "effort": {"score": 12, "reason": "Medium effort (2-3h)"},
                        "blockers": {"score": 8, "reason": "Blocks MCP-044, MCP-045"}
                    },
                    "recommendation": "Strong candidate for immediate work"
                },
                {
                    "rank": 2,
                    "task_id": "MCP-047",
                    "title": "Fix critical bug",
                    "project": "MCP",
                    "priority_score": 85,
                    "breakdown": {
                        "urgency": {"score": 30, "reason": "Critical bug, overdue"},
                        "importance": {"score": 25, "reason": "User-facing issue"},
                        "momentum": {"score": 10, "reason": "Different area than recent work"},
                        "effort": {"score": 15, "reason": "Quick fix (30m)"},
                        "blockers": {"score": 5, "reason": "No dependencies"}
                    },
                    "recommendation": "Urgent but requires context switch"
                }
            ],
            "insights": [
                "MCP-043 has highest momentum score - natural continuation",
                "MCP-047 is urgent but may disrupt flow",
                "Consider batching quick fixes (MCP-047, INB-012) together"
            ]
        }
    """
```

**Implementation**: Multi-factor scoring with transparent breakdown of why each task ranks where it does.

---

## 2. Review Tools

### 2.1 `generate_review_report`

**Purpose**: Generate structured review with insights, not just data.

**MCP Tool Definition**:
```python
@mcp.tool()
def generate_review_report(
    period: Literal["day", "week", "month"],
    date: str | None = None,
    depth: Literal["minimal", "normal", "full"] = "normal",
    perspective: Literal["accomplishments", "planning", "maintenance"] = "accomplishments"
) -> dict:
    """Generate structured review report with insights and prompts.

    Unlike get_context_X which returns raw data, this provides
    synthesized insights and reflection prompts.

    Args:
        period: Time period to review
        date: Specific date/week/month, or None for most recent
        depth: Level of detail
            - "minimal": High-level summary only
            - "normal": Summary + key insights
            - "full": Comprehensive with patterns and recommendations
        perspective: Framing of the review
            - "accomplishments": What got done (default)
            - "planning": What's next
            - "maintenance": Vault health

    Returns:
        {
            "period": {
                "type": "week",
                "date_range": "2026-W04 (Jan 20-26)",
                "days_analyzed": 7
            },
            "summary": {
                "headline": "Productive week with strong focus on MCP project",
                "tasks_completed": 8,
                "tasks_created": 5,
                "projects_active": 2,
                "notes_created": 12,
                "vault_growth": "+2.3%"
            },
            "accomplishments": {
                "highlight": "Completed OAuth implementation (MCP-042, MCP-043)",
                "completed_tasks": [
                    {
                        "task_id": "MCP-042",
                        "title": "Implement OAuth flow",
                        "significance": "Major milestone, unlocks next phase",
                        "effort": "6 hours over 2 days"
                    },
                    // ... more tasks
                ],
                "milestones": [
                    {
                        "description": "MCP project reached 50% completion",
                        "date": "2026-01-24"
                    }
                ],
                "quick_wins": [
                    "Fixed 3 small bugs (INB-010, INB-011, INB-012)",
                    "Updated documentation for 2 features"
                ]
            },
            "challenges": [
                {
                    "issue": "MCP-039 remains stalled for 45 days",
                    "impact": "Blocking database migration",
                    "suggested_action": "Break into smaller tasks or reassess scope"
                },
                {
                    "issue": "SIDE project had no activity",
                    "impact": "3 open tasks not progressing",
                    "suggested_action": "Consider pausing or archiving project"
                }
            ],
            "patterns": {
                "productivity": {
                    "trend": "increasing",
                    "data": "8 tasks this week vs 5 last week (+60%)",
                    "insight": "Strong momentum on MCP project"
                },
                "focus": {
                    "primary_project": "MCP (75% of activity)",
                    "context_switches": 3,
                    "insight": "Good focus, minimal switching"
                },
                "time_of_day": {
                    "peak_productivity": "09:00-12:00",
                    "insight": "Morning hours most productive"
                }
            },
            "reflection_prompts": {
                "went_well": "You completed OAuth implementation ahead of schedule and maintained strong focus on MCP project. What factors contributed to this success?",
                "could_improve": "MCP-039 has been stalled for 45 days. What's blocking progress? Should this task be broken down or closed?",
                "next_period": "With OAuth complete, MCP-044 and MCP-045 are unblocked. Consider starting MCP-044 (testing) early next week to maintain momentum."
            },
            "maintenance_needed": [
                {
                    "type": "orphaned_notes",
                    "count": 3,
                    "description": "3 notes created this week with no links",
                    "action": "Review and link to relevant projects",
                    "estimated_time": "10-15 minutes"
                },
                {
                    "type": "stale_tasks",
                    "count": 2,
                    "description": "2 tasks in SIDE project without progress",
                    "action": "Update status or close",
                    "estimated_time": "5-10 minutes"
                }
            ],
            "next_period_preview": {
                "focus_suggestion": "MCP project (maintain momentum)",
                "priority_tasks": [
                    "MCP-044: Test OAuth integration",
                    "MCP-045: Update documentation"
                ],
                "opportunities": [
                    "Quick wins: Address orphaned notes",
                    "Review SIDE project status"
                ]
            }
        }
    """
```

**Key Features**:
- **Insight generation**: Not just "8 tasks done" but "60% increase, strong momentum"
- **Reflection prompts**: Guide user through structured reflection
- **Maintenance opportunities**: Proactively surface housekeeping tasks
- **Forward-looking**: Preview next period priorities

---

### 2.2 `compare_periods`

**Purpose**: Compare two time periods to identify trends and changes.

**MCP Tool Definition**:
```python
@mcp.tool()
def compare_periods(
    period1: str,  # "2026-W03" or "2026-01" or "2026-01-20"
    period2: str,  # "2026-W04" or "2026-02" or "2026-01-27"
    metrics: list[str] | None = None  # Specific metrics to compare
) -> dict:
    """Compare two time periods for trends and changes.

    Args:
        period1: First period (earlier)
        period2: Second period (later)
        metrics: Optional list of specific metrics to compare
            Options: ["tasks_completed", "tasks_created", "projects_active",
                     "notes_created", "context_switches", "stalled_work"]

    Returns:
        {
            "periods": {
                "period1": {"label": "Week 3", "dates": "Jan 13-19"},
                "period2": {"label": "Week 4", "dates": "Jan 20-26"}
            },
            "comparison": {
                "tasks_completed": {
                    "period1": 5,
                    "period2": 8,
                    "change": "+60%",
                    "trend": "increasing",
                    "significance": "substantial",
                    "interpretation": "Productivity increased significantly"
                },
                "tasks_created": {
                    "period1": 3,
                    "period2": 5,
                    "change": "+67%",
                    "trend": "increasing",
                    "significance": "moderate"
                },
                "projects_active": {
                    "period1": 3,
                    "period2": 2,
                    "change": "-33%",
                    "trend": "decreasing",
                    "significance": "moderate",
                    "interpretation": "Improved focus, fewer active projects"
                },
                "context_switches": {
                    "period1": 5,
                    "period2": 3,
                    "change": "-40%",
                    "trend": "decreasing",
                    "significance": "positive",
                    "interpretation": "Better focus, less task switching"
                }
            },
            "insights": [
                "Productivity increased 60% - strong improvement",
                "Reduced context switching (5 → 3) likely contributed to higher completion rate",
                "SIDE project inactive in period2 - this enabled better MCP focus",
                "Pattern: Fewer active projects correlates with higher completion rate"
            ],
            "recommendations": [
                "Continue focusing on 1-2 projects at a time",
                "Consider formally pausing SIDE project",
                "Maintain morning work blocks (contributed to Week 4 success)"
            ]
        }
    """
```

**Key Features**:
- **Trend analysis**: Not just numbers but interpretation
- **Correlation detection**: "Fewer projects = higher completion rate"
- **Actionable insights**: "Continue focusing on 1-2 projects"

---

### 2.3 `detect_patterns`

**Purpose**: Identify productivity patterns and bottlenecks.

**MCP Tool Definition**:
```python
@mcp.tool()
def detect_patterns(
    metric: Literal[
        "productivity",
        "focus",
        "bottlenecks",
        "time_of_day",
        "day_of_week"
    ],
    lookback_days: int = 30
) -> dict:
    """Detect patterns in work habits and productivity.

    Args:
        metric: Type of pattern to analyze
        lookback_days: Days of history to analyze

    Returns:
        {
            "metric": "productivity",
            "analysis_period": "30 days (2025-12-30 to 2026-01-29)",
            "pattern_detected": true,
            "findings": [
                {
                    "pattern": "3x more productive on Tuesdays and Wednesdays",
                    "evidence": {
                        "tuesday_avg": 4.2,
                        "wednesday_avg": 4.5,
                        "monday_avg": 1.8,
                        "thursday_avg": 2.1,
                        "friday_avg": 1.5
                    },
                    "confidence": "high",
                    "recommendation": "Schedule high-priority tasks for Tue/Wed"
                },
                {
                    "pattern": "Morning hours (09:00-12:00) most productive",
                    "evidence": {
                        "morning_completions": 18,
                        "afternoon_completions": 8,
                        "evening_completions": 2
                    },
                    "confidence": "high",
                    "recommendation": "Protect morning time for deep work"
                },
                {
                    "pattern": "Research tasks often stall",
                    "evidence": {
                        "research_tasks_created": 8,
                        "research_tasks_completed": 2,
                        "completion_rate": "25%"
                    },
                    "confidence": "moderate",
                    "recommendation": "Time-box research tasks or break into smaller chunks"
                }
            ],
            "visualizations": [
                {
                    "type": "heatmap",
                    "title": "Tasks Completed by Day of Week",
                    "data": {
                        "Mon": 1.8,
                        "Tue": 4.2,
                        "Wed": 4.5,
                        "Thu": 2.1,
                        "Fri": 1.5
                    }
                }
            ],
            "recommendations": [
                "Block Tue/Wed mornings for highest-priority tasks",
                "Consider 'Research Fridays' for open-ended investigation",
                "Avoid scheduling important work on Monday (ramp-up day)"
            ]
        }
    """
```

**Patterns to Detect**:
- Day of week productivity variations
- Time of day patterns
- Task type success rates
- Project switching frequency
- Completion velocity trends

---

## 3. Meta-Tools

### 3.1 `get_agent_capabilities`

**Purpose**: Tell agent what it can help with right now.

**MCP Tool Definition**:
```python
@mcp.tool()
def get_agent_capabilities(
    include_context: bool = True,
    include_suggestions: bool = True
) -> dict:
    """Tell agent what capabilities are available based on current vault state.

    Context-aware - capabilities change based on:
    - Whether focus is set
    - Whether tasks exist
    - Whether recent activity exists
    - Vault health (orphans, stale tasks)

    Returns:
        {
            "available_capabilities": {
                "planning": {
                    "available": true,
                    "confidence": "high",
                    "reasons": [
                        "Focus is set (MCP)",
                        "5 open tasks available",
                        "Recent activity suggests active work"
                    ],
                    "suggested_actions": [
                        "Plan today: Generate daily plan",
                        "Suggest next task: Get immediate recommendation",
                        "Analyze priorities: Re-rank tasks"
                    ]
                },
                "reviewing": {
                    "available": true,
                    "confidence": "high",
                    "reasons": [
                        "Last week had significant activity",
                        "Completed 8 tasks last week"
                    ],
                    "suggested_actions": [
                        "Weekly review: Review last week's progress",
                        "Compare weeks: See how this week compares to last",
                        "Detect patterns: Identify productivity trends"
                    ]
                },
                "maintenance": {
                    "available": true,
                    "confidence": "medium",
                    "issues_found": {
                        "orphaned_notes": 3,
                        "stale_tasks": 2,
                        "broken_links": 0
                    },
                    "suggested_actions": [
                        "Fix orphans: Link 3 orphaned notes (~10 min)",
                        "Review stale tasks: Update or close 2 tasks (~5 min)"
                    ]
                },
                "focus_management": {
                    "available": true,
                    "current_focus": "MCP",
                    "suggested_actions": [
                        "Continue focus: Keep working on MCP",
                        "Switch focus: Change to different project",
                        "Review focus: Check MCP project health"
                    ]
                }
            },
            "suggested_conversation_starters": [
                "Would you like me to suggest what to work on next?",
                "Want to review last week's progress?",
                "I noticed 3 orphaned notes - should we link them?",
                "How about we plan your day?"
            ],
            "context_summary": {
                "vault_health": "good",
                "active_focus": "MCP",
                "recent_activity": "8 tasks completed last week",
                "issues_needing_attention": 2
            }
        }
    """
```

**Use Case**: Agent calls this on startup to understand what it can help with.

---

### 3.2 `suggest_tool_sequence`

**Purpose**: Recommend which tools to call for a given goal.

**MCP Tool Definition**:
```python
@mcp.tool()
def suggest_tool_sequence(
    goal: str,
    context: dict[str, Any] | None = None
) -> list[dict]:
    """Given a user goal, suggest which tools to call in what order.

    Args:
        goal: Free-form user goal
            Examples: "plan my day", "review last week",
                     "what should I work on", "check project health"
        context: Optional conversation context

    Returns:
        [
            {
                "step": 1,
                "tool": "get_context_day",
                "params": {"date": "yesterday", "depth": "normal"},
                "rationale": "Understand what was started yesterday to maintain continuity",
                "required": true
            },
            {
                "step": 2,
                "tool": "get_context_day",
                "params": {"date": "today", "depth": "minimal"},
                "rationale": "Check if anything is already planned for today",
                "required": false
            },
            {
                "step": 3,
                "tool": "suggest_next_action",
                "params": {"context": "focus", "time_available": null},
                "rationale": "Get personalized task recommendation based on context",
                "required": true,
                "depends_on": [1, 2]
            },
            {
                "step": 4,
                "tool": "generate_daily_plan",
                "params": {"date": "today", "max_tasks": 3},
                "rationale": "Create structured plan incorporating suggestion",
                "required": false,
                "conditional": "if user wants full day plan (vs just next action)"
            }
        ]
    """
```

**Goal Patterns**:
```python
GOAL_PATTERNS = {
    "plan my day": ["get_context_day(yesterday)", "suggest_next_action", "generate_daily_plan"],
    "what should I work on": ["suggest_next_action", "analyze_task_priority"],
    "review last week": ["generate_review_report(week)", "compare_periods"],
    "check project health": ["get_context_note", "detect_stalled_work", "analyze_project_health"],
    "find bottlenecks": ["detect_stalled_work", "detect_patterns(bottlenecks)"],
    "maintenance": ["list_maintenance_tasks", "detect_stalled_work"],
}
```

---

## Implementation Priority

### Phase 1 (Weeks 1-2): Core Planning
1. `suggest_next_action` - Immediate value
2. `get_agent_capabilities` - Enables agent self-discovery
3. Session management infrastructure

### Phase 2 (Weeks 3-4): Daily Planning
1. `generate_daily_plan`
2. `analyze_task_priority`
3. Planning workflow template

### Phase 3 (Weeks 5-6): Reviews
1. `generate_review_report`
2. `compare_periods`
3. Review workflow template

### Phase 4 (Weeks 7-8): Analysis
1. `detect_stalled_work`
2. `detect_patterns`
3. `suggest_tool_sequence`

---

## Testing Strategy

Each tool should have:
1. **Unit tests**: Core logic and scoring algorithms
2. **Integration tests**: Tool with real vault data
3. **Conversation tests**: Multi-turn agent dialogues
4. **Edge case tests**: Empty vaults, no focus, no tasks

## Documentation Requirements

Each tool needs:
1. **MCP tool description**: Clear, concise, with examples
2. **Agent guidelines**: When to use, what to expect
3. **User documentation**: What the agent can do
4. **Workflow examples**: Common conversation patterns
