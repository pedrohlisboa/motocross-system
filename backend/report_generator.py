"""
Report Generation Module
Exports race results to PDF, Excel, and CSV formats
"""
from typing import List, Dict
from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Event, Result, Rider, Lap


class ReportGenerator:
    """Generate reports in various formats"""

    def __init__(self, db: Session):
        self.db = db

    def generate_pdf(self, event_id: int) -> BytesIO:
        """Generate PDF report for an event"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        
        # Title
        title = Paragraph(f"Race Results - {event.name}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Event info
        info_text = f"""
        <b>Race Mode:</b> {event.race_mode.value}<br/>
        <b>Race Type:</b> {event.race_type.value}<br/>
        <b>Start Time:</b> {event.start_time.strftime('%Y-%m-%d %H:%M:%S') if event.start_time else 'N/A'}<br/>
        <b>End Time:</b> {event.end_time.strftime('%Y-%m-%d %H:%M:%S') if event.end_time else 'N/A'}
        """
        info = Paragraph(info_text, styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Results table
        results_heading = Paragraph("Final Results", heading_style)
        elements.append(results_heading)
        elements.append(Spacer(1, 0.1 * inch))
        
        # Get results
        results = self.db.query(Result, Rider).join(
            Rider, Result.rider_id == Rider.id
        ).filter(
            Result.event_id == event_id
        ).order_by(Result.position).all()
        
        # Create table data
        table_data = [['Pos', 'Number', 'Rider', 'Team', 'Category', 'Laps', 'Total Time', 'Best Lap']]
        
        for result, rider in results:
            table_data.append([
                str(result.position or '-'),
                str(rider.number),
                rider.name,
                rider.team or '-',
                rider.category,
                str(result.total_laps),
                self._format_time(result.total_time),
                self._format_time(result.best_lap_time)
            ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_excel(self, event_id: int) -> BytesIO:
        """Generate Excel report for an event"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Create Excel writer
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Results sheet
            results_data = self._get_results_data(event_id)
            df_results = pd.DataFrame(results_data)
            df_results.to_excel(writer, sheet_name='Results', index=False)
            
            # Lap times sheet
            lap_data = self._get_lap_data(event_id)
            if lap_data:
                df_laps = pd.DataFrame(lap_data)
                df_laps.to_excel(writer, sheet_name='Lap Times', index=False)
            
            # Event info sheet
            event_info = {
                'Event Name': [event.name],
                'Description': [event.description or ''],
                'Race Mode': [event.race_mode.value],
                'Race Type': [event.race_type.value],
                'Start Time': [event.start_time.strftime('%Y-%m-%d %H:%M:%S') if event.start_time else ''],
                'End Time': [event.end_time.strftime('%Y-%m-%d %H:%M:%S') if event.end_time else '']
            }
            df_info = pd.DataFrame(event_info)
            df_info.to_excel(writer, sheet_name='Event Info', index=False)
        
        buffer.seek(0)
        return buffer

    def generate_csv(self, event_id: int) -> BytesIO:
        """Generate CSV report for an event"""
        results_data = self._get_results_data(event_id)
        df = pd.DataFrame(results_data)
        
        buffer = BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer

    def _get_results_data(self, event_id: int) -> List[Dict]:
        """Get results data for export"""
        results = self.db.query(Result, Rider).join(
            Rider, Result.rider_id == Rider.id
        ).filter(
            Result.event_id == event_id
        ).order_by(Result.position).all()
        
        data = []
        for result, rider in results:
            data.append({
                'Position': result.position or '-',
                'Number': rider.number,
                'Rider Name': rider.name,
                'Team': rider.team or '-',
                'Category': rider.category,
                'Total Laps': result.total_laps,
                'Total Time': self._format_time(result.total_time),
                'Best Lap Time': self._format_time(result.best_lap_time),
                'Average Lap Time': self._format_time(result.average_lap_time),
                'Status': result.status or '-'
            })
        
        return data

    def _get_lap_data(self, event_id: int) -> List[Dict]:
        """Get lap times data for export"""
        laps = self.db.query(Lap, Rider).join(
            Rider, Lap.rider_id == Rider.id
        ).filter(
            Lap.event_id == event_id
        ).order_by(Lap.rider_id, Lap.lap_number).all()
        
        data = []
        for lap, rider in laps:
            data.append({
                'Rider Number': rider.number,
                'Rider Name': rider.name,
                'Lap Number': lap.lap_number,
                'Lap Time': self._format_time(lap.lap_time),
                'Total Time': self._format_time(lap.total_time),
                'Timestamp': lap.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            })
        
        return data

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS.mmm"""
        if seconds is None:
            return '-'
        
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"
