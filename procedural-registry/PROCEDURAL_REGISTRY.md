# PROCEDURAL REGISTRY
## Complete Registry of Procedures, Processes, and Workflows

**Date:** 2025-01-03  
**Document Type:** Procedural Registry  
**Scope:** All procedures, processes, and workflows defined across DIESEL COLLECTIVE documentation  
**Status:** Active Registry

---

## EXECUTIVE SUMMARY

This document serves as the **master registry** of all procedures, processes, and workflows defined across the DIESEL COLLECTIVE architecture documentation. It provides a **centralized reference** for operational procedures, activation sequences, build processes, and integration workflows.

**Registry Categories:**
1. **System Activation Procedures**
2. **Build & Deployment Procedures**
3. **Integration Procedures**
4. **Maintenance Procedures**
5. **Troubleshooting Procedures**
6. **Development Procedures**

---

## PART 1: SYSTEM ACTIVATION PROCEDURES

### 1.1 Symbiotic Network Activation Sequence

**Procedure ID:** `PROC-001`  
**Procedure Name:** Symbiotic Network Activation  
**Source Document:** `SYMBIOTIC_NETWORK_ACTIVATION_PLAN.md`  
**Status:** Active  
**Estimated Duration:** 4 weeks

#### Phase 1: Foundation Activation (Week 1)

**Step 1.1: Activate Immersion Engine**
```bash
cd /Volumes/raid0
python3 immersion_engine.py
```
**Purpose:** Builds foundational knowledge map that all other systems depend on  
**Prerequisites:** Python 3.8+, access to knowledge roots  
**Expected Output:** `knowledge_map.json`  
**Validation:** Verify `knowledge_map.json` contains file mappings

**Step 1.2: Activate Vectorization System**
```bash
python3 vectorize_getit.py
```
**Purpose:** Makes all content searchable. Required for MLX RAG Orchestrator  
**Prerequisites:** Immersion Engine completed, GETit directory populated  
**Expected Output:** ChromaDB collections with embeddings  
**Validation:** Verify vector database contains embeddings

**Step 1.3: Load Flow Patterns**
```python
import json
with open('/Volumes/raid0/flow_patterns_20251120.json') as f:
    patterns = json.load(f)
```
**Purpose:** Provides validated frameworks for all decision-making systems  
**Prerequisites:** `flow_patterns_20251120.json` exists  
**Expected Output:** Patterns loaded in memory  
**Validation:** Verify patterns accessible

#### Phase 2: Processing Activation (Week 2)

**Step 2.1: Activate Codex Synthesis**
```bash
python3 codex_synthesis_fast.py
```
**Purpose:** Detects patterns that feed into Syzygy Framework  
**Prerequisites:** Foundation phase complete  
**Expected Output:** Pattern detection active  
**Validation:** Verify patterns being detected

**Step 2.2: Activate MLX RAG Orchestrator**
```bash
python3 mlx_rag_orchestrator.py
```
**Purpose:** Provides high-performance retrieval for all systems  
**Prerequisites:** Vectorization system active  
**Expected Output:** RAG queries returning results  
**Validation:** Test query returns results

**Step 2.3: Activate Workspace Synthesis Tracer**
```bash
python3 workspace_synthesis_tracer.py
```
**Purpose:** Provides visibility into all knowledge flows  
**Prerequisites:** All processing systems active  
**Expected Output:** Tracing data being collected  
**Validation:** Verify traces being recorded

#### Phase 3: Intelligence Activation (Week 3)

**Step 3.1: Integrate Syzygy Framework**
```python
from syzygy_resonance_engine import SyzygyConvergenceOrchestrator

orchestrator = SyzygyConvergenceOrchestrator()
orchestrator.initialize_field()
```
**Purpose:** Enables nonlinear emergence detection  
**Prerequisites:** Codex Synthesis active  
**Expected Output:** Emergent intelligence enabled  
**Validation:** Verify emergence events detected

**Step 3.2: Activate Jimmy Ninja Orchestrator**
```bash
uvicorn jimmy_ninja_orchestrator:app --host 0.0.0.0 --port 8000
```
**Purpose:** Coordinates all distributed systems  
**Prerequisites:** All systems from Phase 1-2 active  
**Expected Output:** Central coordination active  
**Validation:** Verify nodes registering

#### Phase 4: Interface Activation (Week 4)

