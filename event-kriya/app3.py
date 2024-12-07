from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response,jsonify
from pymongo import MongoClient
from reportlab.pdfgen import canvas  # Using ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
import os  # For managing file paths
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Secure key for sessions

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/event-kriya?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"]

def combine_pdfs(pdf_path_1, pdf_path_2):
    try:
        # Create a PDF writer object
        writer = PdfWriter()

        # Read and add the pages of the first PDF
        with open(pdf_path_1, "rb") as file_1:
            reader_1 = PdfReader(file_1)
            for page in reader_1.pages:
                writer.add_page(page)

        # Read and add the pages of the second PDF
        with open(pdf_path_2, "rb") as file_2:
            reader_2 = PdfReader(file_2)
            for page in reader_2.pages:
                writer.add_page(page)

        # Get the directory of the input PDFs
        directory = os.path.dirname(pdf_path_1)

        # Set the output PDF file name
        output_path = os.path.join(directory, "combined_output.pdf")

        # Write the combined PDF to the output path
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        print(f"Combined PDF saved as {output_path}")

        # Remove the intermediate PDFs after combining
        os.remove(pdf_path_1)
        os.remove(pdf_path_2)
        print("Intermediate PDFs deleted.")

        return output_path

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/event-instructions', methods=['GET', 'POST'])
def event_instructions():
    if request.method == 'POST':
        return redirect(url_for('event_detail'))
    return render_template('event_instruction.html')


@app.route('/event_detail', methods=['GET', 'POST'])
def event_detail():
    if request.method == 'POST':
        # Collect event details
        event_details = {
            # Secretary Details
            'secretary_name': request.form['secretary_name'],
            'secretary_roll_number': request.form['secretary_roll_number'],
            'secretary_mobile': request.form['secretary_mobile'],
            
            # Convenor Details
            'convenor_name': request.form['convenor_name'],
            'convenor_roll_number': request.form['convenor_roll_number'],
            'convenor_mobile': request.form['convenor_mobile'],
            
            # Faculty Advisor Details
            'faculty_advisor_name': request.form['faculty_advisor_name'],
            'faculty_advisor_designation': request.form['faculty_advisor_designation'],
            'faculty_advisor_contact': request.form['faculty_advisor_contact'],
            
            # Judge Details
            'judge_name': request.form['judge_name'],
            'judge_designation': request.form['judge_designation'],
            'judge_contact': request.form['judge_contact']
        }
        # Save to session or database
        session['event_details'] = event_details
        return redirect(url_for('event_page'))
    
    # Render the event detail form
    return render_template('event_detail.html')


@app.route('/event', methods=['GET', 'POST'])
def event_page():
    if request.method == 'POST':
        # Collect event data from the form
        event_data = {
            'day_1': 'day_1' in request.form,
            'day_2': 'day_2' in request.form,
            'day_3': 'day_3' in request.form,
            'two_days': request.form.get('two_days'),
            'rounds': request.form.get('rounds'),
            'participants': request.form.get('participants'),
            'individual': 'individual' in request.form,
            'team': 'team' in request.form,
            'team_min': request.form.get('team_min'),
            'team_max': request.form.get('team_max'),
            'halls_required': request.form.get('halls_required'),
            'preferred_halls': request.form.get('preferred_halls'),
            'slot': request.form.get('slot'),
            'extension_boxes': request.form.get('extension_boxes'),
            'event_description': request.form.get('event_description'),
            'event_location': request.form.get('event_location')
        }
        
        # Store event data in session
        session['event_data'] = event_data
        
        # Redirect to the preview page
        return redirect(url_for('items'))
    
    # Render the event form template if the request is GET
    return render_template('event.html')
@app.route('/items', methods=['GET', 'POST'])
def items_page():
    if request.method == 'POST':
        # Collect items data from the form
        items = []
        rows = request.form.getlist('item_name[]')
        
        for i in range(len(rows)):
            item = {
                'item_name': request.form.getlist('item_name[]')[i],
                'quantity': request.form.getlist('quantity[]')[i],
                'price_per_unit': request.form.getlist('price_per_unit[]')[i],
                'total_price': request.form.getlist('total_price[]')[i]
            }
            items.append(item)
        
        # Store items data in session
        session['items_data'] = items

        # Redirect to a preview or confirmation page
        return redirect(url_for('preview_items'))

    # Render the items form template if the request is GET
    return render_template('items.html')


