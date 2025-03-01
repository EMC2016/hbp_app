import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from scipy.special import expit
from imblearn.over_sampling import SMOTE
import numpy as np

df_nhanes = pd.read_csv("nhanes_hypertension_data_drop_NaN_2017_2020.csv")


# df_filtered = df_nhanes[df_nhanes["HeartDiseaseHistory"] == 1]

# default_values = df_filtered[["BMI", "HDL", "Triglycerides", "Glucose", "HbA1c", 
#                      "SerumCreatinine", "ALT", "AST"]].median().to_dict()

# # Convert dictionary to DataFrame
# df_medians = pd.DataFrame([default_values])

# # Define CSV file path
# csv_file_path = "default_values.csv"

# # Save to CSV file
# df_medians.to_csv(csv_file_path, index=False)

# print(f"Default median values saved to {csv_file_path}")

# Define features and target (assume Heart Disease History is the label)
X = df_nhanes.drop(columns=["PatientID", "HeartDiseaseHistory"])
y = df_nhanes["HeartDiseaseHistory"]  # 1 = Yes, 2 = No
# y = y.map({1: 1, 2: 0})  # Convert 1 → 1, 2 → 0


print(df_nhanes["HeartDiseaseHistory"].value_counts())

# Convert categorical variables
X["Smoking"] = X["Smoking"].map({1: 1, 2: 0})
# X["PhysicalActivity"] = X["PhysicalActivity"].fillna(0)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train.fillna(X_train.median(), inplace=True)


# Apply SMOTE to oversample the minority class
smote = SMOTE(sampling_strategy='auto', random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

# feature_weights = {
#     "Age": 2.5, "Hypertension": 3.0, "Smoking": 3.5, "Glucose": 2.0,
#     "HbA1c": 2.5, "HDL": 0.1, "Triglycerides": 2.5, "SerumCreatinine": 1.5,
#     "BMI": 1.5, "ALT": 0.5, "AST": 0.5,
# }



# sample_weights = X_train_resampled.copy()

# for col, weight in feature_weights.items():
#     if col in sample_weights:
#         sample_weights[col] *= weight  # Apply feature importance weights

# # **Sum across columns to get row-wise weights**
# sample_weights = sample_weights.sum(axis=1)  

# # **Ensure all weights are positive**
# sample_weights = np.clip(sample_weights, 1.0, None)  # Clip min weight to 1.0 to avoid XGBoost errors

# # **Convert datasets to XGBoost DMatrix**
# dtrain = xgb.DMatrix(X_train_resampled, label=y_train_resampled, weight=sample_weights)
# dvalid = xgb.DMatrix(X_test, label=y_test)

# **Handle Class Imbalance (Scale Positive Class Weight)**
# scale_pos_weight = sum(y_train_resampled == 0) / sum(y_train_resampled == 1)  # Adjusts imbalance


# scale_pos_weight = 2803 / 248 

dtrain = xgb.DMatrix(X_train_resampled, label=y_train_resampled)
dvalid = xgb.DMatrix(X_test, label=y_test)

# Define parameters
params = {
    "objective": "binary:logistic",  # Binary classification
    "learning_rate": 0.05,
    "max_depth": 10,
    "eval_metric": "logloss",  # Use "auc" for ROC-AUC evaluation
    # "scale_pos_weight": scale_pos_weight,
    # "n_estimators":100,
 }

# Train the model with early stopping
xgb_model = xgb.train(
    params,
    dtrain,
    num_boost_round=400,  # Maximum boosting rounds
    evals=[(dvalid, "validation")],  # Validation set
    early_stopping_rounds=100,  # Stop if no improvement for 20 rounds
    verbose_eval=True  # Print progress
)

#Predict and evaluate
y_pred = (xgb_model.predict(dvalid)> 0.5).astype(int)
accuracy = accuracy_score(y_test, y_pred)
print(f"📊 Final Validation Accuracy: {accuracy:.2f}")

y_pred_log_odds = xgb_model.predict(dvalid, output_margin=True)
print(y_pred_log_odds[:10])  # Shows log-odds instead of probabilities
y_pred_prob = expit(y_pred_log_odds)
print(y_pred_prob[:10])



xgb_model.save_model("xgb_hypertension.json")  # JSON format (readable)

