import os
from flask import session, Flask, flash, redirect, url_for, render_template, request, send_file
from pymongo import MongoClient
from reportlab.pdfgen import canvas
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Secure key for sessions

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/event-kriya?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"] 
workshop_collection = db["workshops"]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/event-instructions', methods=['GET', 'POST'])
def event_instructions():
    if request.method == 'POST':
        return redirect(url_for('event_detail'))
    return render_template('event_instruction.html')

@app.route('/workshop-instructions', methods=['GET', 'POST'])
def workshop_instructions():
    if request.method == 'POST':
        return redirect(url_for('workshop_detail'))
    return render_template('workshop_instruction.html')

@app.route('/event-detail', methods=['GET', 'POST'])
def event_detail():
    if request.method == 'POST':
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
            # Check if session has an event ID
            event_id = session.get("event_id")
            if not event_id:
                # Generate a new event ID if not already in session
                existing_event = event_collection.find_one(sort=[("event_id", -1)])
                if existing_event and "event_id" in existing_event:
                    last_event_num = int(existing_event["event_id"][4:])
                    event_id = f"EVNT{last_event_num + 1:02d}"
                else:
                    event_id = "EVNT01"
                session["event_id"] = event_id

            # Upsert to main collection with status "temporary"
            event_collection.update_one(
                {"event_id": event_id},
                {"$set": {"details": form_data, "event_id": event_id, "status": "temporary"}},
                upsert=True
            )
            flash("Event details saved temporarily!")
            return redirect(url_for('event_page'))
        except Exception as e:
            print(f"Error saving event details: {e}")
            flash("An error occurred while saving event details.")
            return redirect(url_for('event_detail'))

    return render_template('event_detail.html')

@app.route('/workshop-detail', methods=['GET', 'POST'])
def workshop_detail():
    if request.method == 'POST':
        # Extract form data
        form_data = {
            "organizer": {
                "name": request.form.get("organizer_name"),
                "roll_number": request.form.get("organizer_roll_number"),
                "mobile": request.form.get("organizer_mobile"),
            },
            "faculty_advisor": {
                "name": request.form.get("faculty_advisor_name"),
                "designation": request.form.get("faculty_advisor_designation"),
                "contact": request.form.get("faculty_advisor_contact"),
            },
            "speaker": {
                "name": request.form.get("speaker_name"),
                "designation": request.form.get("speaker_designation"),
                "contact": request.form.get("speaker_contact"),
            }
        }

        try:
            # Check if session has a workshop ID
            workshop_id = session.get("workshop_id")
            if not workshop_id:
                # Generate a new workshop ID if not already in session
                existing_workshop = workshop_collection.find_one(sort=[("workshop_id", -1)])
                if existing_workshop and "workshop_id" in existing_workshop:
                    last_workshop_num = int(existing_workshop["workshop_id"][4:])
                    workshop_id = f"WSHP{last_workshop_num + 1:02d}"
                else:
                    workshop_id = "WSHP01"
                session["workshop_id"] = workshop_id

            # Upsert to main collection with status "temporary"
            workshop_collection.update_one(
                {"workshop_id": workshop_id},
                {"$set": {"details": form_data, "workshop_id": workshop_id, "status": "temporary"}},
                upsert=True
            )
            flash("Workshop details saved temporarily!")
            return redirect(url_for('workshop_page'))  # Redirect to a workshop summary page
        except Exception as e:
            print(f"Error saving workshop details: {e}")
            flash("An error occurred while saving workshop details.")
            return redirect(url_for('workshop_detail'))

    return render_template('workshop_detail.html')

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

        return redirect(url_for('items_page'))

    return render_template('event.html')