@app.route('/preview', methods=['GET'])
def preview():
    # Retrieve event details, event data, and items from the session
    event_details = session.get('event_details', {})
    event_data = session.get('event_data', {})
    items = session.get('items', [])  # Default to an empty list if no items are stored
    
    # Pass all data to the template
    return render_template('preview.html', 
                           event_details=event_details, 
                           event_data=event_data, 
                           items=items)

@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        # Retrieve JSON payload
        all_event_data = request.json
        event_details = all_event_data.get('eventDetails')
        event_data = all_event_data.get('eventData')
        items = all_event_data.get('items')  
        # Default to an empty list if not provided
        print("Received items:", items)

        if not items:
            return jsonify({"status": "error", "message": "No items provided."}), 400


        # Log received data for debugging
        print("Received event details:", event_details)
        print("Received event data:", event_data)
        print("Received items:", items)

        # Generate a new event ID
        existing_event = event_collection.find_one(sort=[("event_id", -1)])
        if existing_event and "event_id" in existing_event:
            last_event_num = int(existing_event["event_id"][4:])
            new_event_id = f"EVNT{last_event_num + 1:02d}"
        else:
            new_event_id = "EVNT01"

        # Save event data to MongoDB
        event_entry = {
            "event_id": new_event_id,
            "details": event_details,
            "event": event_data,
            "items": items  # Include items in the event entry
        }
        event_collection.insert_one(event_entry)

        # Store event_id in session
        session["event_id"] = new_event_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "event_id": new_event_id}), 200

    except Exception as e:
        # Handle errors gracefully
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/confirm')
def confirm_page():
    return render_template('confirm.html')


# Assume `event_collection` is a valid MongoDB collection instance

