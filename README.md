# Money Plan App

A personal cashflow tracker built with event sourcing that helps you manage your finances when you get paid. This app records every money movement as an immutable event, enabling you to replay history, audit your cashflow, and answer questions like “How much did I save in Wealthfront last year?”

> **Note:**  
> This project is an evolution of my long-time "Money Plan" concept—a spin on envelope (zero-based) budgeting. While my old spreadsheet worked well for day-to-day budgeting, it lacked a robust history and reporting.

## Overview

- **Purpose:**  
  When you get paid, you create a new Money Plan by recording your initial checking account balance (e.g. Ally Checking) and then allocating funds into one or more Accounts.  
  - **Accounts & Buckets:**  
    - Each **Account** is a shared global entity (e.g. “Wealthfront”, “Apple Card”) that can be used across multiple plans for historical analysis.  
    - An Account is subdivided into one or more **Buckets** (or sub-accounts) that further categorize your funds (e.g. “General Savings”, “House Savings”).  
  - **Editing vs. Commitment:**  
    - A plan may be worked on without any accounts during editing.
    - However, before a plan is committed, it must have at least one account. Additionally, each account must contain at least one bucket. If an account is created without specifying buckets, a default bucket named **"Default"** is automatically added.
  - **Invariant at Commit:**  
    When the plan is committed, the sum of all bucket allocations across all accounts must equal the initial balance.
  - **Notes:**  
    Each plan includes a free-text notes field for additional context.
