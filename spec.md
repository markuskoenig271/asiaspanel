# Asia's Panel – Azure Project Setup

## 1. Project Goal and Specification

**Objective:**  
Build a lightweight **real-time translator / onboarding panel app** (“Asia’s Panel”) that runs entirely in Azure.  
It allows a user (e.g., your girlfriend or test participant) to:

- Select between several **AI voice options** (male/female, language tone, etc.)
- Interact in **real-time** using OpenAI’s models for translation and text-to-speech
- Operate through a **simple web interface**
- Store minimal data (voice configs, logs) in Azure Blob Storage
- Run with minimal cost (few friends using it twice a week)

**Architecture Overview**

| Layer | Azure Service | Purpose |
|-------|----------------|----------|
| Frontend | **Static Web App** | Web interface (HTML/JS, or React later) |
| Backend | **Azure Function App** | Logic + OpenAI integration |
| Storage | **Azure Blob Storage** | Config files, small voice data |
| Domain | `www.asiaspanel.ch` | Custom web address |
| Auth / API | OpenAI API Key | GPT-4 / Audio models |
| Infrastructure | Pay-As-You-Go Subscription | Cheap, serverless setup |

**Technical Goals**
- Run with free or minimal pay-as-you-go usage.
- Keep everything under one resource group.
- Use VS Code for development and deployment.
- Enable future Terraform automation once stable.
