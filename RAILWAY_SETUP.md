# Railway Deployment Setup

## Environment Variables

For the email notifications to work on Railway, you need to set the following environment variables in your Railway project:

1. Go to your Railway project dashboard
2. Click on your project name
3. Navigate to the **Variables** tab
4. Add the following variables:

### Required Variables

| Variable          | Value              | Example                                                 |
| ----------------- | ------------------ | ------------------------------------------------------- |
| `SENDER_EMAIL`    | Your Gmail address | `your-email@gmail.com`                                  |
| `SENDER_PASSWORD` | Gmail App Password | (see below)                                             |
| `SMTP_HOST`       | SMTP server        | `smtp.gmail.com`                                        |
| `SMTP_PORT`       | SMTP port          | `587` (use 587 for STARTTLS — more reliable on Railway) |
| `SECRET_KEY`      | Flask session key  | Any random string                                       |

### Getting Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App passwords**
4. Select Mail and Windows Computer
5. Google will generate a 16-character password
6. Use this password in the `SENDER_PASSWORD` variable (not your regular Gmail password)

### Example Configuration

```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SECRET_KEY=your-secret-key-here
```

## Testing

After deployment on Railway:

1. Log in with credentials: `admin` / `password123`
2. Add a new task
3. Check the server logs for email sending status

Look for messages like:

- `[SUCCESS] Sent notification to...` - Email sent successfully
- `[ERROR]` - Email sending failed (check credentials)

## Troubleshooting

### Email not sending locally

- Make sure `SENDER_EMAIL` and `SENDER_PASSWORD` are set (or use the hardcoded defaults)
- Check that 2-Step Verification is enabled on Gmail
- Verify you're using an App Password, not your regular Gmail password

### Email not sending on Railway

- Confirm all environment variables are set in Railway dashboard
- Check Railway logs for error messages
- Ensure the Remote SMTP server is accessible (port 465 should be open)
