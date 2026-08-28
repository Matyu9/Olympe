from Utils.verify_login import login_required
from Utils.email_utils import send_test_email
from flask import redirect, url_for, request


@login_required(permission='edit_smtp_config')
def smtp_test_cogs(database):
    if request.method == 'POST':
        send_test_email(database)
        return redirect(url_for('smtp_config'))
    else:
        return redirect(url_for('smtp_config'))
