import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from scipy.special import expit
from imblearn.over_sampling import SMOTE

df_nhanes = pd.read_csv("nhanes_hypertension_data_drop_NaN_2017_2020.csv")


# Define features and target (assume Heart Disease History is the label)
X = df_nhanes.drop(columns=["PatientID", "HeartDiseaseHistory"])
y = df_nhanes["HeartDiseaseHistory"]  # 1 = Yes, 2 = No
# y = y.map({1: 1, 2: 0})  # Convert 1 → 1, 2 → 0


print(df_nhanes["HeartDiseaseHistory"].value_counts())

# Convert categorical variables
X["Smoking"] = X["Smoking"].map({1: 1, 2: 0})
X["PhysicalActivity"] = X["PhysicalActivity"].fillna(0)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# X_train.fillna(X_train.median(), inplace=True)


# # Apply SMOTE to oversample the minority class
# smote = SMOTE(sampling_strategy='auto', random_state=42)
# X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

# # Check new class distribution
# print(X_train_resampled.value_counts()) 
# print(y_train_resampled.value_counts()) 

# Convert datasets to XGBoost DMatrix (optional but improves performance)
dtrain = xgb.DMatrix(X_train, label=y_train)
dvalid = xgb.DMatrix(X_test, label=y_test)

scale_pos_weight = 1265 / 104 

# Define parameters
params = {
    "objective": "binary:logistic",  # Binary classification
    "learning_rate": 0.05,
    "max_depth": 4,
    "eval_metric": "logloss",  # Use "auc" for ROC-AUC evaluation
    "scale_pos_weight": scale_pos_weight,
    "n_estimators":100,
}

# Train the model with early stopping
xgb_model = xgb.train(
    params,
    dtrain,
    num_boost_round=500,  # Maximum boosting rounds
    evals=[(dvalid, "validation")],  # Validation set
    early_stopping_rounds=40,  # Stop if no improvement for 20 rounds
    verbose_eval=True  # Print progress
)

# Predict and evaluate
# y_pred = (xgb_model.predict(dvalid)> 0.5).astype(int)
# accuracy = accuracy_score(y_test, y_pred)
# print(f"📊 Final Validation Accuracy: {accuracy:.2f}")

y_pred_log_odds = xgb_model.predict(dvalid, output_margin=True)
print(y_pred_log_odds[:10])  # Shows log-odds instead of probabilities
y_pred_prob = expit(y_pred_log_odds)
print(y_pred_prob[:10])



xgb_model.save_model("xgb_hypertension.json")  # JSON format (readable)

