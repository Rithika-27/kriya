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
        return redirect(url_for('preview'))
    
    # Render the event form template if the request is GET
    return render_template('event.html')

@app.route('/preview', methods=['GET'])
def preview():
    # Retrieve event details and data from the session
    event_details = session.get('event_details', {})
    event_data = session.get('event_data', {})
    return render_template('preview.html', event_details=event_details, event_data=event_data)

@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        all_event_data = request.json
        event_details = all_event_data.get('eventDetails')
        event_data = all_event_data.get('eventData')

        # Log the received data to ensure it's correct
        print("Received event details:", event_details)
        print("Received event data:", event_data)


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
            "event": event_data
        }
        event_collection.insert_one(event_entry)

        # Store event_id in session
        session["event_id"] = new_event_id

        return jsonify({"status": "success", "message": "Event submitted successfully!", "event_id": new_event_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/confirm')
def confirm_page():
    return render_template('confirm.html')


@app.route('/view-preview', methods=['GET'])
def view_preview():
    event_id = session.get("event_id")  # Retrieve event_id from session
    if event_id:
        try:
            # Fetch event data from MongoDB using event_id
            event_data = event_collection.find_one({"event_id": event_id})
            if event_data:
                # Generate PDFs based on the event data
                form_data = event_data["details"]
                pdf_filename_1 = f"event_{event_id}.pdf"
                pdf_filepath_1 = os.path.join(os.getcwd(), pdf_filename_1)

                # Generate PDF for event details
                c = canvas.Canvas(pdf_filepath_1, pagesize=letter)
                c.drawString(100, 750, f"Event ID: {event_id}")
                c.drawString(100, 730, f"Secretary: {form_data.get('secretary_name', 'N/A')} ({form_data.get('secretary_roll_number', 'N/A')})")
                c.drawString(100, 710, f"Mobile: {form_data.get('secretary_mobile', 'N/A')}")
                c.save()

                pdf_filename_2 = f"event_{event_id}_details.pdf"
                pdf_filepath_2 = os.path.join(os.getcwd(), pdf_filename_2)

                # Generate PDF for event-specific details
                event_details = event_data["event"]
                c = canvas.Canvas(pdf_filepath_2, pagesize=letter)
                c.drawString(100, 750, f"Event ID: {event_id}")
                c.drawString(100, 730, f"Rounds: {event_details.get('rounds', 'N/A')}")
                c.drawString(100, 710, f"Description: {event_details.get('event_description', 'N/A')}")
                c.drawString(100, 690, f"Location: {event_details.get('event_location', 'N/A')}")
                c.drawString(100, 670, f"Day 1: {'Yes' if event_details.get('day_1') else 'No'}")
                c.drawString(100, 650, f"Day 2: {'Yes' if event_details.get('day_2') else 'No'}")
                c.drawString(100, 630, f"Day 3: {'Yes' if event_details.get('day_3') else 'No'}")
                c.save()

                # Combine the two PDFs into one
                combined_pdf = combine_pdfs(pdf_filepath_1, pdf_filepath_2)

                if combined_pdf:
                    combined_pdf_filename = f"event_{event_id}_combined.pdf"
                    combined_pdf_path = os.path.join(os.getcwd(), combined_pdf_filename)

                    # Move the combined PDF to the desired location
                    os.rename(combined_pdf, combined_pdf_path)

                    # Serve the combined PDF for download
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



if __name__ == '__main__':
    app.run(debug=True)
