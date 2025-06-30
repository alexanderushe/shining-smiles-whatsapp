# app.py
from dotenv import load_dotenv
import os
load_dotenv()
from flask import Flask, request, Response, send_from_directory
from src.utils.logger import setup_logger
from src.utils.scheduler import init_scheduler
from src.services.payment_service import check_new_payments
from src.services.reminder_service import send_balance_reminders
from src.utils.database import init_db, StudentContact, GatePass
from src.utils.whatsapp import send_whatsapp_message
from config import get_config
import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import qrcode
from PIL import Image as PILImage
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import requests  # Added import
import boto3

app = Flask(__name__)
app.config.from_object(get_config())
logger = setup_logger(__name__)
init_scheduler()

# Term end dates for 2025
TERM_END_DATES = {
    "2025-1": datetime.datetime(2025, 3, 31),
    "2025-2": datetime.datetime(2025, 7, 31),
    "2025-3": datetime.datetime(2025, 11, 30)
}

# Twilio client for media messages
twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

# AWS S3 client
s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
bucket_name = 'shining-smiles-gatepasses'  # Replace with your S3 bucket name

@app.route("/trigger-payments", methods=["POST"])
def trigger_payments():
    """Manual trigger for checking new payments (for testing)."""
    try:
        student_id = request.args.get("student_id_number", "SSC20257279")
        term = request.args.get("term", "2025-1")
        phone_number = request.args.get("phone_number")
        logger.debug(f"Triggering payment check for student_id={student_id}, term={term}, phone_number={phone_number}")
        result = check_new_payments(student_id, term, phone_number)
        if "error" in result:
            logger.error(f"Error in check_new_payments: {result['error']}")
            return {"status": "Payment check failed", "error": result["error"]}, 400
        logger.info(f"Payment check triggered for {student_id}")
        return {"status": "Payment check triggered", "result": result}, 200
    except Exception as e:
        logger.error(f"Error triggering payments: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/trigger-reminders", methods=["POST"])
def trigger_reminders():
    """Manual trigger for balance reminders (for testing)."""
    try:
        student_id = request.args.get("student_id_number", "SSC20257279")
        term = request.args.get("term", "2025-1")
        phone_number = request.args.get("phone_number")
        logger.debug(f"Triggering reminder for student_id={student_id}, term={term}, phone_number={phone_number}")
        result = send_balance_reminders(student_id, term, phone_number)
        if "error" in result:
            logger.error(f"Error in send_balance_reminders: {result['error']}")
            return {"status": "Reminder failed", "error": result["error"]}, 400
        logger.info(f"Balance reminder triggered for {student_id}")
        return {"status": "Balance reminder triggered", "result": result}, 200
    except Exception as e:
        logger.error(f"Error triggering reminders: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/update-contact", methods=["POST"])
def update_contact():
    """Update or add a contact."""
    try:
        student_id = request.args.get("student_id")
        phone_number = request.args.get("phone_number")
        firstname = request.args.get("firstname")
        lastname = request.args.get("lastname")
        if not student_id or not phone_number:
            logger.error("Missing student_id or phone_number")
            return {"error": "student_id and phone_number required"}, 400
        session = init_db()
        if not phone_number.startswith("+"):
            phone_number = f"+263{phone_number.lstrip('0')}"
        contact = session.query(StudentContact).filter_by(student_id=student_id).first()
        if contact:
            contact.firstname = firstname or contact.firstname
            contact.lastname = lastname or contact.lastname
            contact.student_mobile = phone_number
            contact.guardian_mobile_number = phone_number if not contact.guardian_mobile_number else contact.guardian_mobile_number
            contact.preferred_phone_number = phone_number
            contact.last_updated = datetime.datetime.now(datetime.UTC)
            logger.info(f"Updated contact for {student_id}: {phone_number}")
        else:
            contact = StudentContact(
                student_id=student_id,
                firstname=firstname,
                lastname=lastname,
                student_mobile=phone_number,
                guardian_mobile_number=phone_number,
                preferred_phone_number=phone_number,
                last_updated=datetime.datetime.now(datetime.UTC)
            )
            session.add(contact)
            logger.info(f"Added contact for {student_id}: {phone_number}")
        session.commit()
        return {"status": "Contact updated"}, 200
    except Exception as e:
        logger.error(f"Error updating contact for {student_id}: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/get-student-profile", methods=["GET"])
