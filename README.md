# GroundedIQ

**Enterprise Retrieval-Augmented Generation (RAG) Platform**

GroundedIQ is an enterprise-grade Retrieval-Augmented Generation (RAG) system designed to enable reliable, explainable AI-powered knowledge workflows. It focuses on delivering accurate, grounded responses from internal document corpora while minimizing hallucinations through structured retrieval, evaluation, and refusal mechanisms.

---

## Overview

Modern organizations struggle to operationalize AI over internal knowledge due to unreliable outputs, poor retrieval quality, and lack of evaluation. GroundedIQ addresses these challenges by combining:

- Structured ingestion pipelines
- Metadata-aware retrieval
- Relevance filtering and reranking
- Grounded prompt construction
- Explicit refusal logic
- Evaluation and observability

The system is designed to mirror real-world enterprise constraints including scalability, auditability, and controlled access to information.

---

## Key Features

### Reliable Retrieval

- Vector-based semantic search using pgvector
- Metadata-aware filtering (domain, source, access level)
- Reranking for improved precision

### Grounded Responses

- Context-driven prompt construction
- Source citation for all responses
- Strict grounding in retrieved evidence

### Hallucination Mitigation

- Relevance thresholds for context inclusion
- Minimum support requirements
- Refusal behavior when evidence is insufficient

### Evaluation Framework

- Benchmark dataset for testing
- Metrics including:
  - Precision / Recall
  - Groundedness
  - Refusal accuracy
- Repeatable evaluation runs for system tuning

### Enterprise-Oriented Design

- Modular architecture (ingestion, retrieval, generation)
- Designed for secure, scalable deployment
- Supports future RBAC and audit logging extensions

---

## Architecture

GroundedIQ is structured as a modular system:

Frontend (React)
↓
API Layer (FastAPI)
↓
Retrieval Pipeline

- Query embedding
- Vector search (pgvector)
- Metadata filtering
- Reranking
- Relevance thresholding
  ↓
  Prompt Builder
  ↓
  LLM Generation
  ↓
  Response with citations + confidence

### Ingestion Pipeline

Raw Documents
↓
Parsing (PDF, DOCX, Markdown, Text)
↓
Normalization
↓
Chunking (with overlap)
↓
Metadata Enrichment
↓
Embedding Generation
↓
Storage (PostgreSQL + pgvector)

--

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React + TypeScript (Vite)
- **Database:** PostgreSQL with pgvector
- **Embeddings / LLM:** OpenAI (configurable)
- **Containerization:** Docker
- **Evaluation:** Custom benchmark framework

---

## Repository Structure

apps/
api/ # FastAPI backend (ingestion, retrieval, generation)
web/ # React frontend
infra/
docker/ # Container configuration
db/ # Database initialization
docs/ # Architecture and design decisions
scripts/ # Ingestion and evaluation scripts
sample_data/ # Example documents for ingestion
packages/
eval-dataset/ # Benchmark questions and expected outputs

---

## Retrieval Strategy

GroundedIQ uses a multi-stage retrieval pipeline:

1. **Initial Retrieval**
   - Top-K semantic matches via vector search

2. **Metadata Filtering**
   - Domain, source type, and access-level constraints

3. **Reranking**
   - Semantic reranker improves relevance ordering

4. **Thresholding**
   - Only high-confidence chunks are used

5. **Support Validation**
   - Minimum number of supporting chunks required

This ensures responses are based on strong, relevant evidence.

---

## Prompting Strategy

The system enforces:

- Answers must be derived from provided context
- All responses must include citations
- No unsupported inference beyond retrieved data
- Refusal when evidence is insufficient

---

## Evaluation

GroundedIQ includes a built-in evaluation framework:

### Test Cases

- Answerable questions
- Multi-hop reasoning
- Ambiguous queries
- No-answer scenarios
- Conflicting evidence cases

### Metrics

- Retrieval precision / recall
- Groundedness of responses
- Citation accuracy
- Refusal correctness

Evaluation runs are repeatable and designed to guide system improvements.

---

## Getting Started

### Prerequisites

- Docker
- Python 3.11+
- Node.js 20+
- OpenAI API key

### Setup

```bash
# Start database
docker compose up -d

# Start backend
cd apps/api
poetry install
poetry run uvicorn app.main:app --reload

# Start frontend
cd apps/web
pnpm install
pnpm dev
```

Ingest Sample Data

```bash
cd apps/api
poetry run python ../../scripts/seed_documents.py
```

###

Roadmap
Embedding optimization and hybrid search (BM25 + vector)
Role-based access control (RBAC)
Query rewriting and intent classification
Observability integration (tracing, metrics dashboards)
Kubernetes deployment configuration
Advanced evaluation automation
Design Principles

GroundedIQ is built around several core principles:

Reliability over fluency — better to refuse than hallucinate
Transparency — every answer should be explainable
Modularity — components can evolve independently
Evaluation-driven development — measure, then improve
Enterprise readiness — security, scale, and governance matter

### Status

🚧 Actively under development

Core ingestion, retrieval, and system architecture are in place, with ongoing work on evaluation, optimization, and advanced retrieval strategies.

Author

John Moore
Engineering Executive | AI Systems & Platform Architect
