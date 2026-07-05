import asyncio
from typing import List, Optional, Sequence
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.meetings import Meeting, MeetingRecording, MeetingTranscript, MeetingAIAnalysis, MeetingInvitation
from app.models.user import User
from app.modules.meetings.enums import AIAnalysisStatus
from app.modules.meetings.repository import MeetingRepository, MeetingAIAnalysisRepository


class MeetingCompletionService:
    def __init__(self, session: AsyncSession):
        self.meeting_repo = MeetingRepository(session)
        self.ai_repo = MeetingAIAnalysisRepository(session)

    async def send_completion_email(self, meeting_id: UUID) -> None:
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found for completion email")
            return

        host = await self.meeting_repo.get_user_by_id(meeting.host_id)
        invitations = await self.meeting_repo.list_invitations(meeting_id)
        participants = await self.meeting_repo.get_participants_list(meeting_id, active_only=False)
        recordings = await self.meeting_repo.list_recordings_by_meeting(meeting_id)
        transcripts = await self.meeting_repo.list_transcripts_by_meeting(meeting_id)
        analysis = await self.ai_repo.get_by_meeting_id(meeting_id)

        recipients = await self._build_recipient_list(host, invitations, participants)

        if not recipients:
            logger.warning(f"No recipients found for meeting {meeting_id} completion email")
            return

        context = self._build_email_context(meeting, recordings, transcripts, analysis)
        attachments = await self._build_attachments(transcripts, recordings)
        self._dispatch_emails(context, recipients, attachments)

        logger.info(f"Completion email dispatched for meeting {meeting_id} to {len(recipients)} recipient(s)")

    async def _build_recipient_list(
        self,
        host: Optional[User],
        invitations: Sequence[MeetingInvitation],
        participants: Sequence,
    ) -> List[str]:
        recipients: List[str] = []

        if host and host.email:
            recipients.append(host.email)

        for inv in invitations:
            if inv.email and inv.email not in recipients:
                recipients.append(inv.email)

        for p in participants:
            if p.user_id:
                user = await self.meeting_repo.get_user_by_id(p.user_id)
                if user and user.email and user.email not in recipients:
                    recipients.append(user.email)
            elif p.guest_email and p.guest_email not in recipients:
                recipients.append(p.guest_email)

        return recipients

    def _build_email_context(
        self,
        meeting: Meeting,
        recordings: Sequence[MeetingRecording],
        transcripts: Sequence[MeetingTranscript],
        analysis: Optional[MeetingAIAnalysis],
    ) -> dict:
        context = {
            "meeting_title": meeting.title,
            "meeting_date": meeting.ended_at or meeting.created_at,
            "frontend_url": settings.FRONTEND_URL,
            "meeting_id": str(meeting.id),
        }

        if recordings:
            context["has_recording"] = True
            context["recordings"] = [
                {"filename": r.filename, "size": r.size, "duration": r.duration}
                for r in recordings
            ]
        else:
            context["has_recording"] = False

        if transcripts:
            context["has_transcript"] = True
            context["transcripts"] = [
                {"filename": t.filename, "size": t.size}
                for t in transcripts
            ]
        else:
            context["has_transcript"] = False

        if analysis and analysis.status == AIAnalysisStatus.COMPLETED:
            context["has_ai_analysis"] = True
            context["ai_summary"] = analysis.summary
            context["ai_agenda_coverage"] = analysis.agenda_coverage_percentage
            context["ai_covered_points"] = analysis.covered_points
            context["ai_out_of_agenda_points"] = analysis.out_of_agenda_points
            context["ai_suggested_tasks"] = analysis.suggested_tasks
        else:
            context["has_ai_analysis"] = False

        return context

    async def _build_attachments(
        self,
        transcripts: Sequence[MeetingTranscript],
        recordings: Sequence[MeetingRecording],
    ) -> list:
        attachments: list = []

        for tx in transcripts:
            try:
                def _read_bytes():
                    with open(tx.storage_path, 'rb') as f:
                        return f.read()
                content = await asyncio.to_thread(_read_bytes)
                attachments.append({
                    "filename": tx.filename,
                    "content": content,
                    "content_type": tx.content_type,
                })
            except Exception as e:
                logger.error(f"Failed to read transcript {tx.storage_path} for email attachment: {e}")

        for rec in recordings:
            try:
                def _read_bytes():
                    with open(rec.storage_path, 'rb') as f:
                        return f.read()
                content = await asyncio.to_thread(_read_bytes)
                attachments.append({
                    "filename": rec.filename,
                    "content": content,
                    "content_type": rec.content_type,
                })
            except Exception as e:
                logger.error(f"Failed to read recording {rec.storage_path} for email attachment: {e}")

        return attachments

    def _dispatch_emails(self, context: dict, recipients: List[str], attachments: list | None = None) -> None:
        from app.workers.tasks import send_html_email

        subject = f"Meeting Completed: {context['meeting_title']}"
        text_body = self._render_text_body(context)

        for recipient in recipients:
            try:
                send_html_email.delay(
                    recipient=recipient,
                    subject=subject,
                    html_body="",
                    text_body=text_body,
                    attachments=attachments or [],
                )
            except Exception as e:
                logger.error(f"Failed to send completion email to {recipient} for meeting {context['meeting_id']}: {e}")

    def _render_text_body(self, context: dict) -> str:
        lines = [f"Meeting: {context['meeting_title']}"]
        meeting_date = context["meeting_date"]
        if meeting_date:
            if isinstance(meeting_date, datetime):
                lines.append(f"Date: {meeting_date.strftime('%Y-%m-%d %H:%M')}")
            else:
                lines.append(f"Date: {meeting_date}")
        lines.append("")

        if context["has_recording"]:
            lines.append("Recording:")
            for rec in context["recordings"]:
                duration_str = f" ({rec['duration']}s)" if rec.get("duration") else ""
                lines.append(f"  - {rec['filename']}{duration_str}")
            lines.append("")

        if context["has_transcript"]:
            lines.append("Transcript:")
            for tx in context["transcripts"]:
                lines.append(f"  - {tx['filename']}")
            lines.append("")

        if context["has_ai_analysis"]:
            lines.append("AI Analysis:")
            if context.get("ai_summary"):
                lines.append(f"  Summary: {context['ai_summary']}")
            if context.get("ai_agenda_coverage") is not None:
                lines.append(f"  Agenda Coverage: {context['ai_agenda_coverage']}%")
            if context.get("ai_covered_points"):
                lines.append("  Covered Points:")
                for point in context["ai_covered_points"]:
                    lines.append(f"    - {point}")
            if context.get("ai_out_of_agenda_points"):
                lines.append("  Out of Agenda Points:")
                for point in context["ai_out_of_agenda_points"]:
                    lines.append(f"    - {point}")
            if context.get("ai_suggested_tasks"):
                lines.append("  Suggested Tasks:")
                for task in context["ai_suggested_tasks"]:
                    lines.append(f"    - {task.get('title', '')}: {task.get('description', '')} (Priority: {task.get('priority', 'N/A')})")
            lines.append("")

        lines.append(f"View meeting: {context['frontend_url']}/meetings/{context['meeting_id']}")
        return "\n".join(lines)
