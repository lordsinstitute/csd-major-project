# Style Sense --- Generative AI-Powered Fashion Recommendation System

> **Personalized styling · Conversational AI · Visual fashion
> discovery**

Style Sense is a Generative AI-powered fashion recommendation web
application designed to make fashion discovery more personal,
interactive, and convenient. It brings AI-assisted outfit
recommendations, conversational styling guidance, digital wardrobe
management, visual outfit generation, and shopping suggestions into one
platform.

The system considers information such as a user's profile, body type,
skin tone, preferred style, favourite colours, occasion, season, and
other contextual preferences to provide more relevant fashion guidance.

------------------------------------------------------------------------

## Table of Contents

-   [Project Overview](#project-overview)
-   [Problem Statement](#problem-statement)
-   [Objectives](#objectives)
-   [Key Features](#key-features)
-   [Project Modules](#project-modules)
-   [Technology Stack](#technology-stack)
-   [System Architecture](#system-architecture)
-   [Application Workflow](#application-workflow)
-   [Getting Started](#getting-started)
-   [Configuration](#configuration)
-   [Security Notes](#security-notes)
-   [Future Enhancements](#future-enhancements)
-   [Project Team](#project-team)

------------------------------------------------------------------------

## Project Overview

Traditional fashion platforms often focus on browsing history, purchase
history, or popular products. These approaches may not fully account for
an individual's style preferences, body characteristics, occasion,
weather, or seasonal context.

Style Sense aims to move beyond product-only recommendations by
combining personalization with Generative AI. Users can receive outfit
suggestions, ask a conversational AI fashion assistant for advice,
organize clothing in a virtual wardrobe, explore AI-generated fashion
visuals, and discover shopping suggestions.

The platform is designed with separate User and Admin panels. The
administrative side supports user and category management, AI
monitoring, reports, and application analytics.

## Problem Statement

Current fashion discovery experiences can present several limitations:

-   Recommendations may offer limited personalization.
-   Body type, skin tone, preferred style, occasion, weather, and season
    may not be considered together.
-   Users often need to combine individual products manually to create a
    complete outfit.
-   Users may have limited ways to preview an outfit before making a
    purchase.
-   Traditional platforms may not provide conversational fashion
    guidance.
-   Managing and reusing clothes already owned can be difficult without
    a digital wardrobe.

**Proposed approach:** Style Sense combines context-aware fashion
recommendations, conversational AI, visual generation, wardrobe
organization, and shopping support in one application.

## Objectives

-   Provide personalized fashion recommendations using Generative AI.
-   Generate outfit suggestions using user profiles, preferences,
    occasions, and seasonal context.
-   Offer conversational fashion assistance.
-   Support AI-generated fashion images and short video concepts.
-   Enable users to organize clothing and saved outfits digitally.
-   Help users explore suitable shopping suggestions.
-   Provide secure User and Admin interfaces.
-   Support administrative monitoring, reporting, and analytics.
-   Encourage informed purchasing and better use of existing wardrobe
    items.

## Key Features

  -----------------------------------------------------------------------
  Feature                             Description
  ----------------------------------- -----------------------------------
  AI Fashion Stylist                  Suggests outfits and styling ideas
                                      based on user preferences and
                                      context.

  Conversational AI Assistant         Provides natural-language fashion
                                      guidance and answers
                                      fashion-related questions using the
                                      Groq API.

  AI Image Generation                 Uses Hugging Face models to create
                                      visual representations of fashion
                                      ideas.

  AI Fashion Video Generation         Supports the generation of short
                                      fashion showcase videos using AI
                                      models.

  Virtual Try-On                      Provides a way to visualize
                                      recommended outfits on user images.

  Virtual Wardrobe                    Lets users upload, organize, save,
                                      and manage clothing and outfits.

  Smart Shopping                      Helps users discover fashion
                                      products, accessories, brands, and
                                      curated suggestions.

  User Profile & Settings             Stores personal details and fashion
                                      preferences used for
                                      personalization.

  Admin Portal                        Supports user, category, content,
                                      and system management.

  Reports & Analytics                 Helps administrators monitor
                                      activity, AI usage,
                                      recommendations, and platform
                                      performance.
  -----------------------------------------------------------------------

## Project Modules

The project is organized into the following modules:

1.  **User Authentication and Profile Management** --- registration,
    login, sessions, user details, and personalization preferences.
2.  **AI Fashion Recommendation** --- analyzes profile information,
    favourite colours, style, occasion, season, and contextual
    preferences to suggest outfits.
3.  **AI Fashion Assistant** --- provides conversational styling advice
    and fashion-related responses.
4.  **AI Image Generation** --- generates fashion images from
    AI-generated prompts and outfit recommendations.
5.  **Virtual Try-On** --- supports visualization of generated outfits
    on user images.
6.  **Virtual Wardrobe** --- manages uploaded clothing, saved outfits,
    and wardrobe-based combinations.
7.  **Smart Shopping** --- presents relevant products, clothing,
    accessories, brands, and wishlist functionality.
8.  **AI Fashion Video Generation** --- supports short fashion showcase
    videos from generated visuals and styling prompts.
9.  **User Settings** --- manages profile details, fashion preferences,
    notifications, privacy options, and account settings.
10. **Reports and Analytics** --- presents user activity, recommendation
    history, AI usage, trends, and system reports.
11. **Admin Portal** --- provides administrative controls for users,
    categories, AI monitoring, logs, reports, and system configuration.

## Technology Stack

  -----------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Programming Language    Python 3.11.9           Main application
                                                  development

  Web Framework           Django                  Backend and web
                                                  application framework

  Database                MySQL 8                 User profiles,
                                                  preferences, wardrobe
                                                  data, history, and
                                                  application records

  Conversational AI       Groq API                Natural-language
                                                  fashion assistance and
                                                  styling guidance

  Generative / Multimodal Hugging Face models     AI-generated fashion
  AI                                              images and video
                                                  capabilities

  Frontend Styling        Tailwind CSS            Responsive interface
                                                  styling

  UI Design               Glassmorphism           Visual design approach

  Access Control          Authentication and      Separates and protects
                          Role-Based Access       user and administrator
                          Control (RBAC)          functionality
  -----------------------------------------------------------------------

## System Architecture

Style Sense follows a layered application design:

``` mermaid
flowchart TB
    U["User Interface<br/>Web Application"]
    A["Admin Panel"]
    APP["Application Layer<br/>Django"]
    AI["AI Layer<br/>Groq API + Hugging Face Models"]
    DB[("Data Layer<br/>MySQL 8")]
    FS["File Storage<br/>Uploaded and Generated Media"]

    U --> APP
    A --> APP
    APP <--> AI
    APP <--> DB
    APP <--> FS
```

### Architecture Layers

-   **Presentation Layer:** User-facing web application and
    administrative interface.
-   **Application Layer:** Django handles application logic,
    authentication, profiles, wardrobe operations, recommendations, and
    administration.
-   **AI Layer:** Groq API supports conversational fashion assistance;
    Hugging Face models support visual generation capabilities.
-   **Data Layer:** MySQL 8 stores application data such as profiles,
    preferences, wardrobe records, recommendation history, and
    analytics-related information.
-   **Media Storage:** Stores user-uploaded and AI-generated media, such
    as clothing images and generated visuals.

## Application Workflow

``` mermaid
flowchart LR
    A["User Registration / Login"] --> B["Complete Profile & Preferences"]
    B --> C["AI Analysis"]
    C --> D["Personalized Outfit Recommendations"]
    D --> E["AI Visual Generation"]
    E --> F["Wardrobe / Virtual Try-On"]
    F --> G["Shopping Suggestions"]
    G --> H["Conversational AI Support"]
```

1.  The user registers or logs in.
2.  The user provides profile details and fashion preferences.
3.  The system analyzes the available profile and contextual
    information.
4.  The recommendation process generates suitable outfit suggestions and
    styling advice.
5.  AI services support visual exploration through generated fashion
    images and, where configured, videos.
6.  Users can save and organize outfits in the Virtual Wardrobe.
7.  Users can explore virtual try-on and shopping features.
8.  The conversational assistant provides additional fashion guidance.

## Getting Started

The exact setup commands and configuration depend on the Django project
structure in this repository. The following is a general setup
checklist.

### Prerequisites

-   Python 3.11.9
-   MySQL 8
-   pip
-   Git
-   A Groq API key for conversational AI functionality
-   Hugging Face access or credentials if required by the selected
    models

### Setup

1.  **Clone the repository**

    ``` bash
    git clone <YOUR_GITHUB_REPOSITORY_URL>
    cd <YOUR_PROJECT_DIRECTORY>
    ```

2.  **Create and activate a virtual environment**

    Windows PowerShell:

    ``` powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```

    macOS / Linux:

    ``` bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**

    If the repository contains a `requirements.txt` file:

    ``` bash
    pip install -r requirements.txt
    ```

4.  **Configure MySQL**

    -   Create a MySQL database for the application.
    -   Configure the database connection in the Django settings or
        environment configuration used by the project.
    -   Use the database name, username, password, host, and port
        expected by the application.

5.  **Configure AI services**

    -   Add the Groq API key and any required Hugging Face credentials
        through the project's environment configuration.
    -   Use the exact environment variable names expected by the
        application.
    -   Do not commit API keys or other secrets to GitHub.

6.  **Apply database migrations**

    For a standard Django project:

    ``` bash
    python manage.py migrate
    ```

7.  **Start the development server**

    For a standard Django project:

    ``` bash
    python manage.py runserver
    ```

    Open the local address shown in the terminal (usually
    `http://127.0.0.1:8000/`).

> **Note:** These are standard Django setup steps, not a verified
> description of the repository's current file structure. Adjust the
> commands to match the actual project files and settings.

## Configuration

Before running the application, configure:

-   MySQL database connection details.
-   Groq API credentials.
-   Hugging Face credentials or model configuration, if required.
-   Django secret key and deployment-specific settings.
-   Media upload and storage settings.

Keep credentials in environment variables or a local environment file
that is excluded from version control. A safe `.env.example` may be
committed with placeholder values, but never commit a real `.env` file
or API key.

## Security Notes

-   Keep API keys and database passwords out of source control.
-   Use Django's authentication and permission mechanisms to protect
    user and administrator functionality.
-   Apply role-based access control to administrative operations.
-   Validate uploaded files and user input.
-   Configure secure production settings before deployment, including
    secret management, HTTPS, and appropriate allowed hosts.
-   Handle personal profile information and uploaded images responsibly.

## Future Enhancements

Potential future improvements identified for the project include:

-   More advanced personalization using ratings, clicks, saved outfits,
    and user feedback.
-   Hybrid recommendation models combining content-based, collaborative,
    and context-aware methods.
-   More realistic virtual try-on with improved garment fit and support
    for different body types.
-   Live e-commerce catalog, stock, pricing, and checkout integration.
-   Android and iOS applications.
-   Stronger privacy, explainability, bias testing, and secure data
    handling.

## Project Team

**Department:** Computer Science and Engineering (Data Science) ---
CSD-A\
**Project Environment:** MANAC Infotech\
**Supervisor:** Zainab Begum

-   Syed Aijaz
-   **Syed Mohammed Saif Ali**
-   Shaik Afzal Rakheem

------------------------------------------------------------------------

## Responsible Technology

Style Sense also aligns with:

-   **SDG 12 --- Responsible Consumption and Production:** Digital
    wardrobe management can encourage better utilization of existing
    clothing and more informed purchasing decisions.
-   **SDG 9 --- Industry, Innovation and Infrastructure:** The project
    explores the use of Generative AI and intelligent digital
    technologies in fashion.

------------------------------------------------------------------------

*Style Sense --- A smarter way to discover personal style.*