@app.route('/view-preview', methods=['GET'])
def view_preview():
    event_id = session.get("event_id")  # Retrieve event_id from session
    if event_id:
        event_data = event_collection.find_one({"event_id": event_id})
        try:
            if event_data:
                # Generate PDFs based on the event data
                form_data = event_data.get("details", {})

                pdf_filename_1 = f"event_preview_{event_id}.pdf"
                pdf_filepath_1 = os.path.join(os.getcwd(), pdf_filename_1)

                # Initialize PDF
                c = canvas.Canvas(pdf_filepath_1, pagesize=letter)

                # Draw Secretary Details Section
                width, height = letter
                margin = 50
                y = height - 50
                y = draw_fixed_table(
                    c,
                    x=margin,
                    y=y,
                    title="SECRETARY DETAILS:",
                    headers=["NAME", "ROLL NUMBER", "MOBILE NO"],
                    rows=[
                        [
                            form_data.get("secretary_name", "N/A"),
                            form_data.get("secretary_roll_number", "N/A"),
                            form_data.get("secretary_mobile", "N/A"),
                        ]
                    ],
                    num_rows=2,
                )

                # Draw Convenor and Volunteer Details Section
                y = draw_combined_section(
                    c,
                    x=margin,
                    y=y - 20,
                    title="CONVENOR AND VOLUNTEER DETAILS:",
                    headers=["NAME", "ROLL NUMBER", "MOBILE NO"],
                    convenors=[
                        {
                            "name": form_data.get("convenor_name", "N/A"),
                            "roll_number": form_data.get("convenor_roll_number", "N/A"),
                            "mobile": form_data.get("convenor_mobile", "N/A"),
                        }
                    ],
                    volunteers=form_data.get("volunteers", []),
                )

                # Draw Faculty Advisor Details Section
                y = draw_fixed_table(
                    c,
                    x=margin,
                    y=y - 20,
                    title="FACULTY ADVISOR DETAILS:",
                    headers=["NAME", "DESIGNATION", "CONTACT DETAILS"],
                    rows=[
                        [
                            form_data.get("advisor_name", "N/A"),
                            form_data.get("advisor_department", "N/A"),
                            form_data.get("advisor_contact", "N/A"),
                        ]
                    ],
                    num_rows=1,
                )

                # Draw Judge Details Section
                draw_fixed_table(
                    c,
                    x=margin,
                    y=y - 60,
                    title="JUDGE DETAILS:",
                    headers=["NAME", "DESIGNATION", "CONTACT DETAILS"],
                    rows=[
                        [
                            form_data.get("judge_name", "N/A"),
                            form_data.get("judge_designation", "N/A"),
                            form_data.get("judge_contact", "N/A"),
                        ]
                    ],
                    num_rows=1,
                )

                # Save the first PDF
                c.save()

                pdf_filename_2 = f"event_{event_id}_details.pdf"
                pdf_filepath_2 = os.path.join(os.getcwd(), pdf_filename_2)

                # Generate PDF for event-specific details
                event_details = event_data.get("event", {})
                pdf = canvas.Canvas(pdf_filepath_2, pagesize=letter)
                width, height = letter

                # Set margin for text placement
                margin = 60

                # Draw header line
                pdf.line(margin - 20, height - 40, width - margin, height - 40)

                # Checkboxes for days
                pdf.drawString(margin, height - 60, "Day 1:")
                pdf.rect(margin + 40, height - 61, 10, 10, fill=1 if "day1" in event_details.get("day", []) else 0)

                pdf.drawString(margin + 80, height - 60, "Day 2:")
                pdf.rect(margin + 130, height - 61, 10, 10, fill=1 if "day2" in event_details.get("day", []) else 0)

                pdf.drawString(margin + 170, height - 60, "Both Days:")
                pdf.rect(margin + 250, height - 61, 10, 10, fill=1 if "bothDays" in event_details.get("day", []) else 0)

                # Line after checkboxes
                pdf.line(margin - 20, height - 80, width - margin, height - 80)

                # Content fields
                pdf.drawString(margin, height - 110, f"Expected No. of Participants: {event_data.get('participants', 'N/A')}")
                pdf.drawString(margin, height - 140, f"Team Size: Min: {event_details.get('teamSizeMin', 'N/A')}, Max: {event_details.get('teamSizeMax', 'N/A')}")

                pdf.line(margin - 20, height - 150, width - margin, height - 150)

                pdf.drawString(margin, height - 170, f"Number of Halls/Labs Required: {event_details.get('halls_required', 'N/A')}")
                pdf.drawString(margin, height - 200, "Reason for Multiple Halls:")
                pdf.drawString(margin + 20, height - 220, event_details.get("hallReason", "N/A"))

                pdf.line(margin - 20, height - 230, width - margin, height - 230)

                pdf.drawString(margin, height - 250, "Halls/Labs Preferred:")
                pdf.drawString(margin + 20, height - 270, event_details.get("halls_preferred", "N/A"))

                pdf.line(margin - 20, height - 280, width - margin, height - 280)

                # Duration radio buttons
                pdf.drawString(margin, height - 300, "Duration of the Event in Hours:")
                pdf.drawString(margin + 20, height - 320, "Slot 1: 9:30 to 12:30")
                pdf.circle(margin + 160, height - 315, 5, fill=1 if event_details.get("duration") == "slot1" else 0)
                pdf.drawString(margin + 20, height - 340, "Slot 2: 1:30 to 4:30")
                pdf.circle(margin + 160, height - 335, 5, fill=1 if event_details.get("duration") == "slot2" else 0)
                pdf.drawString(margin + 20, height - 360, "Full Day")
                pdf.circle(margin + 160, height - 355, 5, fill=1 if event_details.get("duration") == "fullDay" else 0)

                pdf.line(margin - 20, height - 370, width - margin, height - 370)

                pdf.drawString(margin, height - 390, f"Number Required: {event_details.get('numberRequired', 'N/A')}")
                pdf.drawString(margin, height - 420, "Reason for Number:")
                pdf.drawString(margin + 20, height - 440, event_details.get("numberReason", "N/A"))

                pdf.line(margin - 20, height - 450, width - margin, height - 450)

                pdf.drawString(margin, height - 470, f"Extension Box: {event_details.get('extensionBox', 'N/A')}")

                pdf.line(margin - 20, height - 480, width - margin, height - 480)

                pdf.save()

                # Combine PDFs
                combined_pdf = combine_pdfs(pdf_filepath_1, pdf_filepath_2)

                if combined_pdf:
                    combined_pdf_filename = f"event_{event_id}_combined.pdf"
                    combined_pdf_path = os.path.join(os.getcwd(), combined_pdf_filename)

                    os.rename(combined_pdf, combined_pdf_path)

                    with open(combined_pdf_path, "rb") as f:
                        pdf_content = f.read()

                    response = make_response(pdf_content)
                    response.headers["Content-Type"] = "application/pdf"
                    response.headers["Content-Disposition"] = f"attachment; filename={combined_pdf_filename}"

                    return response

        except Exception as e:
            print(f"Error during preview: {e}")
            flash("An error occurred while generating the preview.")

    return redirect(url_for('event_page'))

