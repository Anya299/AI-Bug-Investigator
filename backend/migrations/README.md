# AI Bug Investigator

An AI-powered debugging assistant that converts raw bug descriptions and stack traces into structured investigation reports.

## Features

✅ AI Root Cause Analysis  
✅ Stack Trace Understanding  
✅ Fix Recommendations  
✅ Prevention Suggestions  
✅ JWT Authentication  
✅ Redis Caching  
✅ Rate Limiting  
✅ Database Storage  
✅ Prompt Version Tracking  


## Architecture

User
 |
FastAPI Backend
 |
AI Model
 |
Database + Redis Cache


## Tech Stack

Backend:
- FastAPI
- Python
- SQLAlchemy

AI:
- OpenRouter LLM
- Prompt Engineering

Database:
- SQLite/PostgreSQL

Caching:
- Redis


## API Endpoints

POST /auth/register

POST /auth/login

POST /analyze-bug

GET /health

GET /cache/stats