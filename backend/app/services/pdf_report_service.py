from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PDF_DIRECTORY = Path(
    "results"
)


class PDFReportError(Exception):
    pass


def safe_text(
    value: Any,
    fallback: str = "N/A",
) -> str:
    if value is None:
        return fallback

    text = str(value).strip()

    return text if text else fallback


def create_results_pdf(
    run_id: str,
    result_data: dict[str, Any],
) -> str:
    PDF_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_path = (
        PDF_DIRECTORY
        / f"{run_id}-results.pdf"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            "Autonomous CI/CD "
            "Healing Agent Report"
        ),
    )

    story = []

    story.append(
        Paragraph(
            "Autonomous CI/CD Healing Agent",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Repository Analysis & Healing Report",
            styles["Heading3"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    summary_data = [
        [
            "Run ID",
            safe_text(
                result_data.get(
                    "run_id"
                )
            ),
        ],
        [
            "Repository",
            safe_text(
                result_data.get(
                    "repository_url"
                )
            ),
        ],
        [
            "Status",
            safe_text(
                result_data.get(
                    "status"
                )
            ),
        ],
        [
            "Verification Mode",
            safe_text(
                result_data.get(
                    "verification_mode"
                )
            ),
        ],
        [
            "Team",
            safe_text(
                result_data.get(
                    "team_name"
                )
            ),
        ],
        [
            "Leader",
            safe_text(
                result_data.get(
                    "leader_name"
                )
            ),
        ],
        [
            "Duration",
            (
                f"{result_data.get('duration_seconds', 0)} sec"
            ),
        ],
        [
            "Final Score",
            safe_text(
                (
                    result_data
                    .get(
                        "score",
                        {},
                    )
                    .get(
                        "final_score"
                    )
                ),
                "0",
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            48 * mm,
            120 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#E8EEF8"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor(
                        "#B8C3D6"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    story.append(
        Paragraph(
            "Project Detection",
            section_style,
        )
    )

    project = (
        result_data.get(
            "project",
            {}
        )
        or {}
    )

    project_data = [
        [
            "Project Type",
            safe_text(
                project.get(
                    "project_type"
                )
            ),
        ],
        [
            "Languages",
            ", ".join(
                project.get(
                    "languages",
                    [],
                )
            )
            or "N/A",
        ],
        [
            "Frameworks",
            ", ".join(
                project.get(
                    "frameworks",
                    [],
                )
            )
            or "N/A",
        ],
        [
            "Package Managers",
            ", ".join(
                project.get(
                    "package_managers",
                    [],
                )
            )
            or "N/A",
        ],
    ]

    project_table = Table(
        project_data,
        colWidths=[
            48 * mm,
            120 * mm,
        ],
    )

    project_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
            ]
        )
    )

    story.append(
        project_table
    )

    story.append(
        Paragraph(
            "Verification",
            section_style,
        )
    )

    verification = (
        result_data.get(
            "verification",
            {}
        )
        or {}
    )

    story.append(
        Paragraph(
            (
                "Passed: "
                f"{safe_text(verification.get('passed'))}"
                "<br/>"
                "Mode: "
                f"{safe_text(verification.get('mode'))}"
            ),
            body_style,
        )
    )

    story.append(
        Paragraph(
            "Healing Iterations",
            section_style,
        )
    )

    iterations = (
        result_data.get(
            "iterations",
            {}
        )
        or {}
    )

    timeline = (
        iterations.get(
            "timeline",
            []
        )
        or []
    )

    if timeline:
        timeline_data = [
            [
                "Iteration",
                "Status",
                "Fixes",
            ]
        ]

        for item in timeline:
            timeline_data.append(
                [
                    safe_text(
                        item.get(
                            "iteration"
                        )
                    ),
                    safe_text(
                        item.get(
                            "status"
                        )
                    ),
                    safe_text(
                        item.get(
                            "fixes_applied",
                            0,
                        )
                    ),
                ]
            )

        timeline_table = Table(
            timeline_data,
            repeatRows=1,
            colWidths=[
                40 * mm,
                85 * mm,
                40 * mm,
            ],
        )

        timeline_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#DDE8F8"
                        ),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                ]
            )
        )

        story.append(
            timeline_table
        )

    else:
        story.append(
            Paragraph(
                "No healing iterations recorded.",
                body_style,
            )
        )

    story.append(
        Paragraph(
            "Applied Fixes",
            section_style,
        )
    )

    fixes = (
        result_data
        .get(
            "fix_application",
            {},
        )
        .get(
            "applied_fixes",
            [],
        )
        or []
    )

    if fixes:
        for index, fix in enumerate(
            fixes,
            start=1,
        ):
            story.append(
                Paragraph(
                    (
                        f"<b>Fix {index}</b><br/>"
                        f"File: {safe_text(fix.get('file'))}<br/>"
                        f"Line: {safe_text(fix.get('line'))}<br/>"
                        f"Status: {safe_text(fix.get('apply_status'))}<br/>"
                        f"Reason: {safe_text(fix.get('reason'))}"
                    ),
                    body_style,
                )
            )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )
    else:
        story.append(
            Paragraph(
                "No fixes were applied.",
                body_style,
            )
        )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Git Automation",
            section_style,
        )
    )

    git_result = (
        result_data.get(
            "git"
        )
        or {}
    )

    git_data = [
        [
            "Branch",
            safe_text(
                git_result.get(
                    "branch_name"
                )
            ),
        ],
        [
            "Commit",
            safe_text(
                git_result.get(
                    "commit_sha"
                )
            ),
        ],
        [
            "Push Status",
            safe_text(
                git_result.get(
                    "push_status"
                )
            ),
        ],
    ]

    git_table = Table(
        git_data,
        colWidths=[
            48 * mm,
            120 * mm,
        ],
    )

    git_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
            ]
        )
    )

    story.append(
        git_table
    )

    story.append(
        Paragraph(
            "Pull Request",
            section_style,
        )
    )

    pull_request = (
        result_data.get(
            "pull_request"
        )
        or {}
    )

    pr_data = [
        [
            "Status",
            safe_text(
                pull_request.get(
                    "status"
                )
            ),
        ],
        [
            "PR Number",
            safe_text(
                pull_request.get(
                    "number"
                )
            ),
        ],
        [
            "State",
            safe_text(
                pull_request.get(
                    "state"
                )
            ),
        ],
        [
            "URL",
            safe_text(
                pull_request.get(
                    "url"
                )
            ),
        ],
    ]

    pr_table = Table(
        pr_data,
        colWidths=[
            48 * mm,
            120 * mm,
        ],
    )

    pr_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
            ]
        )
    )

    story.append(
        pr_table
    )

    story.append(
        Paragraph(
            "CI/CD",
            section_style,
        )
    )

    cicd = (
        result_data.get(
            "cicd"
        )
        or {}
    )

    story.append(
        Paragraph(
            (
                f"Status: {safe_text(cicd.get('status'))}"
                "<br/>"
                f"Conclusion: {safe_text(cicd.get('conclusion'))}"
                "<br/>"
                f"Workflow: {safe_text(cicd.get('workflow_name'))}"
            ),
            body_style,
        )
    )

    story.append(
        Paragraph(
            "Verification Logs",
            section_style,
        )
    )

    verification_results = (
        verification.get(
            "results",
            []
        )
        or []
    )

    if verification_results:
        for result in (
            verification_results
        ):
            command = safe_text(
                result.get(
                    "command"
                )
            )

            status = safe_text(
                result.get(
                    "status"
                )
            )

            stdout = safe_text(
                result.get(
                    "stdout"
                ),
                "",
            )

            stderr = safe_text(
                result.get(
                    "stderr"
                ),
                "",
            )

            log_text = (
                stdout
                or stderr
                or "No logs"
            )

            # Avoid excessively huge PDFs.
            if len(log_text) > 5000:
                log_text = (
                    log_text[:5000]
                    + "\n[LOG TRUNCATED]"
                )

            story.append(
                Paragraph(
                    (
                        f"<b>{command}</b> - {status}"
                    ),
                    body_style,
                )
            )

            story.append(
                Paragraph(
                    (
                        log_text
                        .replace(
                            "&",
                            "&amp;",
                        )
                        .replace(
                            "<",
                            "&lt;",
                        )
                        .replace(
                            ">",
                            "&gt;",
                        )
                        .replace(
                            "\n",
                            "<br/>",
                        )
                    ),
                    body_style,
                )
            )

            story.append(
                Spacer(
                    1,
                    8,
                )
            )
    else:
        story.append(
            Paragraph(
                "No verification logs available.",
                body_style,
            )
        )

    try:
        document.build(
            story
        )

    except Exception as error:
        raise PDFReportError(
            "Unable to generate PDF report"
        ) from error

    return str(
        pdf_path.resolve()
    )