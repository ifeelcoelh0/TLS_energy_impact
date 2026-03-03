# Final Project Report Structure

## 1. Introduction
- Context of IoT devices and energy constraints
- Importance of secure communication
- Motivation for studying TLS energy impact
- Objectives of the project

## 2. Background
- IoT communication protocols
- HTTP vs HTTPS
- TLS handshake overview
- Energy consumption in embedded systems
- Related work

## 3. System Architecture
- Experimental setup overview
- ESP32 as experimental client
- FastAPI backend as data ingestion system
- Data storage model (runs and messages)
- Network configuration

## 4. Experimental Design
- Independent variables
  - TLS enabled vs disabled
  - New connection vs keepalive
- Dependent variables
  - Energy per message
  - Latency per message
  - Overhead
- Controlled variables
- Run definition
- Scenario definition
- Payload size
- Messages per run
- Runs per scenario

## 5. Implementation
### 5.1 ESP32 Firmware
- State machine
- Message format
- Latency measurement method
- Energy measurement method

### 5.2 Backend System
- API design
- Data validation
- Database schema
- Run summary endpoint

## 6. Results
- Per scenario statistics
- Latency comparison
- Energy comparison
- Overhead analysis
- Graphs and tables

## 7. Discussion
- Interpretation of results
- Impact of TLS handshake
- Impact of keepalive
- Limitations
- Experimental noise sources

## 8. Conclusion
- Summary of findings
- Practical implications
- Future work

## 9. References
