import io
import time
import secrets
from datetime import datetime
from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app.config import settings
from app.models.certificate import Certificate
from app.models.user import User
from app.models.course import Course
from app.services.storage_service import storage_service
from app.utils.url_shortener import create_short_url
from app.utils.date_formatter import format_date_with_ordinal, get_date_parts_for_superscript


class CertificateService:
    """Service for generating and managing certificates."""
    
    # Page dimensions (matching template: 185.669 x 262.615 cm)
    # 1 cm = 28.3465 points
    PAGE_WIDTH = 5263  # 185.669 cm * 28.3465 points/cm
    PAGE_HEIGHT = 7444  # 262.615 cm * 28.3465 points/cm
    
    # Student name positioning (centered horizontally)
    # From Inkscape: X=42.870 cm, Y=98.807 cm, W=100 cm, H=12 cm
    STUDENT_NAME_Y = 4400  # (262.615 - 98.807 - 12) * 28.3465 = bottom of field
    STUDENT_NAME_FONT = "Cinzel-SemiBold"
    STUDENT_NAME_FONT_SIZE = 200
    STUDENT_NAME_MAX_WIDTH = 2834  # 100 cm * 28.3465 points/cm
    
    # Issue date positioning (left-aligned)
    # From Inkscape: X=67.870 cm, Y=146.268 cm, W=50 cm, H=10 cm
    ISSUE_DATE_X = 1924  # 67.870 cm * 28.3465 points/cm
    ISSUE_DATE_Y = 3130  # (262.615 - 146.268 - 10) * 28.3465 = bottom of field
    ISSUE_DATE_FONT = "Cinzel-SemiBold"
    ISSUE_DATE_FONT_SIZE = 96
    
    # Certification ID positioning (left-aligned)
    # From Inkscape: X=67.870 cm, Y=165.031 cm, W=50 cm, H=10 cm
    CERT_ID_X = 1924  # 67.870 cm * 28.3465 points/cm
    CERT_ID_Y = 2600  # (262.615 - 165.031 - 10) * 28.3465 = bottom of field
    CERT_ID_FONT = "Cinzel-SemiBold"
    CERT_ID_FONT_SIZE = 96
    
    # Verification URL positioning (left-aligned)
    # From Inkscape: X=67.870 cm, Y=181.114 cm, W=50 cm, H=10 cm
    VERIFY_URL_X = 1924  # 67.870 cm * 28.3465 points/cm
    VERIFY_URL_Y = 2172  # (262.615 - 181.114 - 10) * 28.3465 = bottom of field
    VERIFY_URL_FONT = "JetBrainsMono-Regular"
    VERIFY_URL_FONT_SIZE = 72
    
    def __init__(self):
        # Use absolute path to ensure template is found regardless of working directory
        import os
        # __file__ is in backend/app/services/certificate_service.py
        # Go up 2 levels to get to backend/, then into assets
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_path = os.path.join(backend_dir, "assets", "certificate_template.pdf")
        self.backend_url = settings.backend_url
        self.template_available = False
        self.fonts_available = False
        self._fonts_initialized = False  # Track if fonts have been loaded
        
        # Verify template exists on initialization
        if os.path.exists(self.template_path):
            self.template_available = True
            print(f"✓ Certificate template loaded: {self.template_path}")
        else:
            self.template_available = False
            print(f"✗ WARNING: Certificate template not found at: {self.template_path}")
            print(f"  Certificates will be generated using simple fallback template.")
    
    def _register_fonts(self):
        """Register custom fonts for use in PDF generation. Called lazily on first use."""
        if self._fonts_initialized:
            return
        
        self._fonts_initialized = True
        import os
        # Get backend directory (same as template path calculation)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fonts_dir = os.path.join(backend_dir, "assets", "fonts")
        
        try:
            # Try to register Cinzel font
            cinzel_path = os.path.join(fonts_dir, "Cinzel-SemiBold.ttf")
            if os.path.exists(cinzel_path):
                pdfmetrics.registerFont(TTFont('Cinzel-SemiBold', cinzel_path))
                self.fonts_available = True
            else:
                raise FileNotFoundError(f"Font file not found: {cinzel_path}")
        except Exception:
            # Fallback to built-in serif font (no warning needed)
            self.STUDENT_NAME_FONT = "Times-Bold"
            self.ISSUE_DATE_FONT = "Times-Roman"
            self.CERT_ID_FONT = "Times-Roman"
        
        try:
            # Try to register JetBrainsMono font for URL
            jetbrains_path = os.path.join(fonts_dir, "JetBrainsMono-Regular.ttf")
            if os.path.exists(jetbrains_path):
                pdfmetrics.registerFont(TTFont('JetBrainsMono-Regular', jetbrains_path))
            else:
                raise FileNotFoundError(f"Font file not found: {jetbrains_path}")
        except Exception:
            # Fallback to built-in monospace font (no warning needed)
            self.VERIFY_URL_FONT = "Courier"
        
    def generate_certification_id(self) -> str:
        """
        Generate a unique certification ID.
        Format: CERT-{timestamp}-{random}
        """
        timestamp = int(time.time())
        random_part = secrets.token_hex(4).upper()
        return f"CERT-{timestamp}-{random_part}"
    
    def create_text_overlay(
        self,
        student_name: str,
        issue_date: str,
        cert_id: str,
        verify_url: str,
        page_size=None
    ) -> io.BytesIO:
        """
        Create a PDF overlay with text for the certificate.
        
        Args:
            student_name: Name of the student
            issue_date: Date of certificate issuance
            cert_id: Certification ID
            verify_url: URL for certificate verification
            page_size: Page size (default: template size)
            
        Returns:
            BytesIO object containing the overlay PDF
        """
        # Lazy load fonts on first use
        self._register_fonts()
        
        if page_size is None:
            page_size = (self.PAGE_WIDTH, self.PAGE_HEIGHT)
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=page_size)
        
        # Subtask 2.1: Implement dynamic font sizing for student name
        # Calculate text width and adjust font size if needed
        font_size = self.STUDENT_NAME_FONT_SIZE
        text_width = can.stringWidth(student_name, self.STUDENT_NAME_FONT, font_size)
        
        # If name exceeds max width, reduce font size proportionally
        if text_width > self.STUDENT_NAME_MAX_WIDTH:
            font_size = int((self.STUDENT_NAME_MAX_WIDTH / text_width) * font_size)
            # Set minimum font size to 16pt to prevent unreadable text
            font_size = max(font_size, 16)
            text_width = can.stringWidth(student_name, self.STUDENT_NAME_FONT, font_size)
        
        # Subtask 2.2: Update student name rendering with centered positioning
        # Remove "This certificate is awarded to" text (not included)
        # Use STUDENT_NAME_FONT and calculated font size
        can.setFont(self.STUDENT_NAME_FONT, font_size)
        # Calculate horizontal center position: (PAGE_WIDTH - text_width) / 2
        name_x = (self.PAGE_WIDTH - text_width) / 2
        # Position at STUDENT_NAME_Y from bottom
        can.drawString(name_x, self.STUDENT_NAME_Y, student_name)
        
        print(f"Positioning student name '{student_name}' at ({name_x}, {self.STUDENT_NAME_Y}) with font size {font_size}")
        
        # Subtask 2.3: Update issue date rendering with fixed positioning and superscript ordinal
        # Parse the date to render with superscript ordinal suffix
        # Expected format: "November 17th, 2025" -> render "th" as superscript
        import re
        date_match = re.match(r'(\w+)\s+(\d+)(st|nd|rd|th),\s+(\d+)', issue_date)
        
        if date_match:
            month, day, suffix, year = date_match.groups()
            
            # Render the date with superscript ordinal
            can.setFont(self.ISSUE_DATE_FONT, self.ISSUE_DATE_FONT_SIZE)
            
            # Calculate positions for each part
            x_pos = self.ISSUE_DATE_X
            y_pos = self.ISSUE_DATE_Y
            
            # Draw month and space
            month_text = f"{month} "
            can.drawString(x_pos, y_pos, month_text)
            x_pos += can.stringWidth(month_text, self.ISSUE_DATE_FONT, self.ISSUE_DATE_FONT_SIZE)
            
            # Draw day number
            can.drawString(x_pos, y_pos, day)
            x_pos += can.stringWidth(day, self.ISSUE_DATE_FONT, self.ISSUE_DATE_FONT_SIZE)
            
            # Draw ordinal suffix as superscript (smaller and raised)
            superscript_size = self.ISSUE_DATE_FONT_SIZE * 0.6  # 60% of normal size
            superscript_raise = self.ISSUE_DATE_FONT_SIZE * 0.4  # Raise by 40% of font size
            can.setFont(self.ISSUE_DATE_FONT, superscript_size)
            can.drawString(x_pos, y_pos + superscript_raise, suffix)
            x_pos += can.stringWidth(suffix, self.ISSUE_DATE_FONT, superscript_size)
            
            # Draw comma, space, and year
            can.setFont(self.ISSUE_DATE_FONT, self.ISSUE_DATE_FONT_SIZE)
            year_text = f", {year}"
            can.drawString(x_pos, y_pos, year_text)
        else:
            # Fallback: render as-is if format doesn't match
            can.setFont(self.ISSUE_DATE_FONT, self.ISSUE_DATE_FONT_SIZE)
            can.drawString(self.ISSUE_DATE_X, self.ISSUE_DATE_Y, issue_date)
        
        # Subtask 2.4: Update certification ID rendering with fixed positioning
        # Remove "Certificate ID:" prefix (template already has label)
        can.setFont(self.CERT_ID_FONT, self.CERT_ID_FONT_SIZE)
        # Position at fixed coordinates (CERT_ID_X, CERT_ID_Y)
        can.drawString(self.CERT_ID_X, self.CERT_ID_Y, cert_id)
        
        # Subtask 2.5: Update verification URL rendering with fixed positioning
        # Remove "Verify at:" prefix (template already has text)
        can.setFont(self.VERIFY_URL_FONT, self.VERIFY_URL_FONT_SIZE)
        # Position at fixed coordinates (VERIFY_URL_X, VERIFY_URL_Y)
        can.drawString(self.VERIFY_URL_X, self.VERIFY_URL_Y, verify_url)
        
        can.save()
        packet.seek(0)
        return packet
    
    def create_simple_certificate(
        self,
        student_name: str,
        course_title: str,
        issue_date: str,
        cert_id: str,
        verify_url: str
    ) -> io.BytesIO:
        """
        Create a simple certificate without a template.
        Used as fallback if template is not available.
        
        Args:
            student_name: Name of the student
            course_title: Title of the course
            issue_date: Date of certificate issuance
            cert_id: Certification ID
            verify_url: URL for certificate verification
            
        Returns:
            BytesIO object containing the certificate PDF
        """
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        width, height = letter
        
        # Draw border
        can.setLineWidth(3)
        can.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
        
        # Draw inner border
        can.setLineWidth(1)
        can.rect(0.75 * inch, 0.75 * inch, width - 1.5 * inch, height - 1.5 * inch)
        
        # Title
        can.setFont("Helvetica-Bold", 36)
        title = "CERTIFICATE OF COMPLETION"
        title_width = can.stringWidth(title, "Helvetica-Bold", 36)
        can.drawString((width - title_width) / 2, height - 2 * inch, title)
        
        # Subtitle
        can.setFont("Helvetica", 16)
        subtitle = "This is to certify that"
        subtitle_width = can.stringWidth(subtitle, "Helvetica", 16)
        can.drawString((width - subtitle_width) / 2, height - 2.8 * inch, subtitle)
        
        # Student name
        can.setFont("Helvetica-Bold", 32)
        name_width = can.stringWidth(student_name, "Helvetica-Bold", 32)
        can.drawString((width - name_width) / 2, height - 3.8 * inch, student_name)
        
        # Draw line under name
        can.setLineWidth(1)
        can.line(2 * inch, height - 4 * inch, width - 2 * inch, height - 4 * inch)
        
        # Course completion text
        can.setFont("Helvetica", 16)
        completion_text = "has successfully completed the course"
        completion_width = can.stringWidth(completion_text, "Helvetica", 16)
        can.drawString((width - completion_width) / 2, height - 4.8 * inch, completion_text)
        
        # Course title
        can.setFont("Helvetica-Bold", 20)
        course_width = can.stringWidth(course_title, "Helvetica-Bold", 20)
        can.drawString((width - course_width) / 2, height - 5.5 * inch, course_title)
        
        # Issue date
        can.setFont("Helvetica", 14)
        date_text = f"Issued on {issue_date}"
        date_width = can.stringWidth(date_text, "Helvetica", 14)
        can.drawString((width - date_width) / 2, height - 6.5 * inch, date_text)
        
        # Certification ID
        can.setFont("Helvetica", 12)
        can.drawString(1 * inch, 1.2 * inch, f"Certificate ID: {cert_id}")
        
        # Verification URL
        can.setFont("Helvetica", 10)
        url_text = f"Verify at: {verify_url}"
        url_width = can.stringWidth(url_text, "Helvetica", 10)
        can.drawString((width - url_width) / 2, 0.8 * inch, url_text)
        
        can.save()
        packet.seek(0)
        return packet
    
    async def generate_certificate(
        self,
        db: Session,
        user: User,
        course: Course
    ) -> Optional[Certificate]:
        """
        Generate a certificate for a user who completed the course.
        
        Args:
            db: Database session
            user: User object
            course: Course object
            
        Returns:
            Certificate object or None if generation fails
        """
        try:
            # Check if certificate already exists
            existing_cert = db.query(Certificate).filter(
                Certificate.user_id == user.id
            ).first()
            
            if existing_cert:
                return existing_cert
            
            # Generate certification ID
            cert_id = self.generate_certification_id()
            
            # Format issue date with ordinal suffix (e.g., "November 17th, 2025")
            issue_date = format_date_with_ordinal(datetime.now())
            
            # Create shortened verification URL
            verify_url = create_short_url(settings.frontend_url, cert_id)
            
            # Lazy load fonts before generating certificate
            self._register_fonts()
            
            # Try to use template if available, otherwise create simple certificate
            import os
            if not os.path.exists(self.template_path):
                print(f"ERROR: Certificate template not found at: {self.template_path}")
                print(f"Current working directory: {os.getcwd()}")
                print(f"Backend directory: {os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}")
                print("Falling back to simple certificate without template")
                
                # Create simple certificate without template
                output_packet = self.create_simple_certificate(
                    student_name=user.full_name,
                    course_title=course.title,
                    issue_date=issue_date,
                    cert_id=cert_id,
                    verify_url=verify_url
                )
            else:
                try:
                    print(f"Using certificate template from: {self.template_path}")
                    
                    # Load template
                    template = PdfReader(self.template_path)
                    
                    # Create text overlay
                    overlay_packet = self.create_text_overlay(
                        student_name=user.full_name,
                        issue_date=issue_date,
                        cert_id=cert_id,
                        verify_url=verify_url
                    )
                    
                    # Merge overlay with template
                    overlay = PdfReader(overlay_packet)
                    output = PdfWriter()
                    
                    page = template.pages[0]
                    page.merge_page(overlay.pages[0])
                    output.add_page(page)
                    
                    # Write to BytesIO
                    output_packet = io.BytesIO()
                    output.write(output_packet)
                    output_packet.seek(0)
                    
                    print(f"Successfully generated certificate using template for {user.full_name}")
                    
                except Exception as e:
                    print(f"ERROR: Failed to generate certificate with template: {e}")
                    import traceback
                    traceback.print_exc()
                    print("Falling back to simple certificate without template")
                    
                    # Create simple certificate without template
                    output_packet = self.create_simple_certificate(
                        student_name=user.full_name,
                        course_title=course.title,
                        issue_date=issue_date,
                        cert_id=cert_id,
                        verify_url=verify_url
                    )
            
            # Upload to Vercel Blob
            filename = f"certificates/{cert_id}.pdf"
            try:
                print(f"Uploading certificate to storage: {filename}")
                certificate_url = await storage_service.upload_file(
                    file_data=output_packet.read(),
                    filename=filename,
                    content_type="application/pdf"
                )
                
                if not certificate_url:
                    # Fallback: use a placeholder URL if upload fails
                    certificate_url = f"{self.backend_url}/certificates/{cert_id}.pdf"
                    print(f"Warning: Certificate upload failed. Using placeholder URL: {certificate_url}")
                else:
                    print(f"Certificate uploaded successfully: {certificate_url}")
            except Exception as upload_error:
                # If upload fails, use placeholder URL and continue
                certificate_url = f"{self.backend_url}/certificates/{cert_id}.pdf"
                print(f"Error uploading certificate: {upload_error}. Using placeholder URL: {certificate_url}")
            
            # Create certificate record in database
            print(f"Creating certificate record in database for user {user.id}")
            certificate = Certificate(
                user_id=user.id,
                certification_id=cert_id,
                certificate_url=certificate_url,
                student_name=user.full_name,
                course_title=course.title,
                issued_at=datetime.now()
            )
            
            db.add(certificate)
            print(f"Committing certificate to database...")
            db.commit()
            print(f"Certificate committed successfully")
            db.refresh(certificate)
            print(f"Certificate created with ID: {certificate.certification_id}")
            
            return certificate
            
        except Exception as e:
            print(f"Error generating certificate: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return None
    
    def get_user_certificate(self, db: Session, user_id: str) -> Optional[Certificate]:
        """
        Get certificate for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Certificate object or None if not found
        """
        return db.query(Certificate).filter(
            Certificate.user_id == user_id
        ).first()
    
    def verify_certificate(self, db: Session, cert_id: str) -> Optional[Certificate]:
        """
        Verify a certificate by its certification ID.
        
        Args:
            db: Database session
            cert_id: Certification ID
            
        Returns:
            Certificate object or None if not found
        """
        return db.query(Certificate).filter(
            Certificate.certification_id == cert_id
        ).first()
    
    def lookup_by_short_code(self, db: Session, short_code: str) -> Optional[Certificate]:
        """
        Look up a certificate by its short code (first 6 chars of hex part).
        
        Args:
            db: Database session
            short_code: Short code (e.g., "5A5A93")
            
        Returns:
            Certificate object or None if not found
        """
        # Short code is the first 6 characters of the hex part
        # Cert ID format: CERT-{timestamp}-{hex}
        # We need to find certs where the hex part starts with the short code
        certificates = db.query(Certificate).all()
        
        for cert in certificates:
            # Extract hex part from certification_id
            parts = cert.certification_id.split('-')
            if len(parts) >= 3:
                hex_part = parts[2]
                if hex_part.startswith(short_code):
                    return cert
        
        return None


# Singleton instance
certificate_service = CertificateService()