def get_student_profile():
    """Retrieve student profile from database or SMS API."""
    try:
        student_id = request.args.get("student_id")
        if not student_id:
            logger.error("Missing student_id")
            return {"error": "student_id required"}, 400

        session = init_db()
        contact = session.query(StudentContact).filter_by(student_id=student_id).first()
        if contact:
            logger.info(f"Found profile for {student_id} in database")
            return {
                "status": "success",
                "profile": {
                    "student_id": contact.student_id,
                    "firstname": contact.firstname,
                    "lastname": contact.lastname,
                    "phone_number": contact.preferred_phone_number,
                    "last_updated": contact.last_updated.isoformat()
                }
            }, 200

        from src.api.sms_client import SMSClient
        try:
            client = SMSClient()
            profile = client.get_student_profile(student_id)
            profile_data = profile.get("data", {})
            firstname = profile_data.get("firstname")
            lastname = profile_data.get("lastname")
            student_mobile = profile_data.get("student_mobile")
            guardian_mobile = profile_data.get("guardian_mobile_number")
            if student_mobile and not student_mobile.startswith("+"):
                student_mobile = f"+263{student_mobile.lstrip('0')}"
            if guardian_mobile and not guardian_mobile.startswith("+"):
                guardian_mobile = f"+263{guardian_mobile.lstrip('0')}"
            preferred_phone = student_mobile or guardian_mobile
            if not preferred_phone:
                logger.error(f"No phone number in profile for {student_id}")
                return {"error": "No phone number in profile"}, 404

            contact = StudentContact(
                student_id=student_id,
                firstname=firstname,
                lastname=lastname,
                student_mobile=student_mobile,
                guardian_mobile_number=guardian_mobile,
                preferred_phone_number=preferred_phone,
                last_updated=datetime.datetime.now(datetime.UTC)
            )
            session.add(contact)
            session.commit()
            logger.info(f"Cached profile for {student_id} from API")
            return {
                "status": "success",
                "profile": {
                    "student_id": contact.student_id,
                    "firstname": contact.firstname,
                    "lastname": contact.lastname,
                    "phone_number": contact.preferred_phone_number,
                    "last_updated": contact.last_updated.isoformat()
                }
            }, 200
        except Exception as e:
            logger.error(f"Error fetching profile for {student_id} from API: {str(e)}")
            return {"error": f"Profile not found: {str(e)}"}, 404
    except Exception as e:
        logger.error(f"Error retrieving profile for {student_id}: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/generate-gatepass", methods=["POST"])