**Step 4.1: Verify Sovereign RAG Bridge**
```bash
docker ps | grep webui
curl http://192.168.68.52:6333/collections/diesel_collective_memory
```
**Purpose:** Connects human interface to collective memory  
**Prerequisites:** Qdrant running, Open WebUI container running  
**Expected Output:** Bridge connection verified  
**Validation:** Verify search/store operations work

**Step 4.2: Deploy Neuro Insight Engine**
```bash
cd /Users/metal512/Downloads/neuro-insight-engine
python3 -m http.server 8080
```
**Purpose:** Provides beautiful interface for all backend systems  
**Prerequisites:** All backend systems active  
**Expected Output:** Frontend accessible  
**Validation:** Verify UI loads and connects to backend

---

### 1.2 Swarm Core Activation

**Procedure ID:** `PROC-002`  
**Procedure Name:** Swarm Core Activation  
**Source Document:** `activate_swarm_core.sh`  
**Status:** Active  
**Estimated Duration:** 15 minutes

```bash
#!/bin/bash
# Activate Swarm Core

# 1. Verify all nodes accessible
./check_amdblack_specs.sh

# 2. Start Jimmy Ninja Orchestrator
cd /Volumes/raid0
uvicorn jimmy_ninja_orchestrator:app --host 0.0.0.0 --port 8000 &

# 3. Register nodes
curl -X POST http://localhost:8000/register_node \
  -H "Content-Type: application/json" \
  -d '{"node_id": "plane1_control", "status": "online", "cpu_load": 0.15, "ram_usage": 0.23}'

# 4. Verify swarm status
curl http://localhost:8000/status
```

**Validation Steps:**
1. All nodes show "online" status
2. Active agents count > 0
3. Spatial library stats accessible

---

## PART 2: BUILD & DEPLOYMENT PROCEDURES

### 2.1 Local Development Build

**Procedure ID:** `PROC-003`  
**Procedure Name:** Local Development Build  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 5 minutes

```bash
# 1. Install dependencies
npm install

# 2. Start mock API server (optional)
cd mock-api
npm install
npm start &

# 3. Start development server
cd ..
npm run dev
```

**Expected Output:** Development server running on http://localhost:3000  
**Validation:** Verify application loads in browser

---

### 2.2 Production Build

**Procedure ID:** `PROC-004`  
**Procedure Name:** Production Build  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 10 minutes

```bash
# 1. Clean previous build
rm -rf dist

# 2. Install dependencies
npm ci --production=false

# 3. Run tests
npm run test

# 4. Build application
npm run build:prod

# 5. Verify build
ls -lh dist/
```

**Expected Output:** `dist/` directory with optimized assets  
**Validation:** Verify `index.html` and `assets/` directory exist

---

### 2.3 Docker Build

**Procedure ID:** `PROC-005`  
**Procedure Name:** Docker Build  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 15 minutes

```bash
# 1. Build Docker image
docker build -f Dockerfile.prod -t neuro-insight-engine:latest .

# 2. Verify image
docker images | grep neuro-insight-engine

# 3. Run container
docker run -p 8080:80 neuro-insight-engine:latest

# 4. Health check
curl http://localhost:8080/health
```

**Expected Output:** Container running, health check returns "healthy"  
**Validation:** Verify application accessible on port 8080

---

### 2.4 Remote Deployment

**Procedure ID:** `PROC-006`  
**Procedure Name:** Remote Deployment  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 30 minutes

```bash
# 1. Build application
npm run build:prod

# 2. Create deployment archive
tar -czf deployment.tar.gz -C dist .

# 3. Deploy to remote server
export DEPLOY_HOST="example.com"
export DEPLOY_USER="deploy"
export DEPLOY_PATH="/var/www/neuro-insight-engine"
./scripts/deploy.sh production

# 4. Verify deployment
ssh ${DEPLOY_USER}@${DEPLOY_HOST} "curl http://localhost/health"
```

**Expected Output:** Application deployed and accessible  
**Validation:** Verify health check passes on remote server

---

## PART 3: INTEGRATION PROCEDURES

### 3.1 Backend API Integration

**Procedure ID:** `PROC-007`  
**Procedure Name:** Backend API Integration  
**Source Document:** `NEURO_INSIGHT_ENGINE_ENGINEERING_ENHANCEMENTS.md`  
**Status:** Active  
**Estimated Duration:** 2 hours

**Step 1: Configure API Endpoints**
```javascript
// Update src/config/runtime-config.js
const config = {
    apiBaseUrl: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
    wsBaseUrl: process.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
    mlxRAGUrl: process.env.VITE_MLX_RAG_URL || 'http://localhost:8001'
};
```

