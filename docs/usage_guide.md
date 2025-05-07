# 1. 🔄 Usage Guide

## How to Use `pdf-emailer-func`

### Endpoint
```
POST https://pdf-emailer-func.azurewebsites.net/api/generate-newsletter?code=YOUR_FUNCTION_KEY
```

### Required Headers
```
Content-Type: application/json
```

### Sample Payload
```json
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "title": "🏆 Recover Faster, Train Harder",
  "audience": "martial artists looking to boost recovery",
  "stats": "studies show 85% of athletes improved recovery with supplements",
  "tone": "witty and hype",
  "cta": "Listen to our podcast for more insights",
  "cta_note": "like and subscribe to our social media",
  "custom_prompt": "write a newsletter for a martial arts gym",
  "recipients": "email@example.com"
}
```

### Output
- Sends an email
- HTTP 200 OK with newsletter preview

### Environment Variables
- `.env` file includes SMTP, OpenAI, and Azure credentials.
