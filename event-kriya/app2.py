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

        try:
            # Generate a new event ID only when the "view-preview" route is called (to be done in view-preview)
            # Insert event data into MongoDB
            event_collection.insert_one({"details": form_data, "event_id": ""})  # Insert without event_id
            flash("Event details saved successfully!")
            return redirect(url_for('event_page'))  # Redirect to the event_page route

        except Exception as e:
            print(f"Error saving event details: {e}")
            flash("An error occurred while saving event details.")
            return redirect(url_for('event_detail'))

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
        try:
            # Fetch data from MongoDB
            event_data = event_collection.find_one({"event_id": event_id})

            if event_data:
                # Generate both PDFs based on the event data
                form_data = event_data["details"]
                
                # Generate a new event ID here
                existing_event = event_collection.find_one(sort=[("event_id", -1)])
                if existing_event and "event_id" in existing_event:
                    last_event_num = int(existing_event["event_id"][4:])
                    new_event_id = f"EVNT{last_event_num + 1:02d}"
                else:
                    new_event_id = "EVNT01"
                
                # Save the new event_id to the database
                event_collection.update_one({"_id": event_data["_id"]}, {"$set": {"event_id": new_event_id}})
                session["event_id"] = new_event_id  # Store the event ID in session

                pdf_filename_1 = f"event_{new_event_id}.pdf"
                pdf_filepath_1 = os.path.join(os.getcwd(), pdf_filename_1)  # Save in current directory

                # Generate PDF for event details
                c = canvas.Canvas(pdf_filepath_1, pagesize=letter)
                c.drawString(100, 750, f"Event ID: {new_event_id}")
                c.drawString(100, 730, f"Secretary: {form_data['secretary']['name']} ({form_data['secretary']['roll_number']})")
                c.drawString(100, 710, f"Convenor: {form_data['convenor']['name']} ({form_data['convenor']['roll_number']})")
                c.drawString(100, 690, f"Faculty Advisor: {form_data['faculty_advisor']['name']} ({form_data['faculty_advisor']['designation']})")
                c.drawString(100, 670, f"Judge: {form_data['judge']['name']} ({form_data['judge']['designation']})")
                c.save()

                pdf_filename_2 = f"event_{new_event_id}_details.pdf"
                pdf_filepath_2 = os.path.join(os.getcwd(), pdf_filename_2)  # Save in current directory

                # Generate PDF for event details page
                event_details = event_data["event"]
                c = canvas.Canvas(pdf_filepath_2, pagesize=letter)
                c.drawString(100, 750, f"Event ID: {new_event_id}")
                c.drawString(100, 730, f"Participants: {event_details['participants']}")
                c.drawString(100, 710, f"Halls Required: {event_details['halls_required']}")
                if event_details['team_min']:
                    c.drawString(100, 690, f"Team Minimum: {event_details['team_min']}")
                if event_details['team_max']:
                    c.drawString(100, 670, f"Team Maximum: {event_details['team_max']}")
                c.drawString(100, 650, f"Day 1: {'Yes' if event_details['day_1'] else 'No'}")
                c.drawString(100, 630, f"Day 2: {'Yes' if event_details['day_2'] else 'No'}")
                c.drawString(100, 610, f"Day 3: {'Yes' if event_details['day_3'] else 'No'}")
                c.save()

                # Combine the two PDFs into one
                combined_pdf = combine_pdfs(pdf_filepath_1, pdf_filepath_2)

                if combined_pdf:
                    # Define the path for saving the combined PDF with event_id
                    combined_pdf_filename = f"event_{new_event_id}_combined.pdf"
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
