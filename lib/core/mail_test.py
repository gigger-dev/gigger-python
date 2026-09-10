from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

if __name__ == "__main__":
    import os

    message = Mail(
        from_email="no-reply@gigger.art",
        to_emails="b14cknc0d3@gmail.com",
        subject="Sending with Twilio SendGrid is Fun",
        html_content="<strong>and easy to do anywhere, even with Python</strong>",
    )
    message.template_id = "d-e94dcde1e17c46adaf2c08bb0c36e3d8"
    message.dynamic_template_data = {
        "company_name": "Gigger",
        "otp": "439539",
        "valid_time": "30",
        "recipient_email": "b14cknc0d3@gmail.com",
    }
    try:
        print(os.environ.get("SENDGRID_API_KEY"))
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)  # type: ignore
