from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Secure key for sessions

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/event-kriya?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"]

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
            # Insert the data into the MongoDB collection
            result = event_collection.insert_one({"details": form_data})
            session["event_id"] = str(result.inserted_id)  # Store event_id in session
            flash("Event details saved successfully!")
            return redirect(url_for('event_page'))
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
                event_collection.update_one({"_id": ObjectId(event_id)}, {"$set": {"event": event_data}})
                print(f"Updated Event ID: {event_id}")
            else:
                flash("Error: Event ID not found in session.")
                return redirect(url_for('event_detail'))

            flash("Event details updated successfully!")
        except Exception as e:
            print(f"Error saving event data to MongoDB: {e}")
            flash("An error occurred while updating event details. Please try again.")

        return redirect(url_for('items_page'))

    return render_template('event.html')


@app.route('/items', methods=['GET', 'POST'])
def items_page():
    event_id = session.get("event_id")  # Retrieve event_id from session

    if request.method == 'POST':
        items_data = {
            "sno": request.form.get("sno"),
            "item_name": request.form.get("item_name"),
            "quantity": request.form.get("quantity"),
        }

        if not items_data["item_name"] or not items_data["quantity"]:
            flash("Item name and quantity are required.")
            return jsonify({"success": False, "message": "Item name and quantity are required."}), 400

        try:
            if event_id:
                event_collection.update_one({"_id": ObjectId(event_id)}, {"$push": {"items": items_data}})
                print(f"Updated Event ID: {event_id}")
            else:
                flash("Error: Event ID not found in session.")
                return redirect(url_for('event_detail'))

            flash("Item details saved successfully!")
        except Exception as e:
            print(f"Error saving item data to MongoDB: {e}")
            flash("An error occurred while saving item details. Please try again.")

        return jsonify({"success": True, "message": "Item details saved successfully!"}), 200

    return render_template('items.html')

if __name__ == '__main__':
    app.run(debug=True)