def draw_fixed_table(pdf, x, y, title, headers, rows, num_rows):
    """
    Draws a section with a title and a table below it.
    """
    # Draw Title
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, title)
    y -= 25  # Add some space below the title

    # Draw Headers
    pdf.setFont("Helvetica-Bold", 10)
    cell_widths = [150, 100, 100]
    cell_height = 20  # Adjust row height to avoid overlap

    # Header row
    for i, header in enumerate(headers):
        pdf.rect(x + sum(cell_widths[:i]), y - cell_height, cell_widths[i], cell_height)
        pdf.drawString(x + sum(cell_widths[:i]) + 5, y - cell_height + 5, header)
    y -= cell_height

    # Draw Table Rows
    pdf.setFont("Helvetica", 10)
    for i in range(num_rows):
        row = rows[i] if i < len(rows) else [""] * len(headers)
        for j, cell in enumerate(row):
            pdf.rect(x + sum(cell_widths[:j]), y - cell_height, cell_widths[j], cell_height)
            pdf.drawString(x + sum(cell_widths[:j]) + 5, y - cell_height + 5, str(cell))
        y -= cell_height

    return y

# Helper Function: Draw Combined Section for Convenors and Volunteers
def draw_combined_section(pdf, x, y, title, headers, convenors, volunteers):
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, title)
    y -= 25  # Add space below title

    pdf.setFont("Helvetica-Bold", 10)
    cell_widths = [150, 100, 100]
    cell_height = 20  # Row height adjustment

    # Header row
    for i, header in enumerate(headers):
        pdf.rect(x + sum(cell_widths[:i]), y - cell_height, cell_widths[i], cell_height)
        pdf.drawString(x + sum(cell_widths[:i]) + 5, y - cell_height + 5, header)
    y -= cell_height

    # Draw Convenors
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(x, y, "CONVENORS")
    y -= cell_height

    for convenor in convenors:
        row = [convenor.get("name", "N/A"), convenor.get("roll_number", "N/A"), convenor.get("mobile", "N/A")]
        for i, cell in enumerate(row):
            pdf.rect(x + sum(cell_widths[:i]), y - cell_height, cell_widths[i], cell_height)
            pdf.drawString(x + sum(cell_widths[:i]) + 5, y - cell_height + 5, str(cell))
        y -= cell_height

    # Draw Volunteers
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(x, y, "VOLUNTEERS")
    y -= cell_height

    for volunteer in volunteers:
        row = [volunteer.get("name", "N/A"), volunteer.get("roll_number", "N/A"), volunteer.get("mobile", "N/A")]
        for i, cell in enumerate(row):
            pdf.rect(x + sum(cell_widths[:i]), y - cell_height, cell_widths[i], cell_height)
            pdf.drawString(x + sum(cell_widths[:i]) + 5, y - cell_height + 5, str(cell))
        y -= cell_height

    return y



    return redirect(url_for('event_page'))
if __name__ == '__main__':
    app.run(debug=True)
