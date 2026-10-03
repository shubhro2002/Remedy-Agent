# Autonomous SecOps Auto-Remediator

An enterprise-grade, autonomous Agentic AI system built to detect, audit, and remediate cloud security misconfigurations (such as public S3 buckets) in a completely isolated, simulated AWS environment.

This project demonstrates advanced AI system architecture, featuring multi-node state machines, persistent distributed memory, defense-in-depth guardrails, OpenTelemetry observability, and the Model Context Protocol (MCP).

---

## Agentic Workflow Architecture

The agent operates as a **LangGraph** state machine. It utilizes a ReAct pattern to investigate the environment, drafts a remediation plan, validates it against strict guardrails, and pauses for human approval before executing securely via MCP.

```mermaid
graph TD
    %% Define styles
    classDef startend fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff,rx:20,ry:20;
    classDef llmNode fill:#2b6cb0,stroke:#2c5282,stroke-width:2px,color:#fff;
    classDef logicNode fill:#d69e2e,stroke:#b7791f,stroke-width:2px,color:#fff;
    classDef execNode fill:#c53030,stroke:#9b2c2c,stroke-width:2px,color:#fff;
    classDef db fill:#48bb78,stroke:#276749,stroke-width:2px,color:#fff;

    %% Nodes
    START((START)):::startend
    END_NODE((END)):::startend
    
    Gatekeeper{Incident<br>Already<br>Fixed?}:::logicNode
    Investigator[Investigator Node<br><i>Audit via AWS CLI</i>]:::llmNode
    Drafter[Drafter Node<br><i>Plan Remediation</i>]:::llmNode
    Guardrail[Guardrail Node<br><i>Pydantic Validation</i>]:::logicNode
    HITL{Human-in-the-Loop<br>Approval}:::logicNode
    Executor[Executor Node<br><i>FastMCP Shell</i>]:::execNode
    
    Mongo[(MongoDB Atlas<br>Checkpointer)]:::db

    %% Flow
    START --> Gatekeeper
    Gatekeeper -- Yes (Short Circuit) --> END_NODE
    Gatekeeper -- No --> Investigator
    
    Investigator --> Drafter
    Drafter --> Guardrail
    Guardrail --> HITL
    
    HITL -- Reject --> END_NODE
    HITL -- Approve --> Executor
    Executor --> END_NODE

    %% Memory interactions
    Investigator -. "Save State" .-> Mongo
    Drafter -. "Save State" .-> Mongo
    HITL -. "Freeze/Resume State" .-> Mongo