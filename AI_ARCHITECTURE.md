# AI Architecture Note: Eluno Eyewear OMS

This document details the Artificial Intelligence models and APIs integrated into the Eluno system and the rationale behind their selection.

## 1. Prescription Parsing: Google Gemini 3.5-flash

### **What was used?**
The system uses the **Google Gemini 3.5-flash** API via the `google-generativeai` SDK to process uploaded prescription PDFs and images.

### **Why this choice?**
*   **Multimodal Excellence**: Gemini 3.5-flash excels at "Vision-to-JSON" tasks. It can accurately read handwritten or complex printed prescriptions and map them to our internal data structure.
*   **Native JSON Mode**: By using `response_mime_type: "application/json"`, we ensure the model returns structured data that can be directly consumed by the backend without fragile regex parsing.
*   **Low Latency & Cost**: The "Flash" variant was chosen over "Pro" because it provides sub-second response times and significantly lower operational costs while maintaining the high accuracy required for extraction.
*   **Intelligent Logic**: The model doesn't just extract text; it applies logic (e.g., "If `add_power` > 0, suggest `Progressive` lenses"), reducing manual effort for the ops team.

---

## 2. SLA Risk Prediction: Scikit-Learn RandomForest

### **What was used?**
A **RandomForestClassifier** (Scikit-Learn) trained on historical operational data, stored as `sla_model.pkl` and `encoders.pkl`.

### **Why this choice?**
*   **Local Execution & Privacy**: Unlike LLMs, this model runs locally on the backend server. This ensures low latency and keeps sensitive operational data within the application boundary.
*   **Tabular Data Performance**: RandomForest is an industry standard for tabular data classification. It effectively captures non-linear relationships between variables like "Rework Count," "Inventory Level," and "Current Stage."
*   **Interpretability**: It provides "Feature Importance" metrics, allowing us to understand which factors (e.g., QC failures vs. Store Location) most heavily influence SLA breaches.
*   **Reliability**: It provides a stable **Breach Probability** score (0.0 to 1.0). By using `predict_proba`, we can set precise thresholds for automated alerts (e.g., alerting only when the probability exceeds 80%).

---

## AI Integration Flow

1.  **Ingestion**: User uploads a prescription.
2.  **Extraction (Gemini)**: Gemini extracts the lens power and suggests a lens type.
3.  **Real-time Monitoring**: As the order moves through stages, the **RandomForest** model re-evaluates the breach risk.
4.  **Proactive Alerting**: If the local ML model predicts a high risk (>80%), the system triggers an automated email alert *before* the breach actually occurs.

---

## Future Roadmap
*   **Fine-tuning**: Transition from Gemini-Flash to a fine-tuned small language model (SLM) for specialized medical terminology.
*   **Dynamic Retraining**: Implement a pipeline to retrain the RandomForest model every 30 days based on new production data to prevent model drift.
