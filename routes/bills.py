from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Bill, BillItem, Client
from datetime import datetime
import uuid

bills_bp = Blueprint('bills', __name__, url_prefix='/billing')

@bills_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_bill():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        
        # HTML form se lists uthana
        item_names = request.form.getlist('item_name[]')
        quantities = request.form.getlist('quantity[]')
        mrps = request.form.getlist('mrp[]')

        # 1. Main Bill entry (admin_id ko string mein convert karke)
        new_bill = Bill(
            admin_id=str(current_user.id),
            client_id=client_id,
            bill_number=f"BILL-{uuid.uuid4().hex[:6].upper()}"
        )
        db.session.add(new_bill)
        db.session.flush()

        grand_total = 0
        # 2. Loop through rows
        for i in range(len(item_names)):
            if item_names[i].strip():
                qty = int(quantities[i])
                price = float(mrps[i])
                row_total = qty * price
                grand_total += row_total
                
                item = BillItem(
                    bill_id=new_bill.id, 
                    item_name=item_names[i], 
                    quantity=qty, 
                    mrp=price, 
                    total_price=row_total
                )
                db.session.add(item)

        new_bill.grand_total = grand_total
        db.session.commit()
        
        flash('Bill Created Successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    # Clients fetch karna current user ke liye
    clients = Client.query.filter_by(admin_id=str(current_user.id)).all()
    return render_template('bills/create.html', clients=clients)