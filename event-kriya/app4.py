from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response,jsonify
from pymongo import MongoClient
from reportlab.pdfgen import canvas  # Using ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
import os  # For managing file paths
from PyPDF2 import PdfReader, PdfWriter
from xhtml2pdf import pisa
from io import BytesIO
import PyPDF2  

# from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response,jsonify
# from pymongo import MongoClient
# from reportlab.pdfgen import canvas  # Using ReportLab for PDF generation
# from reportlab.lib.pagesizes import letter
# import os  # For managing file paths
# from PyPDF2 import PdfReader, PdfWriter

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
        # Extract form data from request
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
        }
        session['event_data'] = event_data
        
        # Redirect to the preview page
        return redirect(url_for('items'))
    
    # Render the event form template if the request is GET
    return render_template('event.html')

        # Save the form data to the session for temporary storage
        

@app.route('/items', methods=['GET', 'POST'])
def items():
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
        return redirect(url_for('event_rounds'))

    # Render the items form template if the request is GET
    return render_template('items.html')
@app.route('/event_rounds', methods=['GET', 'POST'])
def event_rounds():
    if request.method == 'POST':
        # Extract form data from request (dynamic rounds)
        round_count = int(request.form.get('round_count', 0))
        rounds_data = []
        
        for i in range(round_count):
            round_data = {
                'round_name': request.form.get(f'round_name_{i}'),
                'round_description': request.form.get(f'round_description_{i}'),
                'round_rules': request.form.get(f'round_rules_{i}'),
            }
            rounds_data.append(round_data)

        # Save rounds data to session
        session['rounds_data'] = rounds_data
        
        # Redirect to the preview page or another page where you display the data
        return redirect(url_for('preview'))

    # Render the event rounds form template if the request is GET
    return render_template('event_rounds.html')


from flask import render_template, request, session

@app.route('/preview', methods=['GET'])
def preview():
    # Retrieve event details, event data, and items from session or defaults
    event_details = session.get('event_details', {})
    event_data = session.get('event_data', {})
    items = session.get('items', [])  # Default to an empty list if no items are stored
    event_info = session.get('event_info', {})  # Fetch event rounds data from session

    # Pass all data to the template
    return render_template('preview.html', 
                           event_details=event_details, 
                           event_data=event_data, 
                           items=items, 
                           event_info=event_info)  # Pass event_info (rounds) as well


@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        # Retrieve the JSON payload from the request body
        all_event_data = request.json
        event_details = all_event_data.get('eventDetails')
        event_data = all_event_data.get('eventData')
        items = all_event_data.get('items', [])  # Default to an empty list if not provided
        event_info = all_event_data.get('eventInfo')  # Get eventInfo

        print("Received eventInfo:", event_info)  # Debugging

        # Validate that items are provided
        if not items:
            return jsonify({"status": "error", "message": "No items provided."}), 400

        # Log received data for debugging
        print("Received event details:", event_details)
        print("Received event data:", event_data)

        # Generate a new event ID
        existing_event = event_collection.find_one(sort=[("event_id", -1)])  # Find the most recent event
        if existing_event and "event_id" in existing_event:
            # Increment the last part of the event ID (e.g., EVNT01 -> EVNT02)
            last_event_num = int(existing_event["event_id"][4:])
            new_event_id = f"EVNT{last_event_num + 1:02d}"
        else:
            new_event_id = "EVNT01"  # First event

        # Save event data to MongoDB
        event_entry = {
            "event_id": new_event_id,
            "details": event_details,
            "event": event_data,
            "items": items,  # Include items in the event entry
            "event_info": event_info  # Save eventInfo
        }
        event_collection.insert_one(event_entry)

        # Store event_id and event_info in session for tracking
        session["event_id"] = new_event_id
       

        # Return a success response with the new event ID
        return jsonify({"status": "success", "message": "Event submitted successfully!", "event_id": new_event_id}), 200

    except Exception as e:
        # Handle errors gracefully
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/confirm')
def confirm_page():
    return render_template('confirm.html')

@app.route('/view-preview', methods=['GET'])
def view_preview():
    event_id = session.get("event_id")  # Retrieve event_id from session
    if not event_id:
        flash("No event ID found in session.")
        return redirect(url_for('event_page'))

    event_data = event_collection.find_one({"event_id": event_id})
    if not event_data:
        flash("Event data not found.")
        return redirect(url_for('event_page'))

    try:
        # Render the first page
        form_data = event_data.get("details", {})
        html_content_page_1 = render_template(
            'event_preview.html',
            event_id=event_id,
            form_data=form_data,
            event_data=event_data
        )
        pdf_output_page_1 = generate_pdf(html_content_page_1)

        # Render the second page
        event_details = event_data.get("event", {})
        html_content_page_2 = render_template(
            'event_preview_second_page.html',
            event_id=event_id,
            event_details=event_details,
            event_data=event_data
        )
        pdf_output_page_2 = generate_pdf(html_content_page_2)

        # Render the third page (items preview)
        items = event_data.get("items", [])
        html_content_page_3 = render_template(
            'items_preview.html',
            event_id=event_id,
            items=items,
            event_data=event_data
        )
        pdf_output_page_3 = generate_pdf(html_content_page_3)

        # Combine PDFs
        combined_pdf_output = combine_pdfs(
            pdf_output_page_1,
            pdf_output_page_2,
            pdf_output_page_3
        )

        # Return combined PDF
        response = make_response(combined_pdf_output.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=event_{event_id}_preview_combined.pdf"
        return response

    except Exception as e:
        print(f"Error during preview: {e}")
        flash("An error occurred while generating the preview.")
        return redirect(url_for('event_page'))


def generate_pdf(html_content):
    """Generate a PDF from HTML content."""
    pdf_output = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_output)
    if pisa_status.err:
        raise ValueError("Error generating PDF.")
    pdf_output.seek(0)
    return pdf_output


def combine_pdfs(*pdf_outputs):
    """Combine multiple PDF outputs into a single PDF."""
    pdf_merger = PyPDF2.PdfMerger()
    for pdf_output in pdf_outputs:
        pdf_output.seek(0)
        pdf_merger.append(pdf_output)
    combined_pdf_output = BytesIO()
    pdf_merger.write(combined_pdf_output)
    combined_pdf_output.seek(0)
    return combined_pdf_output


# Assume `event_collection` is a valid MongoDB collection instance

if __name__ == '__main__':
    app.run(debug=True)