def generate_gatepass():
    """Generate and send gate pass as a PDF with logo, signature, QR code, and watermark."""
    try:
        student_id = request.args.get("student_id", "SSC20257279")
        term = request.args.get("term", "2025-1")
        payment_amount = float(request.args.get("payment_amount", 0))
        total_fees = float(request.args.get("total_fees", 1000))

        if not student_id or not term:
            logger.error("Missing student_id or term")
            return {"error": "student_id and term required"}, 400

        session = init_db()
        contact = session.query(StudentContact).filter_by(student_id=student_id).first()
        if not contact:
            logger.error(f"No contact found for {student_id}")
            return {"error": "No contact found"}, 404

        # Calculate payment percentage
        payment_percentage = (payment_amount / total_fees) * 100
        issued_date = datetime.datetime.now(datetime.UTC)
        expiry_date = None

        # Determine expiry date
        if payment_percentage >= 100:
            expiry_date = TERM_END_DATES.get(term, datetime.datetime(2025, 3, 31))
        elif payment_percentage >= 75:
            expiry_date = issued_date + datetime.timedelta(days=60)
        elif payment_percentage >= 50:
            expiry_date = issued_date + datetime.timedelta(days=30)
        else:
            logger.info(f"Payment {payment_percentage}% for {student_id} below 50%; no gate pass issued")
            return {"status": "No gate pass issued", "reason": "Payment below 50%"}, 200

        # Check existing gate pass
        existing_pass = session.query(GatePass).filter(
            GatePass.student_id == student_id,
            GatePass.expiry_date >= issued_date
        ).first()
        if existing_pass and existing_pass.payment_percentage >= payment_percentage:
            logger.info(f"Existing gate pass for {student_id} is valid until {existing_pass.expiry_date}")
            return {
                "status": "Gate pass not updated",
                "pass_id": existing_pass.pass_id,
                "expiry_date": existing_pass.expiry_date.isoformat(),
                "whatsapp_number": contact.preferred_phone_number
            }, 200

        # Generate unique pass ID
        pass_id = str(uuid.uuid4())

        # Create temporary directory for PDF and QR code
        os.makedirs("temp", exist_ok=True)
        pdf_path = f"temp/gatepass_{pass_id}.pdf"
        qr_path = f"temp/qr_{pass_id}.png"

        # Generate QR code
        qr_url = f"https://shining-smiles-app-809413c70177.herokuapp.com/verify-gatepass?pass_id={pass_id}&whatsapp_number={contact.preferred_phone_number}"
        logger.debug(f"Generating QR code for URL: {qr_url}")
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_path)
        if not os.path.exists(qr_path):
            logger.error("QR code generation failed")
            return {"error": "Failed to generate QR code"}, 500
        logger.debug(f"QR code saved to {qr_path}")

        # Generate PDF
        logger.debug(f"Generating PDF at {pdf_path}")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        bold_style = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12)
        normal_style = ParagraphStyle(name='Normal', parent=styles['Normal'], fontSize=12)

        # Add watermark (faint school logo in background)
        def add_watermark(canvas, doc):
            canvas.saveState()
            canvas.setFillAlpha(0.1)  # Faint opacity
            logo_path = "static/school_logo.png"
            if os.path.exists(logo_path):
                canvas.drawImage(logo_path, 150, 300, width=300, height=150, preserveAspectRatio=True, mask='auto')
            canvas.restoreState()

        doc.build = lambda flowables: SimpleDocTemplate.build(doc, flowables, onFirstPage=add_watermark)

        story = []

        # Header: Logo and Title
        logo_path = "static/school_logo.png"
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch, kind='proportional')
            title = Paragraph("SHINING SMILES GROUP OF SCHOOLS", ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, textColor=colors.darkblue))
            header_table = Table([[logo, title]], colWidths=[2.5*inch, 4*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ]))
            story.append(header_table)
        else:
            logger.warning("School logo not found at static/school_logo.png")
            story.append(Paragraph("SHINING SMILES GROUP OF SCHOOLS", ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, textColor=colors.darkblue)))

        story.append(Spacer(1, 0.5*inch))

        # Information table (bold titles, values next to them)
        data = [
            ["Student ID:", f"{student_id}"],
            ["Name:", f"{contact.firstname or 'N/A'} {contact.lastname or 'N/A'}"],
            ["Pass ID:", f"{pass_id}"],
            ["Issued:", f"{issued_date.strftime('%Y-%m-%d')}"],
            ["Expires:", f"{expiry_date.strftime('%Y-%m-%d')}"],
            ["Payment:", f"{payment_percentage:.1f}%"],
            ["Valid for:", f"{contact.preferred_phone_number}"]
        ]
        info_table = Table(data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 12),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkblue),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgoldenrodyellow),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))

        # QR code (centered)
        if os.path.exists(qr_path):
            logger.debug(f"Adding QR code from {qr_path}")
            qr_image = Image(qr_path, width=2*inch, height=2*inch, kind='proportional')
            qr_table = Table([[qr_image]], colWidths=[2*inch])
            qr_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            story.append(qr_table)
        else:
            logger.error("QR code file missing after generation")
            return {"error": "QR code file missing"}, 500

        # Signature
        signature_path = "static/signature.png"
        if os.path.exists(signature_path):
            logger.debug(f"Adding signature from {signature_path}")
            signature = Image(signature_path, width=2*inch, height=0.5*inch, kind='proportional')
            story.append(Spacer(1, 0.25*inch))
            story.append(Paragraph("Authorized Signature", normal_style))
            story.append(signature)
        else:
            logger.warning("Signature image not found at static/signature.png")
            story.append(Paragraph("Authorized Signature", normal_style))

        doc.build(story)
        if not os.path.exists(pdf_path):
            logger.error("PDF generation failed")
            return {"error": "Failed to generate PDF"}, 500
        logger.debug(f"PDF generated at {pdf_path}")

        # Upload to S3
        s3_key = f"gatepasses/gatepass_{pass_id}.pdf"
        s3.upload_file(pdf_path, bucket_name, s3_key, ExtraArgs={'ACL': 'public-read'})
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        logger.debug(f"Uploaded PDF to S3: {public_url}")

        # Save to database
        gate_pass = GatePass(
            student_id=student_id,
            pass_id=pass_id,
            issued_date=issued_date,
            expiry_date=expiry_date,
            payment_percentage=int(payment_percentage),
            whatsapp_number=contact.preferred_phone_number,
            last_updated=issued_date,
            pdf_path=s3_key,
            qr_path=qr_path
        )
        session.add(gate_pass)
        session.commit()

        # Send PDF via WhatsApp
        logger.debug(f"Sending PDF to WhatsApp: {public_url}")
        try:
            # Test URL accessibility
            response = requests.head(public_url, timeout=5)
            if response.status_code != 200:
                logger.error(f"Public URL inaccessible: {public_url}, status={response.status_code}")
                raise Exception(f"Public URL inaccessible: status={response.status_code}")

            message = twilio_client.messages.create(
                from_=f"whatsapp:{app.config['TWILIO_WHATSAPP_NUMBER']}",
                body="Your gate pass is attached. This pass is valid only for your WhatsApp number. Do not share.",
                media_url=[public_url],
                to=f"whatsapp:{contact.preferred_phone_number}",
                status_callback=f"https://shining-smiles-app-809413c70177.herokuapp.com//message-status"
            )
            logger.info(f"Gate pass PDF sent for {student_id} to {contact.preferred_phone_number}: SID={message.sid}, Status={message.status}")

        except Exception as e:
            logger.error(f"Failed to send WhatsApp PDF for {student_id}: {str(e)}")
            # Fallback to text message
            text_message = (
                f"Dear {contact.firstname or 'Parent'} {contact.lastname or 'Guardian'},\n"
                f"Gate Pass for {student_id}:\n"
                f"Pass ID: {pass_id}\n"
                f"Issued: {issued_date.strftime('%Y-%m-%d')}\n"
                f"Expires: {expiry_date.strftime('%Y-%m-%d')}\n"
                f"Payment: {payment_percentage:.1f}%\n"
                f"This pass is valid only for {contact.preferred_phone_number}. Do not share."
            )
            send_whatsapp_message(contact.preferred_phone_number, text_message)
            logger.info(f"Fallback text gate pass sent for {student_id} to {contact.preferred_phone_number}")
            return {
                "status": "Gate pass issued",
                "pass_id": pass_id,
                "expiry_date": expiry_date.isoformat(),
                "whatsapp_number": contact.preferred_phone_number
            }, 200

        return {
            "status": "Gate pass issued",
            "pass_id": pass_id,
            "expiry_date": expiry_date.isoformat(),
            "whatsapp_number": contact.preferred_phone_number
        }, 200
    except Exception as e:
        logger.error(f"Error generating gate pass for {student_id}: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/whatsapp-incoming", methods=["POST"])