@app.route('/workshop', methods=['GET', 'POST'])
def workshop_page():
    workshop_id = session.get("workshop_id")  # Retrieve workshop_id from session

    if request.method == 'POST':
        # Get the form data
        workshop_data = {
            "day_2": bool(request.form.get("day_2")),
            "day_3": bool(request.form.get("day_3")),
            "both_days": bool(request.form.get("both_days")),
            "participants": request.form.get("participants", "").strip(),
            "proposing_fees": request.form.get("proposing_fees", "").strip(),
            "speaker_remuneration": request.form.get("speaker_remuneration", "").strip(),
            "halls_required": request.form.get("halls_required", "").strip(),
            "preferred_halls": request.form.get("preferred_halls", "").strip(),
            "slot": request.form.get("slot"),
            "extension_box": request.form.get("extension_box", "").strip()
        }

        # Validate required fields
        if not workshop_data["participants"] or not workshop_data["halls_required"]:
            flash("Please fill in all the required fields.")
            return redirect(url_for('workshop_page'))

        try:
            # Update or insert workshop details
            if workshop_id:
                workshop_collection.update_one({"workshop_id": workshop_id}, {"$set": {"workshop": workshop_data}})
                flash("Workshop details updated successfully!")
            else:
                # Insert new workshop details if no workshop_id is found
                workshop_id = workshop_collection.insert_one({"workshop": workshop_data}).inserted_id
                session["workshop_id"] = str(workshop_id)
                flash("Workshop details saved successfully!")

        except Exception as e:
            print(f"Error saving workshop data to MongoDB: {e}")
            flash("An error occurred while saving workshop details. Please try again.")

        return redirect(url_for('items_page'))

    # If GET request, render the workshop page
    return render_template('workshop.html')

@app.route('/generate-pdf')
def generate_pdf():
    event_id = session.get("event_id")
    
    if not event_id:
        flash("Error: Event ID not found in session.")
        return redirect(url_for('event_detail'))
    
    try:
        # Retrieve the event details from the main collection with status "temporary"
        event = event_collection.find_one({"event_id": event_id, "status": "temporary"})
        if not event:
            flash("Error: Temporary event not found.")
            return redirect(url_for('event_detail'))

        # Update the status to "final"
        event_collection.update_one(
            {"event_id": event_id},
            {"$set": {"status": "final"}}
        )
        
        # Create a new PDF in memory
        packet = BytesIO()
        can = canvas.Canvas(packet)
        
        # Add event details to the PDF
        can.setFont("Helvetica", 12)
        can.drawString(100, 750, f"Event ID: {event['event_id']}")
        can.drawString(100, 730, f"Secretary: {event['details']['secretary']['name']}")
        can.drawString(100, 710, f"Secretary Roll Number: {event['details']['secretary']['roll_number']}")
        can.drawString(100, 690, f"Secretary Mobile: {event['details']['secretary']['mobile']}")
        
        can.drawString(100, 670, f"Convenor: {event['details']['convenor']['name']}")
        can.drawString(100, 650, f"Convenor Roll Number: {event['details']['convenor']['roll_number']}")
        can.drawString(100, 630, f"Convenor Mobile: {event['details']['convenor']['mobile']}")
        
        can.drawString(100, 610, f"Faculty Advisor: {event['details']['faculty_advisor']['name']}")
        can.drawString(100, 590, f"Faculty Advisor Designation: {event['details']['faculty_advisor']['designation']}")
        can.drawString(100, 570, f"Faculty Advisor Contact: {event['details']['faculty_advisor']['contact']}")
        
        can.drawString(100, 550, f"Judge: {event['details']['judge']['name']}")
        can.drawString(100, 530, f"Judge Designation: {event['details']['judge']['designation']}")
        can.drawString(100, 510, f"Judge Contact: {event['details']['judge']['contact']}")
        
        # Save the PDF
        can.save()
        packet.seek(0)
        
        # Serve the PDF inline
        return send_file(packet, mimetype='application/pdf', download_name=f"event_{event_id}.pdf", as_attachment=False)
    
    except Exception as e:
        print(f"Error generating PDF: {e}")
        flash("An error occurred while generating the PDF.")
        return redirect(url_for('event_detail'))

if __name__ == '__main__':
    app.run(debug=True)
