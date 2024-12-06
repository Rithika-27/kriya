from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
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

@app.route('/event-detail', methods=['GET', 'POST'])
def event_detail():
    if request.method == 'POST':
        # Collect form data
        form_data = {
            "secretary": {
                "name": request.form.get("secretary_name"),
                "roll_number": request.form.get("secretary_roll_number"),
                "mobile": request.form.get("secretary_mobile"),
            },
            "convenor": {
                "name": request.form.get("convenor_name"),
                "roll_number": request.form.get("convenor_roll_number"),
                "mobile": request.form.get("convenor_mobile"),
            },
            "faculty_advisor": {
                "name": request.form.get("faculty_advisor_name"),
                "designation": request.form.get("faculty_advisor_designation"),
                "contact": request.form.get("faculty_advisor_contact"),
            },
            "judge": {
                "name": request.form.get("judge_name"),
                "designation": request.form.get("judge_designation"),
                "contact": request.form.get("judge_contact"),
            }
        }

        # Save data to session or database
        session['event_details'] = form_data

        # Flash message
        flash("Event details saved successfully!")

        # Redirect to the next page
        return redirect(url_for('event_page'))  # Make sure you have a route for event_page

    return render_template('event_detail.html')

@app.route('/event', methods=['GET', 'POST'])
def event_page():
    event_id = session.get("event_id")  # Retrieve event_id from session

    if request.method == 'POST':
        # Get the form data and ensure there are no errors when fields are missing
        event_data = {
            "day_1": bool(request.form.get("day_1")),
            "day_2": bool(request.form.get("day_2")),
            "day_3": bool(request.form.get("day_3")),
            "participants": request.form.get("participants", "").strip(),
            "halls_required": request.form.get("halls_required", "").strip(),
            "team_min": request.form.get("team_min", "").strip() if request.form.get("team_min") else None,
            "team_max": request.form.get("team_max", "").strip() if request.form.get("team_max") else None,
        }

        # Check if the required fields are provided and handle missing data appropriately
        if not event_data["participants"] or not event_data["halls_required"]:
            flash("Please fill in all the required fields.")
            return redirect(url_for('event_page'))

        try:
            if event_id:
                event_collection.update_one({"event_id": event_id}, {"$set": {"event": event_data}})
                flash("Event details updated successfully!")

                # Generate PDF for event details
                pdf_filename = f"event_{event_id}_details.pdf"
                pdf_filepath = os.path.join(os.getcwd(), pdf_filename)  # Save in current directory

                c = canvas.Canvas(pdf_filepath, pagesize=letter)
                c.drawString(100, 750, f"Event ID: {event_id}")
                c.drawString(100, 730, f"Participants: {event_data['participants']}")
                c.drawString(100, 710, f"Halls Required: {event_data['halls_required']}")
                if event_data['team_min']:
                    c.drawString(100, 690, f"Team Minimum: {event_data['team_min']}")
                if event_data['team_max']:
                    c.drawString(100, 670, f"Team Maximum: {event_data['team_max']}")
                c.drawString(100, 650, f"Day 1: {'Yes' if event_data['day_1'] else 'No'}")
                c.drawString(100, 630, f"Day 2: {'Yes' if event_data['day_2'] else 'No'}")
                c.drawString(100, 610, f"Day 3: {'Yes' if event_data['day_3'] else 'No'}")

                # Save the PDF file
                c.save()

                # Redirect to the next page (you can replace 'success' with any other page you want to go to after PDF generation)
                return redirect(url_for('confirm_page'))

            else:
                flash("Error: Event ID not found in session.")
                return redirect(url_for('event_detail'))

        except Exception as e:
            print(f"Error saving event data to MongoDB: {e}")
            flash("An error occurred while updating event details. Please try again.")

        return redirect(url_for('confirm_page'))  # If everything goes fine, skip the items_page and go to success page

    return render_template('event.html')
@app.route('/confirm')
def confirm_page():
    return render_template('confirm.html') 
@app.route('/view-preview', methods=['GET'])
def view_preview():
    event_id = session.get("event_id")  # Retrieve event_id from session
    if event_id:
        # Path for the two PDFs
        pdf_path_1 = os.path.join(os.getcwd(), f"event_{event_id}.pdf")
        pdf_path_2 = os.path.join(os.getcwd(), f"event_{event_id}_details.pdf")

        # Combine the PDFs
        combined_pdf_path = combine_pdfs(pdf_path_1, pdf_path_2)

        if combined_pdf_path:
            # Send combined PDF as a response
            with open(combined_pdf_path, "rb") as combined_pdf:
                response = make_response(combined_pdf.read())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=combined_event_{event_id}.pdf'
                os.sa
                return response
        else:
            flash("An error occurred while combining the PDFs.")
            return redirect(url_for('confirm_page'))
    else:
        flash("No event ID found.")
        return redirect(url_for('event_detail'))


if __name__ == '__main__':
    app.run(debug=True)
