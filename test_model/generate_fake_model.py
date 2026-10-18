import joblib
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
y = np.array([3, 7, 11, 15, 19])

model = LinearRegression()
model.fit(X, y)
output = Path(__file__).resolve().parents[1] / "ml_models" / "fake_model.pkl"
output.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, output)
print(f"Created {output}")
print("Features: feature1, feature2")
print("Try: predict [2, 3] -> should be ~5")
