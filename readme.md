```
azure-pdf-emailer/
├── main.tf                  # Main Terraform configuration file
├── variables.tf             # Terraform variables definition
├── outputs.tf               # Terraform outputs definition
├── terraform.tfvars         # Terraform variables values (excluded from git)
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── function_app/
│   ├── function_app.py      # Main Azure Function code
│   ├── host.json            # Azure Function host configuration
│   ├── local.settings.json  # Local development settings (excluded from git)
│   ├── requirements.txt     # Python dependencies
│   └── .funcignore          # Azure Functions ignore file
├── scripts/
│   ├── deploy.sh            # Deployment automation script
│   └── test_email.py        # Script to test email functionality
├── docs/
│   ├── cost_analysis.md     # Detailed cost analysis
│   ├── setup_guide.md       # Step-by-step setup instructions
│   └── images/              # Documentation images
│       └── architecture.png # System architecture diagram
└── templates/
    └── email_template.html  # HTML template for emails
```