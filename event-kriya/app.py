from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'xyz1234nbg789ty8inmcv2134'  # Replace with a secure key for sessions

# MongoDB connection
MONGO_URI = "mongodb+srv://Entries:ewp2025@cluster0.1tuj7.mongodb.net/"  
client = MongoClient(MONGO_URI)
db = client["event-kriya"]
event_collection = db["event-entries"]

# Print collection names to verify connection
print("Collections in Database:", db.list_collection_names())

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
    event_id = session.get("event_id")  # Retrieve existing event_id from session
    print("Session Event ID at /event-detail:", event_id)

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
            "volunteer": {
                "name": request.form.get("volunteer_name"),
                "roll_number": request.form.get("volunteer_roll_number"),
                "mobile": request.form.get("volunteer_mobile"),
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
            },
        }

        # Debugging log
        print("Form Data Received at /event-detail:", form_data)

        try:
            # Update existing document or insert a new one
            if event_id:
                event_collection.update_one({"_id": ObjectId(event_id)}, {"$set": {"details": form_data}})
                print("Updated Event ID:", event_id)
            else:
                result = event_collection.insert_one({"details": form_data})
                session["event_id"] = str(result.inserted_id)  # Store the new ID in session
                print("New Event Created, ID:", result.inserted_id)

            flash("Event details saved successfully!")
        except Exception as e:
            print("Error saving event details to MongoDB:", e)
            flash("An error occurred while saving event details. Please try again.")

        return redirect(url_for('event_page'))

    # Prefill data if available
    data = session.get("event_detail") or {}
    return render_template('event_detail.html', data=data)

@app.route('/event', methods=['GET', 'POST'])
def event_page():
    event_id = session.get("event_id")
    print("Session Event ID at /event:", event_id)

    if request.method == 'POST':
        event_data = {
            "day_1": bool(request.form.get("day_1")),
            "day_2": bool(request.form.get("day_2")),
            "day_3": bool(request.form.get("day_3")),
            "two_days": request.form.get("two_days"),
            "technical": bool(request.form.get("technical")),
            "non_technical": bool(request.form.get("non_technical")),
            "rounds": request.form.get("rounds"),
            "participants": request.form.get("participants"),
            "individual": bool(request.form.get("individual")),
            "team_min": request.form.get("team_min"),
            "team_max": request.form.get("team_max"),
            "halls_required": request.form.get("halls_required"),
            "preferred_halls": request.form.get("preferred_halls"),
            "slot": request.form.get("slot"),
            "extension_boxes": request.form.get("extension_boxes"),
        }

        print("Form Data Received at /event:", event_data)

        try:
            if event_id:
                event_collection.update_one({"_id": ObjectId(event_id)}, {"$set": {"event": event_data}})
                print("Updated Event ID:", event_id)
            else:
                result = event_collection.insert_one({"event": event_data})
                session["event_id"] = str(result.inserted_id)
                print("New Event Created, ID:", result.inserted_id)

            flash("Event details updated successfully!")
        except Exception as e:
            print("Error saving event data to MongoDB:", e)
            flash("An error occurred while updating event details. Please try again.")

        return redirect(url_for('items_page'))

    data = session.get("event_page") or {}
    return render_template('event.html', data=data)

@app.route('/items', methods=['GET', 'POST'])
def items_page():
    event_id = session.get("event_id")
    print("Session Event ID at /items:", event_id)

    if request.method == 'POST':
        items_data = {
            "sno": request.form.get("sno"),
            "item_name": request.form.get("item_name"),
            "quantity": request.form.get("quantity"),
            "price_per_unit": request.form.get("price_per_unit"),
            "total_price": request.form.get("total_price"),
        }

        print("Form Data Received at /items:", items_data)

        try:
            if not items_data["item_name"] or not items_data["quantity"]:
                flash("Item name and quantity are required.")
                return jsonify({"success": False, "message": "Item name and quantity are required."}), 400

            if event_id:
                event_collection.update_one({"_id": ObjectId(event_id)}, {"$push": {"items": items_data}})
                print("Updated Event ID:", event_id)
            else:
                result = event_collection.insert_one({"items": [items_data]})
                session["event_id"] = str(result.inserted_id)
                print("New Items Created, ID:", result.inserted_id)

            flash("Item details saved successfully!")
        except Exception as e:
            print("Error saving item data to MongoDB:", e)
            flash("An error occurred while saving item details. Please try again.")

        return jsonify({"success": True, "message": "Item details saved successfully!"}), 200

    data = session.get("items") or []
    return render_template('items.html', items=data)

if __name__ == '__main__':
    app.run(debug=True)