def whatsapp_incoming():
    """Handle incoming WhatsApp messages."""
    try:
        from_number = request.form.get("From").replace("whatsapp:", "")
        message_body = request.form.get("Body").lower().strip()
        logger.debug(f"Incoming WhatsApp message from {from_number}: {message_body}")

        session = init_db()
        contact = session.query(StudentContact).filter_by(preferred_phone_number=from_number).first()
        response = MessagingResponse()

        if not contact:
            response.message("Please provide your student ID. Reply with 'ID <student_id>'.")
            return Response(str(response), mimetype="application/xml")

        if message_body == "get gatepass":
            gate_pass = session.query(GatePass).filter_by(student_id=contact.student_id, whatsapp_number=from_number).order_by(GatePass.issued_date.desc()).first()
            if not gate_pass:
                response.message(f"No active gate pass found for {contact.student_id}.")
            else:
                # Generate PDF for resending
                pdf_path = f"temp/gatepass_{gate_pass.pass_id}.pdf"
                qr_path = f"temp/qr_{gate_pass.pass_id}.png"
                os.makedirs("temp", exist_ok=True)

                # Generate QR code
                qr_url = f"https://shining-smiles-app-809413c70177.herokuapp.com//verify-gatepass?pass_id={gate_pass.pass_id}&whatsapp_number={from_number}"
                logger.debug(f"Generating QR code for URL: {qr_url}")
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_img.save(qr_path)
                if not os.path.exists(qr_path):
                    logger.error("QR code generation failed")
                    response.message("Error generating gate pass PDF. Please try again later.")
                    return Response(str(response), mimetype="application/xml")
                logger.debug(f"QR code saved to {qr_path}")

                # Generate PDF
                logger.debug(f"Generating PDF at {pdf_path}")
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                bold_style = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12)
                normal_style = ParagraphStyle(name='Normal', parent=styles['Normal'], fontSize=12)

                # Add watermark
                def add_watermark(canvas, doc):
                    canvas.saveState()
                    canvas.setFillAlpha(0.1)
                    logo_path = "static/school_logo.png"
                    if os.path.exists(logo_path):
                        canvas.drawImage(logo_path, 150, 300, width=300, height=150, preserveAspectRatio=True, mask='auto')
                    canvas.restoreState()

                doc.build = lambda flowables: SimpleDocTemplate.build(doc, flowables, onFirstPage=add_watermark)

                story = []

                # Header: Logo and Title
                logo_path = "static/school_logo.png"
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=2*inch, height=1*inch, kind='proportional')
                    title = Paragraph("SHINING SMILES GROUP OF SCHOOLS", ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, textColor=colors.darkblue))
                    header_table = Table([[logo, title]], colWidths=[2.5*inch, 4*inch])
                    header_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ]))
                    story.append(header_table)
                else:
                    logger.warning("School logo not found at static/school_logo.png")
                    story.append(Paragraph("SHINING SMILES GROUP OF SCHOOLS", ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=16, textColor=colors.darkblue)))

                story.append(Spacer(1, 0.5*inch))

                # Information table
                data = [
                    ["Student ID:", f"{contact.student_id}"],
                    ["Name:", f"{contact.firstname or 'N/A'} {contact.lastname or 'N/A'}"],
                    ["Pass ID:", f"{gate_pass.pass_id}"],
                    ["Issued:", f"{gate_pass.issued_date.strftime('%Y-%m-%d')}"],
                    ["Expires:", f"{gate_pass.expiry_date.strftime('%Y-%m-%d')}"],
                    ["Payment:", f"{gate_pass.payment_percentage}%"],
                    ["Valid for:", f"{from_number}"]
                ]
                info_table = Table(data, colWidths=[2*inch, 4*inch])
                info_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 12),
                    ('FONT', (1, 0), (1, -1), 'Helvetica', 12),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkblue),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgoldenrodyellow),
                ]))
                story.append(info_table)
                story.append(Spacer(1, 0.5*inch))

                # QR code (centered)
                if os.path.exists(qr_path):
                    logger.debug(f"Adding QR code from {qr_path}")
                    qr_image = Image(qr_path, width=2*inch, height=2*inch, kind='proportional')
                    qr_table = Table([[qr_image]], colWidths=[2*inch])
                    qr_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
                    story.append(qr_table)
                else:
                    logger.error("QR code file missing after generation")
                    response.message("Error generating gate pass PDF. Please try again later.")
                    return Response(str(response), mimetype="application/xml")

                # Signature
                signature_path = "static/signature.png"
                if os.path.exists(signature_path):
                    logger.debug(f"Adding signature from {signature_path}")
                    signature = Image(signature_path, width=2*inch, height=0.5*inch, kind='proportional')
                    story.append(Spacer(1, 0.25*inch))
                    story.append(Paragraph("Authorized Signature", normal_style))
                    story.append(signature)
                else:
                    logger.warning("Signature image not found at static/signature.png")
                    story.append(Paragraph("Authorized Signature", normal_style))

                doc.build(story)
                if not os.path.exists(pdf_path):
                    logger.error("PDF generation failed")
                    response.message("Error generating gate pass PDF. Please try again later.")
                    return Response(str(response), mimetype="application/xml")
                logger.debug(f"PDF generated at {pdf_path}")

                # Upload to S3
                s3_key = f"gatepasses/gatepass_{gate_pass.pass_id}.pdf"
                s3.upload_file(pdf_path, bucket_name, s3_key, ExtraArgs={'ACL': 'public-read'})
                public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                logger.debug(f"Uploaded PDF to S3: {public_url}")

                # Update database
                session = init_db()
                gate_pass.pdf_path = s3_key
                gate_pass.qr_path = qr_path
                session.commit()

                # Send PDF
                logger.debug(f"Sending PDF to WhatsApp: {public_url}")
                try:
                    response = requests.head(public_url, timeout=5)
                    if response.status_code != 200:
                        logger.error(f"Public URL inaccessible: {public_url}, status={response.status_code}")
                        raise Exception(f"Public URL inaccessible: status={response.status_code}")

                    message = twilio_client.messages.create(
                        from_=f"whatsapp:{app.config['TWILIO_WHATSAPP_NUMBER']}",
                        body="Your gate pass is attached. This pass is valid only for your WhatsApp number. Do not share.",
                        media_url=[public_url],
                        to=f"whatsapp:{from_number}",
                        status_callback=f"https://shining-smiles-app-809413c70177.herokuapp.com//message-status"
                    )
                    logger.info(f"Gate pass PDF sent for {contact.student_id} to {from_number}: SID={message.sid}, Status={message.status}")

                    response.message("Your gate pass has been sent as a PDF.")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp PDF for {contact.student_id}: {str(e)}")
                    text_message = (
                        f"Dear {contact.firstname or 'Parent'} {contact.lastname or 'Guardian'},\n"
                        f"Gate Pass for {contact.student_id}:\n"
                        f"Pass ID: {gate_pass.pass_id}\n"
                        f"Issued: {gate_pass.issued_date.strftime('%Y-%m-%d')}\n"
                        f"Expires: {gate_pass.expiry_date.strftime('%Y-%m-%d')}\n"
                        f"Payment: {gate_pass.payment_percentage}%\n"
                        f"This pass is valid only for {from_number}. Do not share."
                    )
                    send_whatsapp_message(from_number, text_message)
                    logger.info(f"Fallback text gate pass sent for {contact.student_id} to {from_number}")
                    response.message("Your gate pass has been sent as text due to an error with the PDF.")

            return Response(str(response), mimetype="application/xml")
        else:
            response.message("Send 'get gatepass' to view your latest gate pass.")
        return Response(str(response), mimetype="application/xml")
    except Exception as e:
        logger.error(f"Error handling WhatsApp message from {from_number}: {str(e)}")
        response = MessagingResponse()
        response.message("An error occurred. Please try again later.")
        return Response(str(response), mimetype="application/xml")