**Step 2: Implement HTTP Client**
```javascript
// Add ResilientHTTPClient class
// Include retry logic and circuit breaker
```

**Step 3: Integrate WebSocket**
```javascript
// Initialize WebSocket connection
// Handle real-time updates
```

**Step 4: Test Integration**
```bash
# Start backend services
# Test API calls from frontend
# Verify WebSocket connection
```

**Validation:** Verify all API endpoints responding correctly

---

### 3.2 Service Health Check Integration

**Procedure ID:** `PROC-008`  
**Procedure Name:** Service Health Check Integration  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 1 hour

```javascript
// Implement ServiceChecker class
// Check service availability
// Fallback to mock services if needed
```

**Validation Steps:**
1. Service checker detects available services
2. Fallback activates when services unavailable
3. Mock services work correctly

---

## PART 4: MAINTENANCE PROCEDURES

### 4.1 Knowledge Map Update

**Procedure ID:** `PROC-009`  
**Procedure Name:** Knowledge Map Update  
**Source Document:** `immersion_engine.py`  
**Status:** Active  
**Estimated Duration:** 30 minutes

```bash
# 1. Run Immersion Engine
cd /Volumes/raid0
python3 immersion_engine.py

# 2. Verify knowledge map updated
ls -lh knowledge_map.json

# 3. Check file count
python3 -c "import json; data=json.load(open('knowledge_map.json')); print(len(data))"
```

**Frequency:** Weekly or when new files added  
**Validation:** Verify knowledge_map.json updated with new files

---

### 4.2 Vector Database Update

**Procedure ID:** `PROC-010`  
**Procedure Name:** Vector Database Update  
**Source Document:** `vectorize_getit.py`  
**Status:** Active  
**Estimated Duration:** 1 hour (depends on file count)

```bash
# 1. Run vectorization
python3 vectorize_getit.py

# 2. Verify vectors created
# Check ChromaDB collections

# 3. Test retrieval
python3 -c "
from mlx_rag_orchestrator import MacStudioRAG
rag = MacStudioRAG()
results = rag.query_local('test query', top_k=5)
print(results)
"
```

**Frequency:** Weekly or when new content added  
**Validation:** Verify new vectors searchable

---

### 4.3 System Status Check

**Procedure ID:** `PROC-011`  
**Procedure Name:** System Status Check  
**Source Document:** `jimmy_ninja_orchestrator.py`  
**Status:** Active  
**Estimated Duration:** 5 minutes

```bash
# 1. Check Jimmy Ninja status
curl http://localhost:8000/status

# 2. Check all nodes
curl http://localhost:8000/status | jq '.nodes'

# 3. Check active agents
curl http://localhost:8000/status | jq '.active_agents'

# 4. Check queue depth
curl http://localhost:8000/status | jq '.queue_depth'
```

**Frequency:** Daily  
**Validation:** Verify all nodes online, queue depth acceptable

---

## PART 5: TROUBLESHOOTING PROCEDURES

### 5.1 Service Unavailable Troubleshooting

**Procedure ID:** `PROC-012`  
**Procedure Name:** Service Unavailable Troubleshooting  
**Source Document:** Multiple  
**Status:** Active  
**Estimated Duration:** 30 minutes

**Step 1: Check Service Status**
```bash
# Check if service is running
curl http://localhost:8000/status

# Check logs
docker logs <container-name>
# or
journalctl -u <service-name>
```

**Step 2: Check Network Connectivity**
```bash
# Ping service
ping <service-host>

# Check port accessibility
telnet <service-host> <port>
```

**Step 3: Check Configuration**
```bash
# Verify environment variables
env | grep VITE_

# Verify config file
cat public/config.json
```

**Step 4: Enable Fallback**
```bash
# Set useMockServices to true
export VITE_USE_MOCK_SERVICES=true
```

**Validation:** Service accessible or fallback active

---

### 5.2 Build Failure Troubleshooting

**Procedure ID:** `PROC-013`  
**Procedure Name:** Build Failure Troubleshooting  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 1 hour

**Step 1: Check Node Version**
```bash
node -v  # Must be >= 18.0.0
npm -v   # Must be >= 9.0.0
```

**Step 2: Clean Dependencies**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Step 3: Check Build Logs**
```bash
npm run build:prod 2>&1 | tee build.log
# Review build.log for errors
```

**Step 4: Verify Environment Variables**
```bash
cat .env.production
# Ensure all required variables set
```

**Validation:** Build completes successfully

---

### 5.3 WebSocket Connection Issues

