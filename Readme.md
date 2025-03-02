# **CardioX AI**

### **AI-Powered Insights for Cardiovascular Wellness**

## **Inspiration**

Cardiovascular diseases (CVDs) remain the leading cause of death worldwide, yet many cases are preventable with early risk detection and proactive management. We developed **CardioX AI** to empower individuals and healthcare providers with an AI-driven tool that not only predicts cardiovascular risk but also provides actionable insights through data visualization, intelligent reporting, and an interactive AI assistant.

## **What It Does**

CardioX AI leverages **XGBoost** to predict cardiovascular disease risk based on 13 key factors such as age, hypertension, cholesterol levels, smoking status, and other lab test metrics. After generating a risk score, the app produces **detailed charts and analytical reports** powered by an **LLM (Large Language Model)**. Users can also interact with an **AI-powered agent** to receive personalized explanations, insights, and recommendations for cardiovascular health management.

## **How We Built It**

### **Backend for CDS Hooks** (Django)

We built the backend using **Django**, integrating **WSGI** for handling prefetched chunked data and **ASGI** to support WebSockets for real-time AI interactions.

1. **Data Processing**: Retrieves patient data from **MeldX** using **CDS Hooks** and the **FHIR** standard.
2. **AI for Prediction**: Integrates an trained **XGBoost model** for machine learning-based cardiovascular risk assessment.
3. **CDS Hooks Cards**: Sends risk prediction results as **CDS Hooks Cards** with alerts and information to **MeldX**.
4. **LLM Integration**: Deploys **Llama-3.2-1B** to generate analytical reports and support conversational AI for the frontend.

### **Frontend for SMART App** (Vite + React)

The frontend was developed using **Vite and React** for a fast and responsive user experience.

1. **SMART App Integration**: Connects securely to **MeldX** via **SMART on FHIR**, using **OIDC** for authentication.
2. **Patient Data Visualization**: Displays **CVD-related patient data** through interactive charts.
3. **AI-Generated Analysis Report**: Presents **LLM-generated reports** summarizing patient health trends.
4. **Conversational AI Agent**: Provides an **interactive UI** where users can ask questions and receive real-time responses.

### **Prediction Model**

- **Trained XGBoost model** using **NIH NHANES (2017-2020) data** with 13 key attributes to assess cardiovascular risk.

## **Challenges We Ran Into**

- **Data Prefetching**: Django does not natively support chunked data processing. We addressed this by using **Gunicorn as a middleware** with **WSGI** to handle prefetched data in chunks.
- **WebSockets for AI Agent**: Since the conversational AI requires a persistent connection, we implemented **Daphne and ASGI** to enable real-time message exchange asynchronously.
- **FHIR Data Mapping**: Converting **FHIR** patient data into a structured format suitable for machine learning required significant preprocessing.
- **Seamless Frontend-Backend Communication**: Ensuring real-time updates and smooth interactions between **Django (backend)** and **Vite (frontend)**.
- **Model Optimization**: Fine-tuning the **XGBoost model** to balance **accuracy, interpretability, and computational efficiency**.
- **LLM Performance**: Optimizing response time and **enhancing contextual understanding** while running the model locally.

## **Accomplishments That We're Proud Of**

✅ Integratoin **CDS hooks with SMART App** based on Django and Vite framework.
✅ Successfully **trained and deployed** an **XGBoost model** for cardiovascular risk prediction.  
✅ Implemented **dynamic report generation** using an **LLM** for clear and actionable insights.  
✅ Developed an **AI-powered conversational assistant** to improve user engagement and understanding.  
✅ Achieved **seamless integration** between the **ML model, report generation, and conversational AI**.

## **What We Learned**

- **OAuth 2.0, FHIR 2.0, and SMART on FHIR** protocols, and how to securely retrieve patient data via **OIDC authentication**.
- **Integrating backend (Django) and frontend (React/Vite) frameworks** for real-time data exchange.
- **Optimizing AI models for local deployment** while maintaining efficiency and accuracy.
- **Best practices for handling FHIR data** in a predictive analytics environment.
- **User-centric design** for healthcare applications to improve accessibility and real-world impact.

## **What's Next for CardioX AI**

🔒 **Secure Patient Data Storage**: Explore privacy-preserving storage solutions (e.g., **Canisters on ICP**) for patient data.  
☁️ **Cloud Deployment**: Deploy both the **frontend and backend** on cloud infrastructure for scalability.  
👥 **Multi-User Support**: Enable simultaneous access for multiple users across different roles (e.g., patients, doctors).  
📊 **Expanding Predictive Capabilities**: Incorporate **ECG, imaging, and genetic data** for a more comprehensive risk assessment.  
🤖 **Enhanced AI Recommendations**: Improve the **LLM-powered AI assistant** to offer **personalized lifestyle and treatment suggestions**.