@app.route("/verify-gatepass", methods=["GET"])
def verify_gatepass():
    """Verify a gate pass."""
    try:
        pass_id = request.args.get("pass_id")
        whatsapp_number = request.args.get("whatsapp_number")
        if not pass_id or not whatsapp_number:
            logger.error("Missing pass_id or whatsapp_number")
            return {"error": "pass_id and whatsapp_number required"}, 400

        session = init_db()
        gate_pass = session.query(GatePass).filter_by(pass_id=pass_id, whatsapp_number=whatsapp_number).first()
        if not gate_pass:
            logger.error(f"Invalid gate pass {pass_id} for {whatsapp_number}")
            return {"error": "Invalid gate pass or WhatsApp number"}, 404

        if gate_pass.expiry_date < datetime.datetime.now(datetime.UTC):
            logger.error(f"Gate pass {pass_id} expired on {gate_pass.expiry_date}")
            return {"error": "Gate pass expired"}, 410

        return {
            "status": "valid",
            "student_id": gate_pass.student_id,
            "expiry_date": gate_pass.expiry_date.isoformat(),
            "whatsapp_number": gate_pass.whatsapp_number
        }, 200
    except Exception as e:
        logger.error(f"Error verifying gate pass {pass_id}: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/message-status", methods=["POST"])