**Procedure ID:** `PROC-014`  
**Procedure Name:** WebSocket Connection Troubleshooting  
**Source Document:** `NEURO_INSIGHT_ENGINE_ENGINEERING_ENHANCEMENTS.md`  
**Status:** Active  
**Estimated Duration:** 30 minutes

**Step 1: Verify WebSocket Server Running**
```bash
# Check if WebSocket server accessible
wscat -c ws://localhost:8000/ws
```

**Step 2: Check Firewall Rules**
```bash
# Verify port not blocked
netstat -an | grep 8000
```

**Step 3: Verify URL Configuration**
```javascript
// Check WebSocket URL in config
console.log(runtimeConfig.get('wsBaseUrl'));
```

**Step 4: Enable Polling Fallback**
```javascript
// Fallback to polling if WebSocket fails
// Already implemented in code
```

**Validation:** WebSocket connects or polling fallback active

---

## PART 6: DEVELOPMENT PROCEDURES

### 6.1 Feature Development Workflow

**Procedure ID:** `PROC-015`  
**Procedure Name:** Feature Development Workflow  
**Source Document:** Standard Development Practice  
**Status:** Active  
**Estimated Duration:** Variable

**Step 1: Create Feature Branch**
```bash
git checkout -b feature/new-feature-name
```

**Step 2: Develop Feature**
```bash
# Make changes
# Test locally
npm run dev
```

**Step 3: Write Tests**
```bash
# Add unit tests
npm run test

# Add integration tests
npm run test:integration
```

**Step 4: Code Review**
```bash
# Lint code
npm run lint

# Format code
npm run format

# Create pull request
```

**Step 5: Merge and Deploy**
```bash
# Merge to develop
# Deploy to staging
# Test in staging
# Merge to main
# Deploy to production
```

---

### 6.2 Testing Procedure

**Procedure ID:** `PROC-016`  
**Procedure Name:** Testing Procedure  
**Source Document:** `NEURO_INSIGHT_ENGINE_REMOTE_BUILD_SPEC.md`  
**Status:** Active  
**Estimated Duration:** 30 minutes

```bash
# 1. Run unit tests
npm run test

# 2. Run tests with coverage
npm run test:coverage

# 3. Run integration tests
npm run test:integration

# 4. Run E2E tests
npm run test:e2e

# 5. Verify coverage threshold
# Coverage should be >= 80%
```

**Validation:** All tests pass, coverage meets threshold

---

## PART 7: PROCEDURE INDEX

### By Category

**System Activation:**
- PROC-001: Symbiotic Network Activation
- PROC-002: Swarm Core Activation

**Build & Deployment:**
- PROC-003: Local Development Build
- PROC-004: Production Build
- PROC-005: Docker Build
- PROC-006: Remote Deployment

**Integration:**
- PROC-007: Backend API Integration
- PROC-008: Service Health Check Integration

**Maintenance:**
- PROC-009: Knowledge Map Update
- PROC-010: Vector Database Update
- PROC-011: System Status Check

**Troubleshooting:**
- PROC-012: Service Unavailable Troubleshooting
- PROC-013: Build Failure Troubleshooting
- PROC-014: WebSocket Connection Issues

**Development:**
- PROC-015: Feature Development Workflow
- PROC-016: Testing Procedure

### By Frequency

**Daily:**
- PROC-011: System Status Check

**Weekly:**
- PROC-009: Knowledge Map Update
- PROC-010: Vector Database Update

**As Needed:**
- All other procedures

---

## PART 8: PROCEDURE TEMPLATE

**Procedure ID:** `PROC-XXX`  
**Procedure Name:** [Name]  
**Source Document:** [Document]  
**Status:** [Active/Deprecated/In Development]  
**Estimated Duration:** [Time]  
**Prerequisites:** [List]  
**Steps:** [Numbered steps]  
**Expected Output:** [Description]  
**Validation:** [How to verify success]  
**Troubleshooting:** [Common issues and solutions]  
**Related Procedures:** [Links to related procedures]

---

## CONCLUSION

This procedural registry provides a **centralized reference** for all operational procedures within the DIESEL COLLECTIVE architecture. Procedures are organized by category and include complete implementation details, validation steps, and troubleshooting guidance.

**Registry Status:** Active  
**Last Updated:** 2025-01-03  
**Total Procedures:** 16  
**Next Review:** 2025-02-03

---

**Document Status:** Complete Procedural Registry  
**Maintenance:** Update as new procedures are added  
**Contact:** Operations Team

