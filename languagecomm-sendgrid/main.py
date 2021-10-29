import sendgrid
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import Mail, Email, To, Content
from google.cloud import translate_v2 as translate
import email
import datetime
import imaplib
import mailbox
from flask import Flask, render_template, request, redirect, session, url_for
import secrets

app = Flask(__name__)
#needed for session variables support
secret = secrets.token_urlsafe(32)
app.secret_key = secret

translate_client = translate.Client()


#route/function to login to imap for the reading process. 
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        #session needed to carry over session variables to other function/url, namely readEmails()
        session['user_email'] = request.form.get('user_email')
        session['user_password'] = request.form.get('user_password')
        return redirect(url_for('readEmails'))
    return render_template('login.html')
    
@app.route('/read')
def readEmails():
    emails = []
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(session['user_email'], session['user_password'])
    mail.list()
    mail.select('inbox')
    result, data = mail.uid('search', None, "UNSEEN") # (ALL/UNSEEN)
    i = len(data[0].split())

    for x in range(i):
        latest_email_uid = data[0].split()[x]
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        # result, email_data = conn.store(num,'-FLAGS','\\Seen') 
        # this might work to set flag to seen, if it doesn't already
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        # Header Details
        date_tuple = email.utils.parsedate_tz(email_message['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            local_message_date = "%s" %(str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))

        # Body details
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
            else:
                continue
        translated_subject = translate_client.translate(subject, target_language='en')
        translated_body = translate_client.translate(body.decode('utf-8'), target_language='en')
        messagedict = {
            "from": email_from,
            "to": email_to,
            "date": local_message_date,
            "subject": translated_subject['translatedText'],
            "body": translated_body['translatedText']
        }
        emails.append(messagedict)
    return render_template('read.html', emails=emails)

@app.route('/', methods=['GET', 'POST'])
def sendTranslatedEmail():
    if request.method == 'POST':
      from_email = request.form['from_email']
      to_email = request.form['to_email']
      subject = request.form['subject']
      body = request.form['body']
      language = request.form['language']
      session['translatedSubject'] = translate_client.translate(subject, target_language=language)
      session['translatedBody'] = translate_client.translate(body, target_language=language)
      sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
      mail = Mail(from_email, to_email, session['translatedSubject']['translatedText'], session['translatedBody']['translatedText'])
      #print(session['translatedSubject']['translatedText'])

      # Get a JSON-ready representation of the Mail object
      mail_json = mail.get()

      # Send an HTTP POST request to /mail/send
      response = sg.client.mail.send.post(request_body=mail_json)
      print(response.status_code)
      print(response.headers)
      return redirect("/sent")
    else: 
      return render_template('index.html')

@app.route('/sent')
def sent():
  return render_template('sent.html', translatedSubject=session['translatedSubject']['translatedText'], translatedBody=session['translatedBody']['translatedText'])





if __name__ == '__main__':
    app.run(debug=True)