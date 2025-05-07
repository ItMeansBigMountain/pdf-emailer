| **Step**                | **Command**           | **Description**                                                                                   |
|-------------------------|-----------------------|---------------------------------------------------------------------------------------------------|
| **Initialize Terraform**| `terraform init`      | Downloads provider plugins and sets up the working directory for Terraform.                      |
| **Plan Changes**         | `terraform plan`     | Creates an execution plan by comparing the desired state with the current infrastructure state.   |
| **Apply Changes**        | `terraform apply`    | Provisions resources in Azure based on the execution plan.                                        |

---

| **Provisioned Resource**      | **Purpose**                                                                                     | **Details**                                                                                     |
|--------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Azure Resource Group**       | Logical container for grouping related Azure resources.                                        | Configured with a name (`pdf-emailer-rg`) and location (e.g., `Central US`).                   |
| **Azure Storage Account**      | Stores files, logs, or other data required by the Function App.                                | Configured with a unique name (`pdfemailerstorage`), `Standard` tier, and `LRS` replication.   |
| **Azure Storage Container**    | Stores generated PDFs for the application.                                                    | Configured as a private container named `generated-pdfs`.                                      |
| **Azure Service Plan**         | Provides the compute resources for the Function App.                                           | Configured as a Linux-based Consumption Plan (`Y1` SKU).                                       |
| **Azure Linux Function App**   | Hosts the serverless application logic for the `pdf-emailer` project.                          | Configured with Python runtime (`3.10`), environment variables, and linked to the Storage Account. |
| **Azure Application Insights** | Provides monitoring and logging for the Function App.                                          | Configured with a name (`pdf-emailer-func-ai`) and linked to the Function App.                 |

---

| **Additional Notes**           | **Description**                                                                                 |
|--------------------------------|-------------------------------------------------------------------------------------------------|
| **Environment Variables**      | Includes SMTP settings, API keys (OpenAI, Anthropic, Cohere, HuggingFace), and scheduling info. |
| **State Management**           | Terraform tracks infrastructure state in `terraform.tfstate`. Store securely for collaboration. |
| **Lock File**                  | `.terraform.lock.hcl` ensures consistent provider versions across environments.                 |
| **Outputs**                    |  API BaseURL = `pdf-emailer-func.azurewebsites.net`         |