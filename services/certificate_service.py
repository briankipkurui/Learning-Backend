import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
import tempfile
import os
from services.aws_s3_service import S3Service

class CertificateGenerationService:
    def __init__(self, s3_service: S3Service):
        project_root = os.path.dirname(os.path.dirname(__file__))
        self.template_path = os.path.join(project_root, 'templates', 'certificate_template.png')
        self.s3_service = s3_service

    def generate_qr_code(self, data: str) -> BytesIO:
        """
        Generate a QR code image from provided data.
        
        Args:
            data: Data to encode in QR code (typically a verification URL)
        
        Returns:
            BytesIO: QR code image as PIL Image object
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        byte_io = BytesIO()
        img.save(byte_io, format='PNG')
        byte_io.seek(0)
        return img

    def generate_certificate(
            self, 
            user_name: str, 
            course_title: str, 
            public_url: str
        ) -> BytesIO:
        """
        Generate a PDF certificate with user details and verification QR code.
        
        Args:
            user_name: Name of the certificate recipient
            course_title: Title of the completed course
            public_url: URL for certificate verification (embedded in QR code)
        
        Returns:
            BytesIO: Generated PDF certificate as buffer
        """
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        pdf.drawImage(self.template_path, 0, 0, width=width, height=height)
        pdf.setFont("Helvetica", 24)
        pdf.drawCentredString(width/2, height-330, user_name)

        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(width/2, height-380, course_title)

        pdf.setFont("Helvetica", 10)
        date_str = datetime.now().strftime("%B %d, %Y")
        pdf.drawCentredString(width/2, height-400, f"on {date_str}")

        # Add QR code to PDF (bottom right corner)
        qr_size = 100
        qr_x = width - 150
        qr_y = 50

        qr_code_img = self.generate_qr_code(public_url)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            qr_code_img.save(tmp_file.name)
            temp_qr_path = tmp_file.name

        pdf.drawImage(temp_qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
        
        os.unlink(temp_qr_path)

        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(qr_x + qr_size/2, qr_y - 10, "Scan to verify")

        pdf.save()
        buffer.seek(0)
        return buffer

    def upload_certificate_to_s3(self, certificate_buffer: BytesIO, user_name: str, course_title: str) -> str:
        """
        Upload the generated certificate PDF to S3 and return the public URL.
        
        Args:
            certificate_buffer: The PDF certificate as a BytesIO buffer
            user_name: Name of the certificate recipient
            course_title: Title of the completed course
            
        Returns:
            str: The public S3 URL of the uploaded certificate
        """
        try:
            # Create a sanitized filename
            sanitized_user = "".join(c for c in user_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            sanitized_course = "".join(c for c in course_title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            
            # Generate filename for the certificate
            filename = f"{sanitized_user}_{sanitized_course}.pdf"
            
            # Upload to S3 using the existing upload_file method
            result = self.s3_service.upload_file(
                file=certificate_buffer.getvalue(),  # Get bytes from BytesIO
                file_name=filename,
                folder_path="certificates",
                mime_type="application/pdf",
                metadata={
                    "user_name": user_name,
                    "course_title": course_title,
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            if result.get("success"):
                return result.get("url")
            else:
                raise Exception(f"Failed to upload certificate to S3: {result.get('message')}")
                
        except Exception as e:
            raise Exception(f"Error uploading certificate to S3: {str(e)}")

    def generate_and_upload_certificate(self, user_name: str, course_title: str, verification_url: str) -> tuple[BytesIO, str]:
        """
        Generate a certificate and upload it to S3 in one operation.
        
        Args:
            user_name: Name of the certificate recipient
            course_title: Title of the completed course
            verification_url: URL for certificate verification (used in QR code)
            
        Returns:
            tuple: (certificate_buffer, s3_url) - The PDF buffer and S3 URL
        """
        try:
            # Generate the certificate PDF
            certificate_buffer = self.generate_certificate(
                user_name=user_name,
                course_title=course_title,
                public_url=verification_url
            )
            
            # Upload to S3
            s3_url = self.upload_certificate_to_s3(
                certificate_buffer=certificate_buffer,
                user_name=user_name,
                course_title=course_title
            )
            
            certificate_buffer.seek(0)
            
            return certificate_buffer, s3_url
            
        except Exception as e:
            raise Exception(f"Error generating and uploading certificate: {str(e)}")
