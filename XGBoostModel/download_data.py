import pandas as pd

# Define URLs for NHANES datasets (2017-2020 cycle)
base_url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/"
#base_url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/"
#https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.xpt

# Files to download
files = {
    "demographics": "DEMO_J.XPT",
    "blood_pressure": "BPX_J.XPT",
    "glucose": "GLU_J.XPT",
    "lipids": "TRIGLY_J.XPT",
    "cholesterol": "HDL_J.XPT",
    "smoking": "SMQ_J.XPT",
    "alcohol": "ALQ_J.XPT",
    "body_measures": "BMX_J.XPT",
    
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
df_nhanes["SBP1"] = nhanes_data["blood_pressure"]["BPXSY1"]
df_nhanes["DBP1"] = nhanes_data["blood_pressure"]["BPXDI1"]
df_nhanes["SBP2"] = nhanes_data["blood_pressure"]["BPXSY2"]
df_nhanes["DBP2"] = nhanes_data["blood_pressure"]["BPXDI2"]
df_nhanes["SBP3"] = nhanes_data["blood_pressure"]["BPXSY3"]
df_nhanes["DBP3"] = nhanes_data["blood_pressure"]["BPXDI3"]
df_nhanes["Glucose"] = nhanes_data["glucose"]["LBXGLU"]
df_nhanes["HDL"] = nhanes_data["cholesterol"]["LBDHDD"]
df_nhanes["LDL"] = nhanes_data["lipids"]["LBDLDL"]
df_nhanes["Triglycerides"] = nhanes_data["lipids"]["LBXTR"]
df_nhanes["Smoking"] = nhanes_data["smoking"]["SMQ020"]  # 1=Smoker, 2=Non-smoker
df_nhanes["Alcohol"] = nhanes_data["alcohol"]["ALQ130"]  # Drinks per week

df_nhanes["ExamMonth"] = nhanes_data["demographics"]["RIDEXMON"]
df_nhanes["ExamYear"] = nhanes_data["demographics"]["RIDEXPRG"]

# Convert to full date (mid-month assumption)
df_nhanes["ExamMonth"] = df_nhanes["ExamMonth"].astype(str).str.zfill(2)

# Convert to full date format with explicit formatting
df_nhanes["ExamDate"] = pd.to_datetime(
    df_nhanes["ExamYear"].astype(str) + "-" + df_nhanes["ExamMonth"] + "-15",
    format="%Y-%m-%d", errors="coerce"
)

# Drop NaN values
#df_nhanes.dropna(inplace=True)

# Save as CSV
df_nhanes.to_csv("nhanes_hypertension_data_with_dates.csv", index=False)

print("✅ NHANES Data with Examination Dates Downloaded & Processed!")
