import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from flask import request, jsonify, render_template, redirect, url_for

from app import app
from db import db
from models import CharSheetType, CharSheetInstance, CharSheetRevisions

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/charsheet/<id_>', methods=['GET'])
def show_charsheet(id_):
    charsheet = CharSheetInstance.query.filter_by(id=id_).first()
    if charsheet is None:
        return 'unknown sheet', 404
    return render_template('charsheet.html', charsheet=charsheet)


@app.route('/charsheet/rev/<rev_id>', methods=['GET'])
def show_revision(rev_id):
    # Find the revision by its ID
    revision = CharSheetRevisions.query.filter_by(rev_id=rev_id).first()
    if revision is None:
        return 'Revision not found', 404

    charsheet = CharSheetInstance.query.filter_by(id=revision.csinst_id).first()
    if charsheet is None:
        return 'Character sheet not found', 404

    charsheet_type = CharSheetType.query.filter_by(id=charsheet.sheet_type_id).first()

    modified_charsheet = {
        'id': charsheet.id,
        'name': charsheet.name,
        'form_values': revision.form_values,
        'sheet_type_id': charsheet.sheet_type_id,
        'sheet_type': charsheet_type
    }

    return render_template('charsheet.html', charsheet=modified_charsheet)

@app.route('/charsheet/lookup', methods=['GET'])
def charsheet_lookup():
    lookup_value = request.args.get('charsheet_lookup', '').strip()

    # Check if lookup_value is a valid UUID
    try:
        lookup_uuid = uuid.UUID(lookup_value, version=4)
        
        # Try to find a matching CharSheetInstance or CharSheetRevisions
        charsheet = CharSheetInstance.query.filter_by(id=lookup_uuid).first()
        if charsheet:
            return redirect(url_for('show_charsheet', id_=charsheet.id))
        
        revision = CharSheetRevisions.query.filter_by(rev_id=lookup_uuid).first()
        if revision:
            return redirect(url_for('show_revision', rev_id=revision.rev_id))
        
    except ValueError:
        # Not a valid UUID, proceed to name search
        pass

    # Perform a case-insensitive search for CharSheetInstances by name
    charsheets = CharSheetInstance.query.filter(
        func.lower(CharSheetInstance.name).contains(func.lower(lookup_value))
    ).all()

    # Render a lookup_results.html template with the search results
    return render_template('lookup_results.html', charsheets=charsheets, search_query=lookup_value)



@app.route('/charsheet/new', methods=['POST'])
def create_charsheet_instance():
    new_charsheet = CharSheetInstance(
        name=request.form['sheet_name'],
        sheet_type_id=request.form['sheet_type'],
        creation_ip=request.headers.get('X-Forwarded-For', request.remote_addr)
    )
    db.session.add(new_charsheet)
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = CharSheetInstance.query.filter_by(name=request.form['sheet_name']).first()
        return redirect(url_for('show_charsheet', id_=existing.id))

    return redirect(url_for('show_charsheet', id_=new_charsheet.id))


@app.route('/charsheet/<id_>/save', methods=['POST'])
def save_charsheet(id_):
    # Check if the request payload is larger than 20MB
    content_length = request.content_length
    if content_length is not None and content_length > (20 * 1024 * 1024):
        return jsonify({"error": "Payload too large"}), 413

    # Retrieve the character sheet by ID
    charsheet = CharSheetInstance.query.filter_by(id=id_).first()
    if not charsheet:
        return jsonify({"error": "Character sheet not found"}), 404

    # Assuming the payload is a JSON with character sheet data
    try:
        data = request.get_json()
        if data is None:
            raise ValueError("No JSON data sent")
        # Update the character sheet's attributes based on the data received
        # For example:
        charsheet.form_values = data.get('form_values', charsheet.form_values)
        # Add any other fields you expect to update

        db.session.commit()
        return jsonify({"message": "Character sheet updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route('/charsheet/<id_>/save-new', methods=['POST'])
def save_charsheet_as_new(id_):
    source = CharSheetInstance.query.filter_by(id=id_).first()
    if not source:
        return jsonify({"error": "Source character sheet not found"}), 404

    data = request.get_json()
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({"error": "Name is required"}), 400

    new_charsheet = CharSheetInstance(
        name=new_name,
        sheet_type_id=source.sheet_type_id,
        form_values=data.get('form_values', source.form_values),
        creation_ip=request.headers.get('X-Forwarded-For', request.remote_addr)
    )
    db.session.add(new_charsheet)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A sheet with that name already exists"}), 409

    return jsonify({"id": new_charsheet.id}), 201

@app.route('/charsheet/<id_>/delete', methods=['POST'])
def delete_charsheet(id_):
    charsheet = CharSheetInstance.query.filter_by(id=id_).first()
    if not charsheet:
        return jsonify({"error": "Character sheet not found"}), 404

    CharSheetRevisions.query.filter_by(csinst_id=id_).delete()
    db.session.delete(charsheet)
    db.session.commit()

    return jsonify({"message": "Character sheet deleted"}), 200


@app.route('/charsheet/types', methods=['GET'])
def get_charsheet_types():
    charsheet_types = CharSheetType.query.all()
    return jsonify([{'id': ctype.id, 'name': ctype.name} for ctype in charsheet_types])


@app.route('/charsheet/<id_>/revs', methods=['GET'])
def get_charsheet_revisions(id_):
    revisions = CharSheetRevisions.query \
        .join(CharSheetInstance, CharSheetInstance.id == CharSheetRevisions.csinst_id) \
        .join(CharSheetType, CharSheetInstance.sheet_type_id == CharSheetType.id) \
        .filter(CharSheetInstance.id == id_) \
        .with_entities(
            CharSheetRevisions.rev_id,
            CharSheetRevisions.csinst_id,
            CharSheetRevisions.revision_dttm,
            CharSheetInstance.name.label('charsheet_name'),
            CharSheetType.name.label('charsheet_type_name')
        ).all()

    revision_data = [
        {
            'rev_id': rev.rev_id,
            'csinst_id': rev.csinst_id,
            'revision_dttm': rev.revision_dttm.isoformat(),  # Convert datetime to string
            'charsheet_name': rev.charsheet_name,
            'charsheet_type_name': rev.charsheet_type_name
        } for rev in revisions
    ]

    return jsonify(revision_data)


@app.route('/charsheet/rev/recents', methods=['GET'])
def get_recent_revisions():
    recent_revisions = CharSheetRevisions.query \
        .join(CharSheetInstance, CharSheetInstance.id == CharSheetRevisions.csinst_id) \
        .join(CharSheetType, CharSheetType.id == CharSheetInstance.sheet_type_id) \
        .with_entities(
            CharSheetRevisions.rev_id,
            CharSheetRevisions.csinst_id,
            CharSheetRevisions.revision_dttm,
            CharSheetInstance.name.label('charsheet_name'),
            CharSheetType.name.label('charsheet_type_name')
        ) \
        .order_by(CharSheetRevisions.revision_dttm.desc()) \
        .limit(10) \
        .all()

    revision_data = [
        {
            'rev_id': rev.rev_id,
            'csinst_id': rev.csinst_id,
            'revision_dttm': rev.revision_dttm.isoformat(),
            'charsheet_name': rev.charsheet_name,
            'charsheet_type_name': rev.charsheet_type_name
        } for rev in recent_revisions
    ]

    return jsonify(revision_data)
