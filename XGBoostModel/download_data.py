import pandas as pd
import numpy as np

# Define URLs for NHANES datasets (2017-2020 cycle)
base_url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/"
#base_url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/"
#https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.xpt

# Files to download
# files = {
#     "demographics": "DEMO_J.XPT",
#     "blood_pressure": "BPX_J.XPT",
#     "glucose": "GLU_J.XPT",
#     "lipids": "TRIGLY_J.XPT",
#     "cholesterol": "HDL_J.XPT",
#     "smoking": "SMQ_J.XPT",
#     "alcohol": "ALQ_J.XPT",
#     "body_measures": "BMX_J.XPT",
#     "diabetes": "GHB_J.XPT",  # HbA1c
#     "kidney_function": "BIOPRO_J.XPT",  # Serum Creatinine
#     "liver_function": "BIOPRO_J.XPT",  # ALT, AST
#     # "inflammation": "CRP_J.XPT",  # CRP
#     "physical_activity": "PAQ_J.XPT",  # Exercise
#     "medications": "RXQ_RX_J.XPT",  # Medication use
#     "medical_conditions": "MCQ_J.XPT",
#     "bio_lab": "HSCRP_J.XPT",
    
# }



files = {
    "demographics": "P_DEMO.xpt",
    "blood_pressure": "P_BPXO.xpt",
    "glucose": "P_GLU.xpt",
    "lipids": "P_TRIGLY.xpt",
    "cholesterol": "P_HDL.xpt",
    "smoking": "P_SMQ.xpt",
    "alcohol": "P_ALQ.xpt",
    "body_measures": "P_BMX.xpt",
    "diabetes": "P_GHB.xpt",  # HbA1c
    "kidney_function": "P_BIOPRO.xpt",  # Serum Creatinine
    "liver_function": "P_BIOPRO.xpt",  # ALT, AST
    # "inflammation": "CRP.xpt",  # CRP
    "physical_activity": "P_PAQ.xpt",  # Exercise
    "medications": "P_RXQ_RX.xpt",  # Medication use
    "medical_conditions": "P_MCQ.xpt",
    "bio_lab": "P_HSCRP.xpt",
    
}

# Load datasets
nhanes_data = {}
for key, filename in files.items():
    url = base_url + filename
    nhanes_data[key] = pd.read_sas(url, format="xport")
    print(f"\n🔹 Columns in {key} dataset:")
    print(nhanes_data[key].columns.tolist())

# Merge relevant columns into a single DataFrame
df_nhanes = pd.DataFrame()

# Extract key columns
df_nhanes["PatientID"] = nhanes_data["demographics"]["SEQN"]
df_nhanes["Age"] = nhanes_data["demographics"]["RIDAGEYR"]
df_nhanes["Gender"] = nhanes_data["demographics"]["RIAGENDR"]
df_nhanes["BMI"] = nhanes_data["body_measures"]["BMXBMI"]
df_nhanes["WaistCircumference"] = nhanes_data["body_measures"]["BMXWAIST"]
df_nhanes["SBP"] = nhanes_data["blood_pressure"]["BPXOSY1"]
df_nhanes["DBP"] = nhanes_data["blood_pressure"]["BPXODI1"]
df_nhanes["Glucose"] = nhanes_data["glucose"]["LBXGLU"]
df_nhanes["HDL"] = nhanes_data["cholesterol"]["LBDHDD"]
df_nhanes["LDL"] = nhanes_data["lipids"]["LBDLDL"]
df_nhanes["Triglycerides"] = nhanes_data["lipids"]["LBXTR"]
df_nhanes["Smoking"] = nhanes_data["smoking"]["SMQ020"]  # 1=Smoker, 2=Non-smoker
df_nhanes["Alcohol"] = nhanes_data["alcohol"]["ALQ130"]  # Drinks per week
# Add new attributes to the dataset
df_nhanes["HbA1c"] = nhanes_data["diabetes"]["LBXGH"]
df_nhanes["SerumCreatinine"] = nhanes_data["kidney_function"]["LBXSCR"]
df_nhanes["ALT"] = nhanes_data["liver_function"]["LBXSATSI"]
df_nhanes["AST"] = nhanes_data["liver_function"]["LBXSASSI"]
df_nhanes["CRP"] = nhanes_data["bio_lab"]["LBXHSCRP"]
df_nhanes["PhysicalActivity"] = nhanes_data["physical_activity"]["PAQ650"]
df_nhanes["HeartDiseaseHistory"] = (
    (nhanes_data["medical_conditions"]["MCQ160B"] == 1) |  # Congestive Heart Failure
    (nhanes_data["medical_conditions"]["MCQ160C"] == 1) |  # Coronary Heart Disease
    (nhanes_data["medical_conditions"]["MCQ160D"] == 1) |  # Angina
    (nhanes_data["medical_conditions"]["MCQ160E"] == 1) |  # Heart Attack
    (nhanes_data["medical_conditions"]["MCQ160F"] == 1)    # Stroke
).astype(int)  # Convert to 1/0

# Compute eGFR (Estimated Glomerular Filtration Rate)
df_nhanes["eGFR"] = 186 * (df_nhanes["SerumCreatinine"] ** -1.154) * (df_nhanes["Age"] ** -0.203)

# Apply gender correction: 0.742 multiplier for females (Gender = 2 in NHANES)
df_nhanes["eGFR"] = np.where(df_nhanes["Gender"] == 2, df_nhanes["eGFR"] * 0.742, df_nhanes["eGFR"])



# Drop NaN values
df_nhanes.dropna(inplace=True)

# Save as CSV
df_nhanes.to_csv("nhanes_hypertension_data_drop_NaN_2017_2020.csv", index=False)

print("✅ NHANES Data with Examination Dates Downloaded & Processed!")