def message_status():
    """Handle Twilio status callbacks for message delivery."""
    try:
        message_sid = request.form.get("MessageSid")
        message_status = request.form.get("MessageStatus")
        logger.debug(f"Message status callback: SID={message_sid}, Status={message_status}")

        session = init_db()
        gate_pass = session.query(GatePass).filter(GatePass.pass_id.ilike(f'%{message_sid[-10:]}%')).first()
        if gate_pass and message_status in ["delivered", "failed", "undelivered"]:
            if gate_pass.pdf_path:
                if gate_pass.pdf_path.startswith("temp/"):
                    if os.path.exists(gate_pass.pdf_path):
                        os.remove(gate_pass.pdf_path)
                        logger.debug(f"Cleaned up PDF: {gate_pass.pdf_path}")
                else:
                    s3.delete_object(Bucket=bucket_name, Key=gate_pass.pdf_path)
                    logger.debug(f"Deleted S3 PDF: {gate_pass.pdf_path}")
            if gate_pass.qr_path and os.path.exists(gate_pass.qr_path):
                os.remove(gate_pass.qr_path)
                logger.debug(f"Cleaned up QR code: {gate_pass.qr_path}")
            gate_pass.pdf_path = None
            gate_pass.qr_path = None
            session.commit()
            logger.info(f"Files cleaned up for message SID={message_sid}")

        return Response(status=200)
    except Exception as e:
        logger.error(f"Error in message status callback: {str(e)}")
        return Response(status=500)

@app.route("/temp/<path:filename>")
def serve_temp_file(filename):
    """Serve temporary files for testing (not for production)."""
    try:
        return send_from_directory("temp", filename)
    except Exception as e:
        logger.error(f"Error serving temp file {filename}: {str(e)}")
        return {"error": "File not found"}, 404

if __name__ == "__main__":
    logger.info(f"Environment variables - SMS_API_BASE_URL: {os.getenv('SMS_API_BASE_URL')}, SMS_API_KEY: {os.getenv('SMS_API_KEY')}")
    logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)