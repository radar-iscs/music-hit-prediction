import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import json

st.title("Music Hit Prediction")
st.set_page_config(page_title="Music Hit Prediction")

def load_model():
    model = joblib.load('../Model/best_model.pkl')
    with open('../Model/feature_columns.json', 'r') as f:
        feature_columns = json.load(f)
    with open('../Model/model_info.json', 'r') as f:
        model_info = json.load(f)
    feature_importance = pd.read_csv('../Model/feature_importance.csv')
    return model, feature_columns, model_info, feature_importance

def style_result(val):
    if val == 'Hit':
        return 'color: green'
    elif val == 'Not Hit':
        return 'color: red'
    return ''


st.header("Load Model")
try:
    model, feature_columns, model_info, feature_importance = load_model()
    st.write(f"Model loaded: {model_info['model_name']}")
    st.write(f"Accuracy: {model_info['test_accuracy']:.2%} | F1 Score: {model_info['test_f1_score']:.2%}")
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()


st.header("Upload CSV File")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    X = pd.DataFrame()
    for col in feature_columns:
        if col in df.columns:
            X[col] = df[col]
        else:
            X[col] = 0
    
    X = X.fillna(0)
    
    
    st.header("Predictions")
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    
    df['result'] = predictions
    df['probability'] = probabilities
    
    print(probabilities)
    
    # If popularity column exists, show accuracy
    if 'is_hit' in df.columns:
        false_positive = 0
        false_negative = 0
        for i, row in df.iterrows():
            if row['result'] == 0 and row['is_hit'] != 0:
                false_negative += 1
            if row['result'] == 1 and row['is_hit'] != 1:
                false_positive += 1
                
        correct = len(df) - (false_positive + false_negative)
        
        st.write(f"Predicted hit but not hit: {false_positive}")
        st.write(f"Predicted not hit but hit: {false_negative}")
        st.write(f"**Accuracy:** {correct}/{len(df)} ({correct/len(df)*100:.1f}%)")
    
    display_cols = ['track_name', 'artists', 'is_hit', 'result', 'probability']
    display_cols = [c for c in display_cols if c in df.columns]
    
    display_df = df[display_cols].copy()
    display_df['result'] = display_df['result'].map({0: 'Not Hit', 1: 'Hit'})
    display_df['is_hit'] = display_df['is_hit'].map({0: 'Not Hit', 1: 'Hit'})
    styled_df = display_df.style.applymap(style_result, subset=['result'])
    if 'is_hit' in display_cols:
        styled_df = styled_df.applymap(style_result, subset=['is_hit'])
    st.dataframe(styled_df)


st.header("Feature Importance")

fig, ax = plt.subplots(figsize=(10, 6))
top_features = feature_importance.head(10)
ax.barh(top_features['Feature'], top_features['Importance'])
ax.set_xlabel('Importance')
ax.set_title('Top 10 Important Features')
plt.tight_layout()
st.pyplot(fig)
